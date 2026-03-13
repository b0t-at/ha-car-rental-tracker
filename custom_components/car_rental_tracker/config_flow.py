"""Config flow for Car Rental Tracker integration."""
from __future__ import annotations

from datetime import date, datetime
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv

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


def _get_schema(data: dict[str, Any] | None = None) -> vol.Schema:
    """Get the configuration schema with default values."""
    if data is None:
        data = {}
    
    return vol.Schema(
        {
            vol.Required(
                CONF_START_DATE,
                default=data.get(CONF_START_DATE, date.today().isoformat()),
            ): selector.DateSelector(),
            vol.Required(
                CONF_END_DATE,
                default=data.get(CONF_END_DATE, date.today().isoformat()),
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
                selector.EntitySelectorConfig(domain=["sensor"])
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


class CarRentalTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Car Rental Tracker."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate dates
            date_errors = _validate_dates(
                user_input[CONF_START_DATE], user_input[CONF_END_DATE]
            )
            if date_errors:
                errors.update(date_errors)
            else:
                # Create a unique ID based on the configuration
                await self.async_set_unique_id(
                    f"{user_input[CONF_ODOMETER_ENTITY]}_{user_input[CONF_START_DATE]}"
                )
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Car Rental ({user_input[CONF_START_DATE]})",
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
    """Handle options flow for Car Rental Tracker."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate dates
            date_errors = _validate_dates(
                user_input[CONF_START_DATE], user_input[CONF_END_DATE]
            )
            if date_errors:
                errors.update(date_errors)
            else:
                # Update the config entry with new data
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data=user_input,
                )
                return self.async_create_entry(title="", data={})

        # Use current config as defaults
        current_config = {**self.config_entry.data}

        return self.async_show_form(
            step_id="init",
            data_schema=_get_schema(current_config),
            errors=errors,
        )
