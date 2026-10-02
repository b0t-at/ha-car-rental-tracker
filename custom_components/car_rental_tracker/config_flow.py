"""Config flow for Car Rental Tracker integration."""
from __future__ import annotations

from datetime import date, datetime, timedelta
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector
from homeassistant.util import dt as dt_util

from .baseline import parse_odometer
from .const import (
    CONF_END_DATE,
    CONF_INITIAL_ODOMETER,
    CONF_KM_ALLOWANCE_PER_MONTH,
    CONF_ODOMETER_ENTITY,
    CONF_OVERAGE_COST_PER_KM,
    CONF_START_DATE,
    DEFAULT_KM_ALLOWANCE,
    DEFAULT_OVERAGE_COST,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def _default_end_date(start: date) -> date:
    """Return the default (inclusive) end date: one year after start, minus a day."""
    try:
        next_year = start.replace(year=start.year + 1)
    except ValueError:  # February 29th
        next_year = start.replace(year=start.year + 1, day=28)
    return next_year - timedelta(days=1)


def _get_schema(data: dict[str, Any] | None = None) -> vol.Schema:
    """Get the configuration schema with default values."""
    if data is None:
        data = {}

    start_default = data.get(CONF_START_DATE, dt_util.now().date().isoformat())
    try:
        end_fallback = _default_end_date(date.fromisoformat(start_default)).isoformat()
    except (TypeError, ValueError):
        end_fallback = start_default

    return vol.Schema(
        {
            vol.Required(
                CONF_START_DATE,
                default=start_default,
            ): selector.DateSelector(),
            vol.Required(
                CONF_END_DATE,
                default=data.get(CONF_END_DATE, end_fallback),
            ): selector.DateSelector(),
            vol.Required(
                CONF_KM_ALLOWANCE_PER_MONTH,
                default=data.get(CONF_KM_ALLOWANCE_PER_MONTH, DEFAULT_KM_ALLOWANCE),
            ): vol.All(vol.Coerce(float), vol.Range(min=1)),
            vol.Required(
                CONF_INITIAL_ODOMETER,
                default=data.get(CONF_INITIAL_ODOMETER, 0),
            ): vol.All(vol.Coerce(float), vol.Range(min=0)),
            vol.Required(
                CONF_OVERAGE_COST_PER_KM,
                default=data.get(CONF_OVERAGE_COST_PER_KM, DEFAULT_OVERAGE_COST),
            ): vol.All(vol.Coerce(float), vol.Range(min=0)),
            vol.Required(
                CONF_ODOMETER_ENTITY,
                default=data.get(CONF_ODOMETER_ENTITY, ""),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["sensor", "input_number"])
            ),
        }
    )


def _validate_dates(start_date: str, end_date: str) -> dict[str, str] | None:
    """Validate that end date is after start date."""
    try:
        start = datetime.fromisoformat(start_date).date()
        end = datetime.fromisoformat(end_date).date()

        if end <= start:
            return {"base": "invalid_date_range"}
    except (ValueError, TypeError):
        return {"base": "invalid_date_format"}

    return None


def _validate_input(
    hass: HomeAssistant,
    user_input: dict[str, Any],
    previous_entity: str | None = None,
) -> dict[str, str]:
    """Validate the dates and the odometer entity; return form errors.

    The odometer entity must exist and report a numeric value. An unchanged
    entity (previous_entity) is not checked again, so a temporarily
    unavailable source does not block editing other options.
    """
    errors = _validate_dates(user_input[CONF_START_DATE], user_input[CONF_END_DATE]) or {}

    entity_id = user_input[CONF_ODOMETER_ENTITY]
    if entity_id != previous_entity:
        state = hass.states.get(entity_id)
        if state is None or parse_odometer(state.state) is None:
            errors[CONF_ODOMETER_ENTITY] = "invalid_odometer"

    return errors


def _unique_id(user_input: dict[str, Any]) -> str:
    """Return the unique ID of an entry (odometer entity and start date)."""
    return f"{user_input[CONF_ODOMETER_ENTITY]}_{user_input[CONF_START_DATE]}"


def _title(user_input: dict[str, Any]) -> str:
    """Return the title of an entry."""
    return f"Car Rental ({user_input[CONF_START_DATE]})"


class CarRentalTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Car Rental Tracker."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            errors = _validate_input(self.hass, user_input)
            if not errors:
                await self.async_set_unique_id(_unique_id(user_input))
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=_title(user_input),
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_get_schema(user_input),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> CarRentalTrackerOptionsFlow:
        """Get the options flow for this handler."""
        return CarRentalTrackerOptionsFlow()


class CarRentalTrackerOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Car Rental Tracker.

    The edited values are stored in the entry data, and the unique ID and
    title are kept in sync with the odometer entity and start date.
    """

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            errors = _validate_input(
                self.hass,
                user_input,
                self.config_entry.data.get(CONF_ODOMETER_ENTITY),
            )
            unique_id = _unique_id(user_input)
            if not errors and self._unique_id_taken(unique_id):
                errors["base"] = "already_configured"
            if not errors:
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data=user_input,
                    title=_title(user_input),
                    unique_id=unique_id,
                )
                return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="init",
            data_schema=_get_schema({**self.config_entry.data, **(user_input or {})}),
            errors=errors,
        )

    def _unique_id_taken(self, unique_id: str) -> bool:
        """Return True if another entry of this domain uses the unique ID."""
        return any(
            entry.unique_id == unique_id
            and entry.entry_id != self.config_entry.entry_id
            for entry in self.hass.config_entries.async_entries(DOMAIN)
        )
