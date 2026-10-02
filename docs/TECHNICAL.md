# Car Rental Tracker - Technical Documentation

## Architecture overview

Car Rental Tracker is a Home Assistant custom integration with two parts:

1. **Backend (Python)**: config flow, update coordinator, calculations and sensor entities
2. **Frontend card (JavaScript)**: a Lovelace card that the integration serves and loads automatically

Minimum Home Assistant version: 2024.12.0.

## Backend

### Files

```
custom_components/car_rental_tracker/
├── __init__.py          # Entry setup/unload, coordinator, serves and auto-loads the card
├── manifest.json        # Integration metadata (version is managed by release-please)
├── const.py             # Constants and configuration keys
├── config_flow.py       # UI config flow and options flow
├── calculations.py      # Contract calculations (no Home Assistant imports)
├── baseline.py          # Month-start baseline selection and storage format (no Home Assistant imports)
├── sensor.py            # Sensor descriptions (SENSOR_DESCRIPTIONS) and the sensor entity
├── strings.json         # UI and entity translation strings
├── translations/
│   └── en.json          # English translations
└── www/
    └── car-rental-card.js   # Lovelace card
```

`calculations.py` and `baseline.py` don't import Home Assistant, so they can be unit tested without it.

### Key parts

#### CarRentalCoordinator (__init__.py)
- A `DataUpdateCoordinator`, one per config entry, stored in `entry.runtime_data`
- Listens for state changes of the odometer entity and recalculates every 5 minutes, so date-based values (days, time progress) stay current
- Remembers the last two valid odometer readings and keeps using the last valid one while the entity is unavailable or not numeric
- Determines the month-start odometer reading from those readings and the recorder history, and persists it (see [Monthly statistics](#monthly-statistics))
- Calls `calculate_rental_stats()` and provides a `CarRentalData` (stats, current odometer, `monthly_baseline`, `monthly_baseline_source`), or `None` until there has been a valid reading

#### RentalStats (calculations.py)
- `NamedTuple` holding all calculated values: KM totals, progress, monthly values, day counts, projections and status

#### Sensor entities (sensor.py)
- Each sensor is a `CarRentalSensorEntityDescription` in `SENSOR_DESCRIPTIONS` with a `value_fn` (and optionally an `attributes_fn`) that reads `CarRentalData`. One entity class, `CarRentalSensor`, serves all of them.
- 15 sensors per config entry, all on one device named `Car Rental Tracker (<start date>)`. The unique id is `<entry_id>_<key>`.
- Push-based: they update when the coordinator notifies them; they don't poll. They are unavailable while the coordinator data is `None`.
- `has_entity_name` is set and each sensor has a `translation_key` equal to its key (`current_odometer`, `total_driven`, `km_allowed`, `km_remaining`, `km_projected`, `time_progress`, `km_progress`, `monthly_driven`, `monthly_remaining`, `monthly_allowance`, `days_remaining`, `days_elapsed`, `projected_overage`, `projected_cost`, `status`). Entity ids therefore look like `sensor.car_rental_tracker_2024_01_01_km_remaining`. Home Assistant creates the entity ids once; changing the start date later renames the device but keeps the existing ids.
- Status is an `enum` sensor with the options `ok`, `warning` and `critical` (translated). Its attributes are `is_over_limit`, `is_projected_over`, `days_elapsed` and `days_total`.
- Distance sensors use the `distance` device class and km. Current Odometer is `total_increasing`, Total Driven is `total`, and the other distance sensors (including KM Allowed) are `measurement`.
- Days Remaining and Days Elapsed use the `duration` device class with the unit `d`.
- Projected Cost is a `monetary` sensor without a state class; its unit is the Home Assistant currency (`hass.config.currency`).
- Monthly Driven has the attributes `monthly_baseline` (the month-start odometer reading from history; empty when the initial odometer or the estimate is used) and `monthly_baseline_source` (where the month-start reading came from).

### Calculations

All calculations are in `calculations.py`. `calculate_rental_stats()` takes an optional keyword argument `today`; the coordinator passes the current date in Home Assistant's time zone, and tests pass fixed dates.

#### Contract period

- The end date is **inclusive**: `days_total = (end - start).days + 1`, and a contract from Jan 1 to Dec 31 is exactly 12 months.
- `calculate_months_between(start, end_exclusive)` counts whole months with `relativedelta`. Leftover days are divided by the length of the month-long period they fall in (anchored on the start date), so the result never decreases when the end date moves later.
- `km_allowed = km_allowance_per_month × calculate_months_between(start, end + 1 day)`
- Before the start date: `days_elapsed = 0`, `time_progress = 0`, `days_remaining = days_total`, status `ok`.

#### Progress and projection

```
time_progress = days_elapsed / days_total × 100      (clamped to 0..100)
km_progress   = total_driven / km_allowed × 100
km_projected  = total_driven + (total_driven / days_elapsed) × days_remaining
projected_overage = max(km_projected - km_allowed, 0)
projected_cost    = projected_overage × overage_cost_per_km
```

`days_elapsed` counts the start day as day 1.

#### Status

```python
if not has_started:
    status = STATUS_OK
elif is_over_limit or km_progress >= 100:
    status = STATUS_CRITICAL
elif is_projected_over or km_progress > time_progress + 10:
    status = STATUS_WARNING
else:
    status = STATUS_OK
```

`STATUS_OK`, `STATUS_WARNING` and `STATUS_CRITICAL` are defined in `calculations.py`.

#### Monthly statistics

Monthly values are per **calendar month**: from the 1st of the month to today. After the contract has ended, they are calculated for the last month of the contract.

The month-start baseline is chosen in this order:

1. The contract started in the current month: the configured initial odometer (`initial_odometer`).
2. A valid reading near midnight on the 1st (Home Assistant time zone): the last valid reading at or before midnight (`history_before_month_start`), or, if there is none, the first valid reading within 24 hours after midnight (`history_after_month_start`, see `MAX_DELAY_AFTER_BOUNDARY`). The candidates are the coordinator's last two readings plus the recorder's state changes from midnight to 24 hours later, including the state at midnight. The selection logic is in `baseline.py` and works on plain objects with `.state` and `.last_updated`.
3. No usable reading (recorder disabled, old data purged, or no update during the first 24 hours of the month): an estimate from the contract's daily average times the days elapsed in the month (`estimated_fallback`).

A history baseline is computed once per month and persisted with `homeassistant.helpers.storage.Store` in `.storage/car_rental_tracker.<entry_id>` (entity id, month, value, source). It is restored on startup if it belongs to the same odometer entity, and the file is removed in `async_remove_entry` when the entry is deleted. An estimate is never persisted; it is retried at most once per `BASELINE_RETRY_INTERVAL` (1 hour), and only while a history reading can still turn up.

`monthly_remaining = max(km_allowance_per_month - monthly_driven, 0)`.

### Configuration flow

#### Setup
1. **Settings** → **Devices & services** → **Add integration** → **Car Rental Tracker**
2. Form fields:
   - Start and end date (date pickers)
   - Monthly KM allowance, initial odometer, overage cost per KM (number inputs)
   - Odometer entity (entity selector; `sensor` or `input_number` domain)
3. The flow checks that the end date is after the start date and that the odometer entity exists and has a numeric state (`invalid_odometer` otherwise). The schema requires a monthly allowance of at least 1 and a non-negative initial odometer and overage cost.
4. The entry creates one device with 15 sensors.

#### Options flow
- **Configure** on the entry changes the same values, with the same checks. An unchanged odometer entity isn't checked again, so a temporarily unavailable source doesn't block editing the other values.
- The entry's unique id (`<odometer entity>_<start date>`) and title follow the edited values; a combination that another entry already uses is rejected (`already_configured`).
- Saving reloads the entry. Existing entity ids are kept.

### Data flow

```
Odometer entity state change ─┐
5-minute timer ───────────────┼─> Coordinator ─> calculate_rental_stats() ─> Sensors ─> Card
Recorder history (month start)┘
```

### Error handling

- **Odometer entity missing, unavailable or not numeric**: logged at debug level (once, until a valid reading returns). The coordinator keeps calculating with the last valid reading; if there has never been a valid reading, the sensors are `unavailable`. The config and options flows reject a missing or non-numeric entity (`invalid_odometer`).
- **Odometer not in km**: a warning is logged once; the values are used unconverted.
- **Recorder history unavailable**: a warning is logged once, and the monthly baseline falls back to the daily-average estimate (`estimated_fallback`).
- **Division by zero**: progress and averages return 0 when the denominator is 0.
- **Odometer below the initial reading**: Total Driven is clamped to 0.

## Frontend

### Loading

`__init__.py` serves `www/` at `/hacsfiles/car_rental_tracker/` (and `/local/community/car_rental_tracker/`) and registers `/hacsfiles/car_rental_tracker/car-rental-card.js` with `homeassistant.components.frontend.add_extra_js_url`, so every dashboard loads the card without a Lovelace resource. A manually added resource still works: the card only calls `customElements.define` if `car-rental-card` isn't defined yet.

### Configuration

```yaml
type: custom:car-rental-card
entity: sensor.car_rental_tracker_2024_01_01_status   # required: any sensor of the tracker device
title: My Rental Car                                   # optional
```

The card has no visual editor. It finds the other sensors of the same device through `hass.entities[entity].device_id` and each entity's `translation_key`. If `translation_key` isn't available, it matches the entity id suffix `_<key>` among the entities of the same device.

### Sections

1. **Main stats**: current odometer, total driven, KM remaining, days left
2. **Progress**: time and KM progress bars with a pace indicator
3. **This month**: calendar-month driven, remaining and allowance with a progress bar
4. **Projections**: projected KM, overage and cost
5. **Alerts**: warning and critical messages

## Testing

Unit tests cover the Home Assistant-free modules:

- `tests/test_calculations.py`: `calculations.py` (months between dates, allowance, day counts, projection and status, monthly statistics), using fixed `today` dates
- `tests/test_baseline.py`: month-start baseline selection in `baseline.py`
- `tests/conftest.py`: puts `custom_components/car_rental_tracker` on `sys.path` so these modules import without Home Assistant

Run them locally:

```bash
pip install -r tests/requirements.txt
python -m pytest tests -v
```

`sensor.py`, `config_flow.py`, `__init__.py` and the card have no automated tests. Check them by hand:

- [ ] Set up the integration through the UI, with a `sensor` and with an `input_number` as the odometer
- [ ] All 15 sensors are created with the expected entity ids
- [ ] Options flow changes are applied after the reload
- [ ] The card loads without a Lovelace resource and shows all sections
- [ ] Two config entries with separate cards show their own values
- [ ] Light and dark theme, mobile layout

## CI

GitHub Actions workflows in `.github/workflows/`:

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `tests.yml` | push to `main`, pull requests | Python 3.14, installs `tests/requirements.txt`, runs `pytest tests -v` |
| `hacs-validate.yml` | push to `main`, pull requests | HACS validation |
| `hassfest-validate.yml` | push to `main`, pull requests | Home Assistant hassfest validation |
| `release.yml` | push to `main` | release-please |

Actions are pinned to commit SHAs. The validation and test workflows only have `contents: read`.

## Releases

Releases are made by [release-please](https://github.com/googleapis/release-please) from [conventional commits](https://www.conventionalcommits.org/):

1. Merge PRs to `main` with conventional-commit titles: `fix:` for bug fixes (patch), `feat:` for features (minor), `feat!:` or a `BREAKING CHANGE:` footer for breaking changes (major). Use `docs:`, `test:`, `ci:` or `chore:` for changes that don't affect users.
2. release-please opens or updates a release PR. It bumps `.release-please-manifest.json` and the `version` in `manifest.json`, and adds the new section to `CHANGELOG.md`.
3. Merging the release PR creates the tag and the GitHub release. HACS offers the new version to users.

Don't edit the version in `manifest.json`, `.release-please-manifest.json` or `CHANGELOG.md` by hand.

### Backward compatibility

- Config entry data and entity unique ids are kept stable, so existing installations keep their entities and history.
- Changes to entity ids, card configuration or the config entry format are breaking changes and need a `feat!:` / `BREAKING CHANGE:` commit.
- Changes to a sensor's unit, device class or state class change its long-term statistics metadata; Home Assistant then reports issues in **Developer tools** → **Statistics**. Mention them in the release notes, as the [README's upgrade notes for 1.3.x](../README.md#upgrading-from-13x) do.

## Extending

### Adding a sensor

1. Add a `SENSOR_<NAME>` key constant to `const.py`. The key is the unique id suffix and the translation key, so don't change it after a release.
2. Add a description to `SENSOR_DESCRIPTIONS` in `sensor.py`, usually with the `_distance`, `_percentage` or `_days` helper, and a `value_fn` that reads `CarRentalData`. If the value isn't calculated yet, extend `RentalStats` first (see [Adding a calculation](#adding-a-calculation)).
3. Add `entity.sensor.<key>.name` to `strings.json` and `translations/en.json`. The English name must slugify to the key (for example `"KM Remaining"` → `km_remaining`): the entity id is built from it, and the card falls back to matching the `_<key>` suffix.
4. Add the key to `SENSOR_KEYS` in `www/car-rental-card.js` so the card can find the sensor.
5. Update the sensor count (currently 15) and the sensor lists in this document and the [README](../README.md).

### Adding a calculation

1. Add the function to `calculations.py` (no Home Assistant imports)
2. Extend `RentalStats` if needed and fill it in `calculate_rental_stats`
3. Add tests to `tests/test_calculations.py`

## Security and privacy

- All calculations run locally; the integration makes no external calls.
- The only database access is reading the odometer entity's history through the Home Assistant recorder API.
- Dependency: `python-dateutil`. The card uses no third-party JavaScript libraries.

## Troubleshooting

| Problem | Likely cause | What to do |
|---------|--------------|------------|
| Sensors unavailable | Odometer entity hasn't reported a numeric state since Home Assistant started | Check the entity in **Developer tools** → **States**; enable debug logging for `custom_components.car_rental_tracker` |
| Wrong values | Wrong dates or initial odometer | Fix them with **Configure** on the entry |
| Monthly Driven is an estimate | No recorder history for the 1st of the month | Check `monthly_baseline_source`; make sure the recorder keeps the odometer entity |
| Card not displayed | Old frontend cache | Restart Home Assistant and reload the browser (Ctrl+F5) |
| Card says entity not found | Entity was renamed | Update `entity` in the card configuration |

## References

- [Integration development](https://developers.home-assistant.io/docs/creating_component_index)
- [Sensor entity](https://developers.home-assistant.io/docs/core/entity/sensor)
- [Config flow](https://developers.home-assistant.io/docs/config_entries_config_flow_handler)
- [Entity naming and translations](https://developers.home-assistant.io/docs/core/entity#entity-naming)
