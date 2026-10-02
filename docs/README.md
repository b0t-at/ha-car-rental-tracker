# Car Rental Tracker documentation

The user guide (installation, configuration, sensors, dashboard card, automations and troubleshooting) is the [main README](../README.md).

| Document | Contents |
|----------|----------|
| [README](../README.md) | Installation, configuration, sensor list, card setup, automations, troubleshooting |
| [EXAMPLE.md](EXAMPLE.md) | Card layouts, dashboard and automation examples |
| [TECHNICAL.md](TECHNICAL.md) | Architecture, calculations, testing, CI and release process |

Quick reference:

- Minimum Home Assistant version: 2024.12.0
- Entity ids: `sensor.car_rental_tracker_<YYYY_MM_DD>_<sensor>`, for example `sensor.car_rental_tracker_2024_01_01_status` for a contract that starts on 2024-01-01
- Entity ids are created once; changing the start date later renames the device but keeps the ids
- Languages: English and German. Dialogs and the card follow the user's profile language, sensor names the system language; other languages fall back to English. With German as the system language when a contract is added, the sensor part of the entity ids is German (see [Languages](../README.md#languages))
- New language: add `translations/<language>.json` (mirroring `en.json`) and the card texts in `www/car-rental-card.js` (see [Adding a language](TECHNICAL.md#adding-a-language))
- Upgrading from 1.3.x: see [Upgrading from 1.3.x](../README.md#upgrading-from-13x) (statistics metadata, inclusive end date, card resource)
- Card: `type: custom:car-rental-card` with `entity` set to any sensor of the contract (usually the Status sensor). The card is loaded automatically; no Lovelace resource is needed.
