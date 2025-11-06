"""Car Rental Tracker integration for Home Assistant.

This integration tracks car rental contracts with KM limits and provides
detailed statistics, projections, and visual dashboard capabilities.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, RESOURCE_REGISTERED_FLAG

_LOGGER = logging.getLogger(__name__)

# List of platforms supported by this integration
PLATFORMS: list[Platform] = [Platform.SENSOR]

# Configuration schema (for configuration.yaml support)
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Car Rental Tracker component from configuration.yaml.
    
    This integration requires config flow setup, but we still need this
    function for Home Assistant to load the integration.
    """
    _LOGGER.debug("Car Rental Tracker integration: async_setup called")
    return True


async def _register_lovelace_resource(hass: HomeAssistant) -> None:
    """Register the Lovelace card resource."""
    # Only register once
    if RESOURCE_REGISTERED_FLAG in hass.data.get(DOMAIN, {}):
        return
    
    # Register the frontend paths for the www directory
    www_path = hass.config.path(f"custom_components/{DOMAIN}/www")
    await hass.http.async_register_static_paths([
        StaticPathConfig(f"/hacsfiles/{DOMAIN}", www_path, False),
        StaticPathConfig(f"/local/community/{DOMAIN}", www_path, False),
    ])
    _LOGGER.info(f"Registered frontend paths: /hacsfiles/{DOMAIN} and /local/community/{DOMAIN}")
    
    # Mark as registered
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][RESOURCE_REGISTERED_FLAG] = True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Car Rental Tracker from a config entry.
    
    This is called when the integration is set up through the UI.
    """
    _LOGGER.info("Setting up Car Rental Tracker integration")
    
    # Store integration data in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data
    
    # Register Lovelace resource
    await _register_lovelace_resource(hass)
    
    # Forward the setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Register update listener for config changes
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    
    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update.
    
    Called when the user updates the configuration through the UI.
    """
    _LOGGER.debug("Updating Car Rental Tracker configuration")
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.
    
    This is called when the integration is being removed.
    """
    _LOGGER.info("Unloading Car Rental Tracker integration")
    
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    # Remove stored data
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok
