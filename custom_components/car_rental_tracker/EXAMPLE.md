# Car Rental Tracker - Visual Example

## Dashboard Card Example

The Car Rental Tracker card provides a comprehensive, at-a-glance view of your rental status.

### Card Layout

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

### Status Badge Colors

- **🟢 OK (Green)**: Usage is within expected limits, on track
- **🟡 WARNING (Orange)**: Projected to exceed allowance or driving faster than pace
- **🔴 CRITICAL (Red)**: Already exceeded KM allowance

### Warning Example

When you're ahead of pace:

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
┃  💰 Estimated Cost                 $714.00                  ┃
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

### Critical Example

When you've exceeded your allowance:

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

## Configuration Examples

### Basic Configuration

```yaml
type: custom:car-rental-card
entity: sensor.car_rental_tracker_XXXXX_status
title: My Rental Car
```

### In a Dashboard View

```yaml
title: Car Management
path: car
icon: mdi:car
cards:
  - type: custom:car-rental-card
    entity: sensor.car_rental_tracker_status
    title: Monthly Rental

  - type: entities
    title: Quick Stats
    entities:
      - sensor.car_rental_tracker_days_remaining
      - sensor.car_rental_tracker_km_remaining
      - sensor.car_rental_tracker_projected_cost
```

### Multiple Rental Cars

```yaml
type: vertical-stack
cards:
  - type: custom:car-rental-card
    entity: sensor.car_rental_tracker_personal_status
    title: Personal Rental
  
  - type: custom:car-rental-card
    entity: sensor.car_rental_tracker_business_status
    title: Business Rental
```

## Automation Examples

### Daily Summary Notification

```yaml
automation:
  - alias: Daily Rental Summary
    trigger:
      - platform: time
        at: "20:00:00"
    action:
      - service: notify.mobile_app
        data:
          title: "Car Rental Daily Summary"
          message: >
            📊 Today's Status:
            Driven: {{ states('sensor.car_rental_tracker_total_driven') }} km
            Remaining: {{ states('sensor.car_rental_tracker_km_remaining') }} km
            Days Left: {{ states('sensor.car_rental_tracker_days_remaining') }}
            Status: {{ states('sensor.car_rental_tracker_status') | upper }}
```

### Overage Warning

```yaml
automation:
  - alias: Rental Overage Warning
    trigger:
      - platform: state
        entity_id: sensor.car_rental_tracker_status
        to: "warning"
    action:
      - service: persistent_notification.create
        data:
          title: "⚠️ Car Rental Warning"
          message: >
            You're driving faster than your contract pace!
            Projected overage: {{ states('sensor.car_rental_tracker_projected_overage') }} km
            Estimated cost: ${{ states('sensor.car_rental_tracker_projected_cost') }}
```

### Monthly Report

```yaml
automation:
  - alias: Monthly Rental Report
    trigger:
      - platform: template
        value_template: "{{ now().day == 1 }}"
    action:
      - service: notify.email
        data:
          title: "Car Rental Monthly Report"
          message: >
            📈 Last Month Summary:
            - Driven: {{ states('sensor.car_rental_tracker_monthly_driven') }} km
            - Allowance: {{ states('sensor.car_rental_tracker_monthly_allowance') }} km
            - Efficiency: {{ (states('sensor.car_rental_tracker_monthly_driven') | float / states('sensor.car_rental_tracker_monthly_allowance') | float * 100) | round(1) }}%
            
            Current Status: {{ states('sensor.car_rental_tracker_status') | upper }}
            Days Remaining: {{ states('sensor.car_rental_tracker_days_remaining') }}
```

## Features Showcase

### 📊 Comprehensive Statistics
- Live odometer reading
- Total KM driven
- KM remaining in contract
- Days until contract end
- Monthly breakdowns

### 📈 Smart Projections
- Projected total KM at contract end
- Estimated overage (if any)
- Projected additional costs
- Daily/monthly average calculations

### ⚡ Real-time Updates
- Updates when odometer sensor changes
- Automatic recalculation every 5 minutes
- Instant status changes

### 🎨 Beautiful Visuals
- Modern, clean design
- Color-coded progress bars
- Responsive layout
- Dark mode support (via Home Assistant theme)

### 🔔 Smart Alerts
- Automatic status detection
- Warning when ahead of pace
- Critical alert when over limit
- Actionable recommendations

### 🔧 Easy Configuration
- UI-based setup (no YAML required)
- Entity selector for odometer
- Date pickers for contract period
- Validation and error handling
- Reconfigurable through options flow

## Use Cases

1. **Long-term Rentals**: Track monthly or yearly rental contracts
2. **Lease Management**: Monitor lease agreements with KM limits
3. **Fleet Management**: Track multiple vehicles
4. **Cost Control**: Avoid unexpected overage charges
5. **Trip Planning**: Know how many KM you have left for trips

## Tips for Best Results

1. **Accurate Initial Reading**: Make sure to record the exact odometer reading when you pick up the car
2. **Regular Updates**: Ensure your odometer sensor updates regularly (daily is ideal)
3. **Contract Dates**: Double-check your start and end dates match your contract
4. **Monthly Allowance**: Verify your monthly KM allowance is correct
5. **Overage Cost**: Enter the correct per-KM overage cost from your contract

## Troubleshooting

### Card Not Showing
- Verify the card resource is loaded
- Check Developer Tools → Resources
- Clear browser cache
- Reload the page

### Wrong Calculations
- Verify contract dates are correct
- Check initial odometer reading
- Ensure odometer sensor is in kilometers (not miles)
- Verify monthly allowance matches your contract

### Sensor Not Updating
- Check that your odometer sensor is working
- View the sensor in Developer Tools → States
- Verify the sensor reports numeric values
- Check Home Assistant logs for errors
