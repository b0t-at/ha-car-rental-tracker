# Contributing to HA Plugins

Thank you for your interest in contributing to this Home Assistant plugins repository!

## How to Add a New Plugin

### 1. Plugin Structure

Each plugin must be placed in its own directory under `custom_components/` with the following minimum structure:

```
custom_components/
└── your_plugin_name/
    ├── __init__.py        # Main integration file (required)
    ├── manifest.json      # Integration metadata (required)
    ├── config_flow.py     # Configuration UI (optional but recommended)
    ├── sensor.py          # Sensor platform (if applicable)
    ├── switch.py          # Switch platform (if applicable)
    └── README.md          # Plugin-specific documentation (recommended)
```

### 2. Required Files

#### `manifest.json`

Every integration must have a manifest file with the following structure:

```json
{
  "domain": "your_plugin_name",
  "name": "Your Plugin Display Name",
  "documentation": "https://github.com/Utesgui/HA-plugins/tree/main/custom_components/your_plugin_name",
  "issue_tracker": "https://github.com/Utesgui/HA-plugins/issues",
  "codeowners": ["@Utesgui"],
  "requirements": [],
  "dependencies": [],
  "version": "1.0.0",
  "iot_class": "local_polling"
}
```

**Key fields:**
- `domain`: Must match your directory name (lowercase, no spaces)
- `name`: User-friendly name displayed in Home Assistant
- `requirements`: Python packages required (e.g., `["requests>=2.25.0"]`)
- `iot_class`: How your integration communicates (see [IoT Classes](https://developers.home-assistant.io/docs/creating_component_index#iot-class))
- `version`: Semantic version number

#### `__init__.py`

Minimum implementation:

```python
"""Your Plugin integration."""
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

DOMAIN = "your_plugin_name"

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration from configuration.yaml."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return True
```

### 3. Development Guidelines

- Follow [Home Assistant's development standards](https://developers.home-assistant.io/docs/development_index)
- Use Python 3.11+ features
- Include type hints in your code
- Write clear, descriptive comments
- Test your integration with multiple Home Assistant versions
- Keep dependencies minimal

### 4. HACS Compatibility

Ensure your plugin is compatible with HACS:
- Use semantic versioning (e.g., 1.0.0)
- Include a `manifest.json` with a `version` field
- Document installation and configuration in a README.md
- Tag releases in Git if using version control

### 5. Testing Locally

Before submitting:

1. Copy your plugin folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant
3. Check logs for any errors: `config/home-assistant.log`
4. Test all functionality through the Home Assistant UI
5. Verify the plugin shows up in **Settings** → **Devices & Services**

### 6. Submitting Your Plugin

1. Fork this repository
2. Create a new branch: `git checkout -b add-your-plugin-name`
3. Add your plugin directory under `custom_components/`
4. Update the main README.md to list your plugin
5. Submit a Pull Request with:
   - Clear description of what your plugin does
   - Installation instructions
   - Any special configuration needed

### 7. Code Review

All submissions will be reviewed for:
- Code quality and standards
- Security considerations
- HACS compatibility
- Proper documentation
- Testing evidence

## Questions?

If you have questions or need help, please:
- Open an [Issue](https://github.com/Utesgui/HA-plugins/issues)
- Refer to [Home Assistant's development documentation](https://developers.home-assistant.io/)

## Resources

- [Home Assistant Developer Docs](https://developers.home-assistant.io/)
- [HACS Documentation](https://hacs.xyz/)
- [Integration Quality Scale](https://developers.home-assistant.io/docs/integration_quality_scale_index)
- [Home Assistant Architecture](https://developers.home-assistant.io/docs/architecture_index)

Thank you for contributing! 🎉
