# Car Rental Tracker for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)

Track a car rental or lease contract that has a KM allowance. Car Rental Tracker reads your car's odometer from Home Assistant and shows how much of the allowance you have used, how much time has passed, where you are likely to end up at the end of the contract, and what an overage would cost. A dashboard card that shows all of this is included.

**Requires Home Assistant 2024.12.0 or newer.**

## Features

- **Odometer tracking**: uses any `sensor` or `input_number` entity that holds your car's odometer reading in km
- **Contract totals**: total KM driven, total allowance, remaining KM
- **Time vs. KM progress**: compare the share of the contract period that has passed with the share of the allowance you have used
- **Projections**: projected KM at contract end, projected overage and projected overage cost
- **Monthly statistics**: KM driven and remaining in the current calendar month, plus the configured monthly allowance
- **Status**: `ok`, `warning` or `critical`, usable in automations
- **Dashboard card**: progress bars and key figures; loaded automatically, no manual resource needed

## Installation

### HACS (recommended)

1. Open **HACS** in Home Assistant.
2. Open the **⋮** menu in the top right corner and select **Custom repositories**.
3. Enter `https://github.com/b0t-at/ha-car-rental-tracker`, select **Integration** as the type, and click **Add**.
4. Search for **Car Rental Tracker** in HACS and click **Download**.
5. Restart Home Assistant.

### Manual

1. Copy the `custom_components/car_rental_tracker` folder from this repository into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.

### Upgrading from 1.3.x

Existing contracts keep their entities and history, but some values and metadata change:

- **Statistics metadata**: Days Remaining and Days Elapsed now use the unit `d` and the `duration` device class, Projected Cost is a `monetary` sensor without a state class, and KM Allowed has the state class `measurement`. Home Assistant may list issues for these sensors in **Developer tools** → **Statistics**; use the **Fix issue** button there to resolve them.
- **End date is inclusive**: the total allowance now counts the end date as a contract day, so a contract from Jan 1 to Dec 31 is exactly 12 months. If you entered the day after the contract ends as the end date (for example Jan 1 instead of Dec 31), KM Allowed may now be about one day's allowance too high. Change the end date to the last day of the contract with **Configure**.
- **Card resource**: the card is now loaded automatically. If you added `/hacsfiles/car_rental_tracker/car-rental-card.js` as a Lovelace resource, you can remove it; leaving it in place does no harm.
- **New sensor**: Monthly Allowance shows the configured KM allowance per month.

## Configuration

1. Go to **Settings** → **Devices & services** → **Add integration**.
2. Search for **Car Rental Tracker**.
3. Fill in the form:
   - **Start date**: the first day of the contract
   - **End date**: the last day of the contract (inclusive; a contract from Jan 1 to Dec 31 is exactly 12 months)
   - **KM allowance per month**: the monthly KM limit from your contract
   - **Initial odometer**: the odometer reading when you received the car
   - **Overage cost per KM**: what the contract charges per KM over the allowance
   - **Odometer entity**: a `sensor` or an `input_number` that holds the current odometer reading in km. It must exist and have a numeric state when you save the form. If your car has no odometer sensor, create an `input_number` helper and update it by hand or from an automation.

You can change these values later with **Configure** on the integration's entry. The integration reloads with the new values. If you keep the same odometer entity, it isn't checked again, so you can edit the other values while the entity is temporarily unavailable.

Entity ids are created once, when you add the contract. If you change the start date later, the device gets the new name, but the entity ids keep the old date. Rename them on the device page if you want them to match.

### Several rentals

Add the integration once per contract. Each entry creates its own device ("Car Rental Tracker (&lt;start date&gt;)") with its own set of sensors. Give each one its own card (see [Dashboard card](#dashboard-card)).

## Sensors

Each contract creates 15 sensors on one device. Entity ids are built from the device name, which contains the contract start date:

```
sensor.car_rental_tracker_<YYYY_MM_DD>_<sensor>
```

For a contract that starts on 2024-01-01, the KM Remaining sensor is `sensor.car_rental_tracker_2024_01_01_km_remaining`. If two contracts share a start date, Home Assistant adds a suffix such as `_2` to the second one. The ids are fixed when the contract is added (see [Configuration](#configuration)), and you can rename them yourself, so the device page (**Settings** → **Devices & services** → **Car Rental Tracker** → device) is the reliable place to look them up.

| Sensor | Entity id suffix | Description | Unit |
|--------|------------------|-------------|------|
| Current Odometer | `current_odometer` | Current reading of the odometer entity | km |
| Total Driven | `total_driven` | KM driven since contract start | km |
| KM Allowed | `km_allowed` | Total allowance for the whole contract (monthly allowance × contract months) | km |
| KM Remaining | `km_remaining` | Allowance left; negative once you are over | km |
| KM Projected | `km_projected` | Projected total KM at contract end, based on your daily average so far | km |
| Time Progress | `time_progress` | Share of the contract period that has passed | % |
| KM Progress | `km_progress` | Share of the total allowance used | % |
| Monthly Driven | `monthly_driven` | KM driven in the current calendar month | km |
| Monthly Remaining | `monthly_remaining` | KM left of this calendar month's allowance (never below 0) | km |
| Monthly Allowance | `monthly_allowance` | Configured KM allowance per month | km |
| Days Remaining | `days_remaining` | Days until the contract end date | d |
| Days Elapsed | `days_elapsed` | Days since the contract start date | d |
| Projected Overage | `projected_overage` | Projected KM above the allowance at contract end | km |
| Projected Cost | `projected_cost` | Projected overage × overage cost per KM | Home Assistant currency |
| Status | `status` | `ok`, `warning` or `critical` | - |

The Projected Cost sensor uses the currency configured in **Settings** → **System** → **General**.

The Monthly Driven sensor has two attributes about the start of the month (see [Monthly statistics](#monthly-statistics)): `monthly_baseline`, the odometer reading taken from history as the start of the month (empty when the initial odometer or an estimate is used), and `monthly_baseline_source`, which tells you where that reading came from. The Status sensor has the attributes `is_over_limit`, `is_projected_over`, `days_elapsed` and `days_total`.

## Dashboard card

The card is served by the integration and loaded into the frontend automatically. You don't need to add a Lovelace resource. After installing or updating, reload the browser (Ctrl+F5 / Cmd+Shift+R) so it picks up the new file.

### Add the card

1. Edit your dashboard and click **Add card**.
2. Search for **Car Rental Tracker Card**.
3. The card picker pre-fills the Status sensor of one of your contracts. The card has no visual editor, so use the code editor to pick another contract or set a title:

```yaml
type: custom:car-rental-card
entity: sensor.car_rental_tracker_2024_01_01_status
title: My Rental Car
```

| Option | Required | Description |
|--------|----------|-------------|
| `type` | yes | `custom:car-rental-card` |
| `entity` | yes | Any sensor of the contract's device; usually the Status sensor. The card finds the other sensors of the same device by itself. |
| `title` | no | Card heading (default: "Car Rental Tracker") |

### Several rentals

Point each card at a sensor of a different contract:

```yaml
type: vertical-stack
cards:
  - type: custom:car-rental-card
    entity: sensor.car_rental_tracker_2024_01_01_status
    title: Personal car
  - type: custom:car-rental-card
    entity: sensor.car_rental_tracker_2025_03_15_status
    title: Company car
```

### Individual sensors

The sensors also work in the built-in cards:

```yaml
type: entities
entities:
  - entity: sensor.car_rental_tracker_2024_01_01_total_driven
    name: Total driven
  - entity: sensor.car_rental_tracker_2024_01_01_km_remaining
    name: KM left
  - entity: sensor.car_rental_tracker_2024_01_01_days_remaining
    name: Days left
  - entity: sensor.car_rental_tracker_2024_01_01_status
    name: Status
```

## Automations

Replace the entity ids with your own. `notify.mobile_app_your_phone` is a placeholder for your notify action.

### Warning and critical notifications

```yaml
automation:
  - alias: Car rental status changed
    triggers:
      - trigger: state
        entity_id: sensor.car_rental_tracker_2024_01_01_status
        to:
          - warning
          - critical
    actions:
      - action: notify.mobile_app_your_phone
        data:
          title: "Car rental: {{ trigger.to_state.state | upper }}"
          message: >
            {% if trigger.to_state.state == 'critical' %}
            You have exceeded your KM allowance. Additional charges will apply.
            {% else %}
            You are driving faster than your contract allows.
            Projected overage: {{ states('sensor.car_rental_tracker_2024_01_01_projected_overage') }} km.
            {% endif %}
```

### Monthly summary

Monthly Driven counts the current calendar month and starts again at 0 on the 1st. To report a full month, send the summary on the last day of the month, shortly before midnight:

```yaml
automation:
  - alias: Car rental monthly summary
    triggers:
      - trigger: time
        at: "23:55:00"
    conditions:
      - condition: template
        value_template: "{{ (now() + timedelta(days=1)).day == 1 }}"
    actions:
      - action: notify.mobile_app_your_phone
        data:
          title: "Car rental: {{ now().strftime('%B') }} summary"
          message: >
            Driven this month: {{ states('sensor.car_rental_tracker_2024_01_01_monthly_driven') }} km
            of {{ states('sensor.car_rental_tracker_2024_01_01_monthly_allowance') }} km.
            KM left in the contract: {{ states('sensor.car_rental_tracker_2024_01_01_km_remaining') }} km.
```

More examples are in [docs/EXAMPLE.md](docs/EXAMPLE.md).

## How the values are calculated

### Contract period

Both the start date and the end date count as contract days. A contract from 2024-01-01 to 2024-12-31 has 366 days and exactly 12 months, so KM Allowed is 12 × the monthly allowance. Partial months count as a fraction of a month.

Before the start date, Days Elapsed and Time Progress are 0, Days Remaining equals the full contract length, and the status is `ok`.

### Progress and projection

```
Time Progress = Days Elapsed / Contract Days × 100
KM Progress   = Total Driven / KM Allowed × 100
KM Projected  = Total Driven + (Total Driven / Days Elapsed) × Days Remaining
```

### Status

- **critical**: Total Driven has reached or exceeded KM Allowed
- **warning**: KM Projected is above KM Allowed, or KM Progress is more than 10 percentage points ahead of Time Progress
- **ok**: everything else

### Monthly statistics

Monthly values are per **calendar month** (from the 1st of the month to today), limited to the contract period. After the end date, they keep showing the last month of the contract. The starting point of the month is taken from:

1. the initial odometer, in the month the contract starts (`monthly_baseline_source: initial_odometer`), or
2. the odometer value at midnight on the 1st of the month, in Home Assistant's time zone: the last value before midnight, or, if there is none, the first value within 24 hours after midnight (`history_before_month_start` / `history_after_month_start`). The value comes from the Home Assistant recorder or from the readings the integration saw while running, or
3. an estimate from your daily average when there is no such reading, for example because the recorder purged old data or the odometer didn't update during the first day of the month (`estimated_fallback`). The integration looks for a real reading again once an hour while one can still turn up.

Once a real reading has been found for the month, it is saved in `.storage/car_rental_tracker.<entry_id>`, so it survives restarts and recorder purges. The file is removed when you delete the contract.

The `monthly_baseline_source` and `monthly_baseline` attributes of the Monthly Driven sensor show which one was used.

## Troubleshooting

### Sensors show "Unavailable"

- The sensors are unavailable until the odometer entity has reported a valid numeric reading at least once since Home Assistant started. Check that it has a numeric state in **Developer tools** → **States**.
- If the odometer entity later becomes unavailable or non-numeric (for example while the car is out of range), the sensors keep using the last valid reading. This is logged at debug level only.
- The sensors update whenever the odometer entity changes and every 5 minutes.

### Card shows "Custom element doesn't exist: car-rental-card"

- Restart Home Assistant after installing or updating the integration.
- Reload the browser with Ctrl+F5 (Cmd+Shift+R on macOS); on the companion app, clear the frontend cache in the app settings.
- In the browser developer tools (F12), check on the **Network** tab that `car-rental-card.js` loads, and check the **Console** for errors.
- A manually added resource `/hacsfiles/car_rental_tracker/car-rental-card.js` is not needed any more, but it does no harm if you already have one.

### Values look wrong

- Check the start date, end date and initial odometer in the integration's **Configure** dialog.
- The odometer entity must report kilometers. Readings in miles are not converted.

## Documentation

- [Examples](docs/EXAMPLE.md): card layouts, dashboards and automations
- [Technical documentation](docs/TECHNICAL.md): architecture, calculations, testing and release process

## Support

Report bugs and request features in the [issue tracker](https://github.com/b0t-at/ha-car-rental-tracker/issues). Please include your Home Assistant version and relevant log entries.

## Contributing

Pull requests are welcome. Use [conventional commit](https://www.conventionalcommits.org/) titles (`feat: ...`, `fix: ...`); releases are created from them automatically. Run the tests with:

```bash
pip install -r tests/requirements.txt
python -m pytest tests -v
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
