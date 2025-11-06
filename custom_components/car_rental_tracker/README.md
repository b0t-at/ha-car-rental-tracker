# Car Rental Tracker for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

A comprehensive Home Assistant integration for tracking car rental contracts with KM limits. Monitor your usage, get projections, and avoid overage charges with beautiful visualizations.

## Features

### 📊 Comprehensive Tracking
- **Real-time Odometer**: Track current KM from any Home Assistant sensor
- **Total Distance**: Automatically calculate total KM driven since rental start
- **Allowance Management**: Configure monthly KM allowances and track usage
- **Projections**: Get accurate projections of KM at contract end based on current pace

### 📈 Dual Progress Tracking
- **Time Progress**: See how much of your contract period has elapsed
- **KM Progress**: Track percentage of KM allowance used
- **Pace Indicator**: Know if you're ahead or behind the ideal pace

### 📅 Monthly Statistics
- Current month's KM driven
- Remaining KM for this month
- Monthly allowance tracking
- Visual progress bars

### ⚠️ Smart Alerts
- **OK Status**: Usage is within expected limits
- **Warning Status**: Projected to exceed allowance or driving too fast
- **Critical Status**: Already exceeded KM allowance

### 💰 Cost Projections
- Configure overage cost per KM
- See projected overage charges
- Estimate final costs if you exceed limits

### 🎨 Beautiful Dashboard Card
- Custom Lovelace card with modern design
- Color-coded status indicators
- Progress bars and statistics
- Responsive layout for mobile and desktop

## Installation

### HACS Installation (Recommended)

1. Open **HACS** in Home Assistant
2. Click on **Integrations**
3. Click the **three dots** in the top right corner
4. Select **Custom repositories**
5. Add this repository URL: `https://github.com/Utesgui/HA-plugins`
6. Select **Integration** as the category
7. Click **Add**
8. Find **Car Rental Tracker** in HACS and click **Download**
9. Restart Home Assistant

### Manual Installation

1. Download the `car_rental_tracker` folder from this repository
2. Copy it to your `config/custom_components/` directory
3. Restart Home Assistant

## Configuration

### Step 1: Add the Integration

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for **Car Rental Tracker**
3. Fill in the configuration form:
   - **Start Date**: When you picked up the rental car
   - **End Date**: When you need to return the car
   - **KM Allowance per Month**: Your monthly KM limit
   - **Initial Odometer**: The odometer reading when you got the car
   - **Overage Cost per KM**: Cost per KM if you exceed the limit
   - **Odometer Sensor Entity**: Select an existing sensor that tracks your car's odometer

### Step 2: Add the Dashboard Card

#### Option A: Visual Editor

1. Add the custom card resource:
   - Go to **Settings** → **Dashboards** → **Resources**
   - Click **Add Resource**
   - URL: `/local/community/car_rental_tracker/car-rental-card.js`
   - Resource type: **JavaScript Module**

2. Add the card to your dashboard:
   - Edit your dashboard
   - Click **Add Card**
   - Search for **Custom: Car Rental Card**
   - Configure the entity (use the status sensor)

#### Option B: YAML Configuration

1. Add the resource to your `configuration.yaml` or dashboard configuration:

```yaml
lovelace:
  resources:
    - url: /hacsfiles/car_rental_tracker/car-rental-card.js
      type: module
```

2. Add the card to your dashboard:

```yaml
type: custom:car-rental-card
entity: sensor.car_rental_tracker_XXXXX_status
title: My Rental Car
```

Replace `XXXXX` with your integration's unique ID.

## Sensors Created

The integration creates the following sensors:

| Sensor | Description | Unit |
|--------|-------------|------|
| **Current Odometer** | Live odometer reading from configured sensor | km |
| **Total Driven** | Total KM driven since rental start | km |
| **KM Allowed** | Total KM allowance for contract period | km |
| **KM Remaining** | Remaining KM before exceeding allowance | km |
| **KM Projected** | Projected total KM at contract end | km |
| **Time Progress** | Percentage of time elapsed | % |
| **KM Progress** | Percentage of KM allowance used | % |
| **Monthly Driven** | KM driven in current month | km |
| **Monthly Remaining** | Remaining KM for current month | km |
| **Days Remaining** | Days until contract ends | days |
| **Projected Overage** | Projected excess KM at contract end | km |
| **Projected Cost** | Estimated overage cost | $ |
| **Status** | Overall status (ok/warning/critical) | - |

## Example Dashboard Configuration

### Simple Card

```yaml
type: custom:car-rental-card
entity: sensor.car_rental_tracker_status
title: My Rental Car
```

### Multiple Rentals

If you have multiple rental cars, add multiple integrations and cards:

```yaml
type: vertical-stack
cards:
  - type: custom:car-rental-card
    entity: sensor.car_rental_tracker_car1_status
    title: Personal Car Rental
  - type: custom:car-rental-card
    entity: sensor.car_rental_tracker_car2_status
    title: Business Car Rental
```

### Using Individual Sensors

You can also create custom cards using individual sensors:

```yaml
type: entities
entities:
  - entity: sensor.car_rental_tracker_total_driven
    name: Total Driven
  - entity: sensor.car_rental_tracker_km_remaining
    name: KM Left
  - entity: sensor.car_rental_tracker_days_remaining
    name: Days Left
  - entity: sensor.car_rental_tracker_status
    name: Status
```

## Automations

Create automations to get notified about your rental status:

### Warning Notification

```yaml
automation:
  - alias: Car Rental Warning
    trigger:
      - platform: state
        entity_id: sensor.car_rental_tracker_status
        to: "warning"
    action:
      - service: notify.mobile_app
        data:
          title: "Car Rental Warning"
          message: "You're driving faster than your contract pace. Consider slowing down to avoid overage charges."
```

### Critical Alert

```yaml
automation:
  - alias: Car Rental Critical
    trigger:
      - platform: state
        entity_id: sensor.car_rental_tracker_status
        to: "critical"
    action:
      - service: notify.mobile_app
        data:
          title: "Car Rental CRITICAL"
          message: "You have exceeded your KM allowance! Additional charges will apply."
          data:
            priority: high
```

### Monthly Summary

```yaml
automation:
  - alias: Car Rental Monthly Summary
    trigger:
      - platform: time
        at: "09:00:00"
      - platform: template
        value_template: "{{ now().day == 1 }}"
    action:
      - service: notify.mobile_app
        data:
          title: "Car Rental Monthly Summary"
          message: >
            Last month: {{ states('sensor.car_rental_tracker_monthly_driven') }} km driven.
            This month allowance: {{ states('sensor.car_rental_tracker_monthly_allowance') }} km.
```

## Calculations

### Time Progress
```
Time Progress = (Days Elapsed / Total Days) × 100
```

### KM Progress
```
KM Progress = (Total Driven / KM Allowed) × 100
```

### Projected KM
```
Daily Average = Total Driven / Days Elapsed
Projected KM = Total Driven + (Daily Average × Days Remaining)
```

### Monthly Statistics
The integration tracks which rental month you're in and calculates statistics for the current month based on your contract start date, not calendar months.

## Troubleshooting

### Odometer sensor not updating
- Ensure your odometer sensor is working and reporting valid numeric values
- Check Home Assistant logs for any errors
- The integration updates when the odometer sensor changes or every 5 minutes

### Sensors showing "Unknown"
- Wait a few minutes after setup for initial data to populate
- Check that all configuration values are correct
- Verify your odometer entity is providing valid data

### Card not displaying correctly
- Clear browser cache
- Verify the card resource is loaded in Developer Tools → Resources
- Check browser console for JavaScript errors

### Wrong calculations
- Verify your start and end dates are correct
- Ensure initial odometer reading is accurate
- Check that your odometer sensor is reporting in kilometers (not miles)

## Support

For issues, feature requests, or questions:
- Open an issue on [GitHub](https://github.com/Utesgui/HA-plugins/issues)
- Check existing issues for solutions
- Provide Home Assistant logs when reporting bugs

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](../../../LICENSE) file for details.

## Changelog

### Version 1.0.0
- Initial release
- Core functionality: tracking, calculations, and projections
- Custom Lovelace card with visual dashboard
- Monthly statistics
- Status alerts and warnings
- Cost projections
