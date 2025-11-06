# Home Assistant Custom Plugins

This repository hosts custom integrations and plugins for Home Assistant. All integrations are designed to be installed via [HACS (Home Assistant Community Store)](https://hacs.xyz/).

## Prerequisites

- **Home Assistant** installed and running
- **HACS** (Home Assistant Community Store) installed
  - If you haven't installed HACS yet, follow the [official installation guide](https://hacs.xyz/docs/setup/download)

## Available Plugins

This repository contains custom integrations for Home Assistant. Each plugin is located in its own directory under `custom_components/`.

### 🚗 Car Rental Tracker

**Track your car rental contract with KM limits and avoid overage charges!**

A comprehensive integration for managing long-term car rentals with KM allowances. Features include:
- Real-time odometer tracking
- Monthly KM usage statistics
- Projected overage calculations
- Smart alerts for usage warnings
- Beautiful dashboard card with progress bars and charts
- Cost projections

[📖 Documentation](custom_components/car_rental_tracker/README.md) | [⬇️ Installation Guide](custom_components/car_rental_tracker/README.md#installation)

## Installation

### Method 1: Install via HACS (Recommended)

1. Open Home Assistant and go to **HACS**
2. Click on **Integrations**
3. Click the **three dots** in the top right corner
4. Select **Custom repositories**
5. Add this repository URL: `https://github.com/Utesgui/HA-plugins`
6. Select **Integration** as the category
7. Click **Add**
8. Find the desired plugin in HACS and click **Download**
9. Restart Home Assistant
10. Go to **Settings** → **Devices & Services** → **Add Integration**
11. Search for and add the plugin

### Method 2: Manual Installation

1. Download the desired plugin folder from the `custom_components/` directory
2. Copy the plugin folder to your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant
4. Go to **Settings** → **Devices & Services** → **Add Integration**
5. Search for and add the plugin

## Repository Structure

```
HA-plugins/
├── custom_components/          # All custom integrations
│   ├── plugin_name_1/         # Individual plugin directory
│   │   ├── __init__.py
│   │   ├── manifest.json
│   │   └── ...
│   └── plugin_name_2/
│       ├── __init__.py
│       ├── manifest.json
│       └── ...
├── LICENSE
└── README.md
```

## For Plugin Developers

### Adding a New Plugin

Each custom integration should:

1. Be placed in its own directory under `custom_components/`
2. Include a `manifest.json` file with proper metadata
3. Follow Home Assistant's [integration development guidelines](https://developers.home-assistant.io/docs/creating_component_index)
4. Be compatible with HACS requirements

### Minimum Required Files

Each plugin directory must contain:

- `__init__.py` - Main integration file
- `manifest.json` - Integration metadata

Example `manifest.json`:
```json
{
  "domain": "your_plugin_name",
  "name": "Your Plugin Name",
  "documentation": "https://github.com/Utesgui/HA-plugins",
  "issue_tracker": "https://github.com/Utesgui/HA-plugins/issues",
  "codeowners": ["@Utesgui"],
  "requirements": [],
  "version": "1.0.0",
  "iot_class": "local_polling"
}
```

## Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/Utesgui/HA-plugins/issues) page
2. Create a new issue with detailed information about your problem

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
