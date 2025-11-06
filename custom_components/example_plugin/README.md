# Example Plugin

This is a template/example plugin that demonstrates the basic structure needed for a Home Assistant custom component.

## ⚠️ Note

This is an **example template** for developers. It does not provide any actual functionality and should not be installed for use in production Home Assistant instances.

## Purpose

This example serves as:
- A reference for the minimum file structure required
- A starting point for developing new plugins
- Documentation of best practices

## Files Included

- `__init__.py` - Main integration setup with entry points
- `manifest.json` - Integration metadata and requirements
- `README.md` - This documentation file

## For Developers

If you're creating a new plugin:

1. Copy this directory structure
2. Rename `example_plugin` to your plugin's name
3. Update `manifest.json` with your plugin details
4. Implement your plugin logic in `__init__.py`
5. Add additional platform files as needed (e.g., `sensor.py`, `switch.py`)
6. Test thoroughly before submitting

## Resources

- [Home Assistant Developer Docs](https://developers.home-assistant.io/)
- [Integration Development](https://developers.home-assistant.io/docs/creating_component_index)
- [CONTRIBUTING.md](../../../CONTRIBUTING.md) in the root of this repository
