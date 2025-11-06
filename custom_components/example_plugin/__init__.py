"""Example Plugin integration for Home Assistant.

This is a template/example integration that demonstrates the basic structure
needed for a Home Assistant custom component.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# Define the domain for this integration
DOMAIN = "example_plugin"

# List of platforms supported by this integration
PLATFORMS: list[Platform] = []  # Add platforms like Platform.SENSOR, Platform.SWITCH, etc.


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the Example Plugin component from configuration.yaml.
    
    This is called when Home Assistant starts up and loads this integration.
    """
    _LOGGER.info("Example Plugin integration loaded from configuration.yaml")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Example Plugin from a config entry.
    
    This is called when the integration is set up through the UI.
    """
    _LOGGER.info("Setting up Example Plugin integration")
    
    # Store integration data in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}
    
    # Forward the setup to platforms (if any)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.
    
    This is called when the integration is being removed.
    """
    _LOGGER.info("Unloading Example Plugin integration")
    
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    # Remove stored data
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok
