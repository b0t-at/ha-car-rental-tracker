# Car Rental Tracker - Examples

All examples use a contract that starts on 2024-01-01, so the entity ids start with `sensor.car_rental_tracker_2024_01_01_`. Replace that part with the ids of your own contract; you can look them up on the device page under **Settings** → **Devices & services** → **Car Rental Tracker**. The suffixes shown here are the English ones; if Home Assistant's system language was German when you added the contract, your ids end in the German sensor names instead (see [Entity ids and the system language](../README.md#entity-ids-and-the-system-language)). `notify.mobile_app_your_phone` is a placeholder for your own notify action.

The automation examples use the `triggers:` / `actions:` syntax, which the minimum supported Home Assistant version (2024.12) understands.

## Dashboard card

The card gives an at-a-glance view of the contract. The sketches below show its layout; the real card follows your Home Assistant theme.

### Card layout

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  🚗 Car Rental Tracker                         [OK]        ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                                             ┃
┃  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┃
┃  │    🔢    │  │    🗺️    │  │    ⏲️    │  │    📅    │  ┃
┃  │ 12,500 km│  │ 2,500 km │  │ 1,200 km │  │    45    │  ┃
┃  │  Current │  │  Total   │  │    KM    │  │   Days   │  ┃
┃  │ Odometer │  │  Driven  │  │ Remaining│  │   Left   │  ┃
┃  └──────────┘  └──────────┘  └──────────┘  └──────────┘  ┃
┃                                                             ┃
┃  Progress Overview                                          ┃
┃  ─────────────────                                          ┃
┃                                                             ┃
┃  🕐 Time Elapsed                                    45.2%   ┃
┃  ██████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░        ┃
┃                                                             ┃
┃  🚗 KM Usage                                        37.5%   ┃
┃  ███████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░         ┃
┃                                                             ┃
┃  ✓ 7.7% Behind - You Can Drive More                        ┃
┃                                                             ┃
┃  This Month                                                 ┃
┃  ──────────                                                 ┃
┃                                                             ┃
┃  Driven: 450 km    Remaining: 550 km    Allowance: 1000 km ┃
┃  █████████████████████░░░░░░░░░░░░░░░░░░░                 ┃
┃                   45.0% of monthly allowance used           ┃
┃                                                             ┃
┃  Projections                                                ┃
┃  ───────────                                                ┃
┃                                                             ┃
┃  📊 Projected KM at End            11,234 km                ┃
┃                                                             ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

"This Month" covers the current calendar month (from the 1st to today).

### Status badge

- **OK (green)**: usage is within the expected range
- **WARNING (orange)**: projected to exceed the allowance, or KM progress is more than 10 percentage points ahead of time progress
- **CRITICAL (red)**: the KM allowance has been reached or exceeded

### Warning example

When you are ahead of pace:

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  🚗 Car Rental Tracker                    [WARNING]        ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                                             ┃
┃  ... (stats section) ...                                    ┃
┃                                                             ┃
┃  🕐 Time Elapsed                                    45.2%   ┃
┃  ██████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░        ┃
┃                                                             ┃
┃  🚗 KM Usage                                        62.8%   ┃
┃  ███████████████████████████████░░░░░░░░░░░░░░░░░         ┃
┃                                                             ┃
┃  ⚠️ 17.6% Ahead - Slow Down!                               ┃
┃                                                             ┃
┃  ... (monthly section) ...                                  ┃
┃                                                             ┃
┃  Projections                                                ┃
┃  ───────────                                                ┃
┃                                                             ┃
┃  📊 Projected KM at End            14,856 km                ┃
┃  ⚠️ Projected Overage              2,856 km                 ┃
┃  💰 Estimated Cost                 714.00 €                 ┃
┃                                                             ┃
┃  ┌──────────────────────────────────────────────────────┐  ┃
┃  │ ⚠️ WARNING: You are projected to exceed your        │  ┃
┃  │    allowance by 2,856 km                             │  ┃
┃  └──────────────────────────────────────────────────────┘  ┃
┃  ┌──────────────────────────────────────────────────────┐  ┃
┃  │ 🚗 You are driving faster than your contract pace.  │  ┃
┃  │    Consider slowing down.                            │  ┃
┃  └──────────────────────────────────────────────────────┘  ┃
┃                                                             ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

The cost is shown in the currency configured in Home Assistant (**Settings** → **System** → **General**).

### Critical example

When you have used up your allowance:

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  🚗 Car Rental Tracker                   [CRITICAL]        ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                                             ┃
┃  ... (stats section) ...                                    ┃
┃                                                             ┃
┃  🕐 Time Elapsed                                    85.4%   ┃
┃  ██████████████████████████████████████████░░░░░░         ┃
┃                                                             ┃
┃  🚗 KM Usage                                       107.2%   ┃
┃  ███████████████████████████████████████████████████       ┃
┃                                                             ┃
┃  ┌──────────────────────────────────────────────────────┐  ┃
┃  │ 🚨 CRITICAL: You have exceeded your KM allowance!   │  ┃
┃  └──────────────────────────────────────────────────────┘  ┃
┃                                                             ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

## Card configuration examples

The card is loaded automatically by the integration; you don't need to add a Lovelace resource. Search for **Car Rental Tracker Card** in the card picker; it pre-fills the Status sensor of one of your contracts. The card has no visual editor, so change `entity` or `title` in the card's code editor.

### Basic

```yaml
type: custom:car-rental-card
entity: sensor.car_rental_tracker_2024_01_01_status
title: My Rental Car
```

`entity` can be any sensor of the contract's device; the card finds the other sensors of that device by itself. `title` is optional.

### In a dashboard view

```yaml
title: Car Management
path: car
icon: mdi:car
cards:
  - type: custom:car-rental-card
    entity: sensor.car_rental_tracker_2024_01_01_status
    title: Monthly Rental

  - type: entities
    title: Quick Stats
    entities:
      - sensor.car_rental_tracker_2024_01_01_days_remaining
      - sensor.car_rental_tracker_2024_01_01_km_remaining
      - sensor.car_rental_tracker_2024_01_01_monthly_remaining
      - sensor.car_rental_tracker_2024_01_01_projected_cost
```

### Several rental cars

Add the integration once per contract. Each contract gets its own device and sensors, named after its start date (here 2024-01-01 and 2025-03-15). If two contracts share a start date, the second one gets a `_2` suffix, for example `sensor.car_rental_tracker_2024_01_01_status_2`; check the device page for the exact ids.

```yaml
type: vertical-stack
cards:
  - type: custom:car-rental-card
    entity: sensor.car_rental_tracker_2024_01_01_status
    title: Personal Rental

  - type: custom:car-rental-card
    entity: sensor.car_rental_tracker_2025_03_15_status
    title: Business Rental
```

## Automation examples

### Daily summary notification

```yaml
automation:
  - alias: Daily rental summary
    triggers:
      - trigger: time
        at: "20:00:00"
    actions:
      - action: notify.mobile_app_your_phone
        data:
          title: "Car rental daily summary"
          message: >
            Driven: {{ states('sensor.car_rental_tracker_2024_01_01_total_driven') }} km
            Remaining: {{ states('sensor.car_rental_tracker_2024_01_01_km_remaining') }} km
            Days left: {{ states('sensor.car_rental_tracker_2024_01_01_days_remaining') }}
            Status: {{ states('sensor.car_rental_tracker_2024_01_01_status') | upper }}
```

### Overage warning

```yaml
automation:
  - alias: Rental overage warning
    triggers:
      - trigger: state
        entity_id: sensor.car_rental_tracker_2024_01_01_status
        to: "warning"
    actions:
      - action: persistent_notification.create
        data:
          title: "Car rental warning"
          message: >
            You are driving faster than your contract pace.
            Projected overage: {{ states('sensor.car_rental_tracker_2024_01_01_projected_overage') }} km
            Estimated cost: {{ states('sensor.car_rental_tracker_2024_01_01_projected_cost') }}
            {{ state_attr('sensor.car_rental_tracker_2024_01_01_projected_cost', 'unit_of_measurement') }}
```

### Monthly report

Monthly Driven and Monthly Remaining cover the current calendar month and start again on the 1st. A report sent on the 1st would only see the first minutes of the new month, so this one runs at 23:55 on the last day of the month:

```yaml
automation:
  - alias: Monthly rental report
    triggers:
      - trigger: time
        at: "23:55:00"
    conditions:
      - condition: template
        value_template: "{{ (now() + timedelta(days=1)).day == 1 }}"
    actions:
      - action: notify.mobile_app_your_phone
        data:
          title: "Car rental report for {{ now().strftime('%B %Y') }}"
          message: >
            {% set driven = states('sensor.car_rental_tracker_2024_01_01_monthly_driven') | float(0) %}
            {% set allowance = states('sensor.car_rental_tracker_2024_01_01_monthly_allowance') | float(0) %}
            Driven: {{ driven | round(0) }} km
            Allowance: {{ allowance | round(0) }} km
            {% if allowance > 0 %}Used: {{ (driven / allowance * 100) | round(1) }}% of the monthly allowance{% endif %}

            Status: {{ states('sensor.car_rental_tracker_2024_01_01_status') | upper }}
            Days remaining: {{ states('sensor.car_rental_tracker_2024_01_01_days_remaining') }}
```

## Feature overview

### Statistics
- Live odometer reading
- Total KM driven
- KM remaining in the contract
- Days elapsed and days until contract end
- Calendar-month figures (driven, remaining, allowance)

### Projections
- Projected total KM at contract end
- Projected overage (if any)
- Projected overage cost

### Updates
- Recalculated whenever the odometer entity changes
- Recalculated every 5 minutes so time-based values stay current

### Alerts
- Status sensor (`ok` / `warning` / `critical`) for automations
- Warning when you are ahead of pace
- Critical when the allowance is used up

### Configuration
- UI-based setup, no YAML needed for the integration
- Odometer can be a `sensor` or an `input_number` helper
- Date pickers for the contract period
- Change values later with **Configure** on the integration entry

## Use cases

1. **Long-term rentals**: monthly or yearly rental contracts
2. **Leases**: lease agreements with KM limits
3. **Several vehicles**: one integration entry per contract
4. **Cost control**: avoid unexpected overage charges
5. **Trip planning**: know how many KM you have left for a trip

## Tips

1. **Initial reading**: enter the exact odometer reading from when you received the car.
2. **Regular updates**: the more often the odometer entity updates, the more accurate the monthly figures. If you use an `input_number`, update it at least once a month, on the 1st: a reading from the first 24 hours of the month is used as the start of the month; otherwise the monthly figures are estimated.
3. **Contract dates**: the end date is the last day of the contract and is counted as a contract day.
4. **Monthly allowance**: check it against your contract.
5. **Overage cost**: enter the per-KM overage price from your contract.

## Troubleshooting

### Card not showing
- Restart Home Assistant after installing or updating the integration.
- Reload the browser with Ctrl+F5 (Cmd+Shift+R on macOS).
- In the browser developer tools (F12), check that `car-rental-card.js` loads on the **Network** tab.

### Wrong calculations
- Check the contract dates and initial odometer in the integration's **Configure** dialog.
- The odometer entity must report kilometers; miles are not converted.
- Check the monthly allowance.

### Sensor not updating
- Look at the odometer entity in **Developer tools** → **States** and make sure it has a numeric value.
- While the odometer entity is unavailable or not numeric, the sensors keep the last valid reading. If there has never been a valid reading since Home Assistant started, they show "Unavailable".
- Missing readings are only logged at debug level. Enable debug logging for `custom_components.car_rental_tracker` to see them.
