/**
 * Car Rental Tracker Card for Home Assistant
 * 
 * A custom Lovelace card for visualizing car rental contract status,
 * KM usage, and projections.
 */

class CarRentalCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._config = null;
    this._hass = null;
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error('Please define an entity (status sensor)');
    }

    this._config = config;
    this.render();
  }

  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  getCardSize() {
    return 6;
  }

  render() {
    if (!this._config || !this._hass) {
      return;
    }

    const entityId = this._config.entity;
    const statusEntity = this._hass.states[entityId];

    if (!statusEntity) {
      this.shadowRoot.innerHTML = `
        <ha-card>
          <div class="card-content">
            <p class="error">Entity not found: ${entityId}</p>
          </div>
        </ha-card>
      `;
      return;
    }

    // Get the device ID from the entity
    const deviceId = statusEntity.attributes.device_id || entityId.split('.')[1].replace('_status', '');
    
    // Find all related sensors
    const sensors = this._findRelatedSensors(deviceId);

    if (!sensors.total_driven) {
      this.shadowRoot.innerHTML = `
        <ha-card>
          <div class="card-content">
            <p class="error">Related sensors not found. Please check configuration.</p>
          </div>
        </ha-card>
      `;
      return;
    }

    const status = statusEntity.state;
    const statusClass = this._getStatusClass(status);

    // Render the card
    this.shadowRoot.innerHTML = `
      ${this._getStyles()}
      <ha-card>
        <div class="card-header">
          <div class="header-title">
            <ha-icon icon="mdi:car"></ha-icon>
            <h1>${this._config.title || 'Car Rental Tracker'}</h1>
          </div>
          <div class="status-badge ${statusClass}">
            ${status.toUpperCase()}
          </div>
        </div>
        
        <div class="card-content">
          ${this._renderMainStats(sensors)}
          ${this._renderProgressBars(sensors)}
          ${this._renderMonthlyStats(sensors)}
          ${this._renderProjections(sensors)}
          ${this._renderAlerts(sensors, status)}
        </div>
      </ha-card>
    `;
  }

  _findRelatedSensors(deviceId) {
    const sensors = {};
    const prefix = `sensor.car_rental_tracker_${deviceId}_`;
    
    // Map of sensor suffixes to property names
    const sensorMap = {
      'current_odometer': 'current_odometer',
      'total_driven': 'total_driven',
      'km_allowed': 'km_allowed',
      'km_remaining': 'km_remaining',
      'km_projected': 'km_projected',
      'time_progress': 'time_progress',
      'km_progress': 'km_progress',
      'monthly_driven': 'monthly_driven',
      'monthly_remaining': 'monthly_remaining',
      'days_remaining': 'days_remaining',
      'projected_overage': 'projected_overage',
      'projected_cost': 'projected_cost',
    };

    // Try to find sensors with and without device prefix
    for (const [suffix, key] of Object.entries(sensorMap)) {
      let entityId = `${prefix}${suffix}`;
      let entity = this._hass.states[entityId];
      
      // If not found, try without device ID
      if (!entity) {
        entityId = `sensor.${suffix}`;
        entity = this._hass.states[entityId];
      }
      
      // Try alternative patterns
      if (!entity) {
        // Search all entities for matching suffix
        for (const eid of Object.keys(this._hass.states)) {
          if (eid.includes(suffix) && eid.includes('car_rental')) {
            entity = this._hass.states[eid];
            break;
          }
        }
      }
      
      if (entity) {
        sensors[key] = entity;
      }
    }

    return sensors;
  }

  _renderMainStats(sensors) {
    return `
      <div class="main-stats">
        <div class="stat-item">
          <div class="stat-icon">
            <ha-icon icon="mdi:counter"></ha-icon>
          </div>
          <div class="stat-value">${this._formatNumber(sensors.current_odometer?.state)} km</div>
          <div class="stat-label">Current Odometer</div>
        </div>
        <div class="stat-item">
          <div class="stat-icon">
            <ha-icon icon="mdi:map-marker-distance"></ha-icon>
          </div>
          <div class="stat-value">${this._formatNumber(sensors.total_driven?.state)} km</div>
          <div class="stat-label">Total Driven</div>
        </div>
        <div class="stat-item">
          <div class="stat-icon">
            <ha-icon icon="mdi:gauge"></ha-icon>
          </div>
          <div class="stat-value">${this._formatNumber(sensors.km_remaining?.state)} km</div>
          <div class="stat-label">KM Remaining</div>
        </div>
        <div class="stat-item">
          <div class="stat-icon">
            <ha-icon icon="mdi:calendar-clock"></ha-icon>
          </div>
          <div class="stat-value">${sensors.days_remaining?.state || 0}</div>
          <div class="stat-label">Days Left</div>
        </div>
      </div>
    `;
  }

  _renderProgressBars(sensors) {
    const timeProgress = parseFloat(sensors.time_progress?.state || 0);
    const kmProgress = parseFloat(sensors.km_progress?.state || 0);
    
    const timeClass = timeProgress > 90 ? 'warning' : 'ok';
    const kmClass = this._getProgressClass(kmProgress, timeProgress);

    return `
      <div class="progress-section">
        <h2>Progress Overview</h2>
        
        <div class="progress-item">
          <div class="progress-header">
            <span class="progress-label">
              <ha-icon icon="mdi:clock-outline"></ha-icon>
              Time Elapsed
            </span>
            <span class="progress-value">${timeProgress.toFixed(1)}%</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill ${timeClass}" style="width: ${Math.min(timeProgress, 100)}%"></div>
          </div>
        </div>

        <div class="progress-item">
          <div class="progress-header">
            <span class="progress-label">
              <ha-icon icon="mdi:speedometer"></ha-icon>
              KM Usage
            </span>
            <span class="progress-value">${kmProgress.toFixed(1)}%</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill ${kmClass}" style="width: ${Math.min(kmProgress, 100)}%"></div>
          </div>
        </div>

        ${this._renderPaceIndicator(timeProgress, kmProgress)}
      </div>
    `;
  }

  _renderPaceIndicator(timeProgress, kmProgress) {
    const difference = kmProgress - timeProgress;
    let paceText, paceClass, icon;

    if (Math.abs(difference) < 5) {
      paceText = 'On Pace';
      paceClass = 'ok';
      icon = 'mdi:check-circle';
    } else if (difference > 0) {
      paceText = `${difference.toFixed(1)}% Ahead - Slow Down!`;
      paceClass = 'warning';
      icon = 'mdi:alert-circle';
    } else {
      paceText = `${Math.abs(difference).toFixed(1)}% Behind - You Can Drive More`;
      paceClass = 'ok';
      icon = 'mdi:information';
    }

    return `
      <div class="pace-indicator ${paceClass}">
        <ha-icon icon="${icon}"></ha-icon>
        <span>${paceText}</span>
      </div>
    `;
  }

  _renderMonthlyStats(sensors) {
    const monthlyDriven = parseFloat(sensors.monthly_driven?.state || 0);
    const monthlyRemaining = parseFloat(sensors.monthly_remaining?.state || 0);
    const monthlyAllowance = monthlyDriven + monthlyRemaining;
    const monthlyProgress = monthlyAllowance > 0 ? (monthlyDriven / monthlyAllowance * 100) : 0;

    return `
      <div class="monthly-section">
        <h2>This Month</h2>
        <div class="monthly-stats">
          <div class="monthly-item">
            <span class="monthly-label">Driven</span>
            <span class="monthly-value">${this._formatNumber(monthlyDriven)} km</span>
          </div>
          <div class="monthly-item">
            <span class="monthly-label">Remaining</span>
            <span class="monthly-value">${this._formatNumber(monthlyRemaining)} km</span>
          </div>
          <div class="monthly-item">
            <span class="monthly-label">Allowance</span>
            <span class="monthly-value">${this._formatNumber(monthlyAllowance)} km</span>
          </div>
        </div>
        <div class="progress-bar monthly-progress">
          <div class="progress-fill ${this._getProgressClass(monthlyProgress, 50)}" 
               style="width: ${Math.min(monthlyProgress, 100)}%">
          </div>
        </div>
        <div class="monthly-percentage">${monthlyProgress.toFixed(1)}% of monthly allowance used</div>
      </div>
    `;
  }

  _renderProjections(sensors) {
    const kmProjected = parseFloat(sensors.km_projected?.state || 0);
    const kmAllowed = parseFloat(sensors.km_allowed?.state || 0);
    const projectedOverage = parseFloat(sensors.projected_overage?.state || 0);
    const projectedCost = parseFloat(sensors.projected_cost?.state || 0);

    const isOverProjected = kmProjected > kmAllowed;

    return `
      <div class="projections-section">
        <h2>Projections</h2>
        <div class="projection-stats">
          <div class="projection-item">
            <div class="projection-label">
              <ha-icon icon="mdi:chart-line"></ha-icon>
              Projected KM at End
            </div>
            <div class="projection-value ${isOverProjected ? 'warning' : ''}">${this._formatNumber(kmProjected)} km</div>
          </div>
          ${isOverProjected ? `
            <div class="projection-item warning">
              <div class="projection-label">
                <ha-icon icon="mdi:alert-circle"></ha-icon>
                Projected Overage
              </div>
              <div class="projection-value">${this._formatNumber(projectedOverage)} km</div>
            </div>
            <div class="projection-item warning">
              <div class="projection-label">
                <ha-icon icon="mdi:currency-usd"></ha-icon>
                Estimated Cost
              </div>
              <div class="projection-value">$${projectedCost.toFixed(2)}</div>
            </div>
          ` : ''}
        </div>
      </div>
    `;
  }

  _renderAlerts(sensors, status) {
    const alerts = [];
    
    const kmProgress = parseFloat(sensors.km_progress?.state || 0);
    const timeProgress = parseFloat(sensors.time_progress?.state || 0);
    const projectedOverage = parseFloat(sensors.projected_overage?.state || 0);

    if (status === 'critical') {
      alerts.push({
        icon: 'mdi:alert-circle',
        message: 'CRITICAL: You have exceeded your KM allowance!',
        class: 'critical'
      });
    } else if (status === 'warning') {
      if (projectedOverage > 0) {
        alerts.push({
          icon: 'mdi:alert',
          message: `WARNING: You are projected to exceed your allowance by ${this._formatNumber(projectedOverage)} km`,
          class: 'warning'
        });
      }
      if (kmProgress > timeProgress + 10) {
        alerts.push({
          icon: 'mdi:speedometer-slow',
          message: 'You are driving faster than your contract pace. Consider slowing down.',
          class: 'warning'
        });
      }
    }

    if (alerts.length === 0) {
      return '';
    }

    return `
      <div class="alerts-section">
        ${alerts.map(alert => `
          <div class="alert ${alert.class}">
            <ha-icon icon="${alert.icon}"></ha-icon>
            <span>${alert.message}</span>
          </div>
        `).join('')}
      </div>
    `;
  }

  _getStatusClass(status) {
    const statusMap = {
      'ok': 'status-ok',
      'warning': 'status-warning',
      'critical': 'status-critical'
    };
    return statusMap[status] || 'status-ok';
  }

  _getProgressClass(progress, timeProgress) {
    if (progress >= 100) {
      return 'critical';
    } else if (progress > 85 || progress > timeProgress + 10) {
      return 'warning';
    }
    return 'ok';
  }

  _formatNumber(value) {
    if (value === null || value === undefined) {
      return '0';
    }
    const num = parseFloat(value);
    return num.toLocaleString(undefined, { maximumFractionDigits: 1 });
  }

  _getStyles() {
    return `
      <style>
        :host {
          display: block;
        }

        ha-card {
          padding: 16px;
          background: var(--ha-card-background, var(--card-background-color, white));
          border-radius: var(--ha-card-border-radius, 12px);
          box-shadow: var(--ha-card-box-shadow, 0 2px 8px rgba(0,0,0,0.1));
        }

        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }

        .header-title {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .header-title ha-icon {
          --mdc-icon-size: 32px;
          color: var(--primary-color);
        }

        .header-title h1 {
          margin: 0;
          font-size: 24px;
          font-weight: 500;
          color: var(--primary-text-color);
        }

        .status-badge {
          padding: 6px 16px;
          border-radius: 16px;
          font-size: 12px;
          font-weight: 600;
          letter-spacing: 0.5px;
        }

        .status-ok {
          background: #4caf50;
          color: white;
        }

        .status-warning {
          background: #ff9800;
          color: white;
        }

        .status-critical {
          background: #f44336;
          color: white;
        }

        .card-content {
          display: flex;
          flex-direction: column;
          gap: 24px;
        }

        .main-stats {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
          gap: 16px;
        }

        .stat-item {
          text-align: center;
          padding: 16px;
          background: var(--secondary-background-color);
          border-radius: 8px;
        }

        .stat-icon ha-icon {
          --mdc-icon-size: 32px;
          color: var(--primary-color);
        }

        .stat-value {
          font-size: 24px;
          font-weight: 600;
          color: var(--primary-text-color);
          margin: 8px 0 4px 0;
        }

        .stat-label {
          font-size: 12px;
          color: var(--secondary-text-color);
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .progress-section h2,
        .monthly-section h2,
        .projections-section h2 {
          font-size: 18px;
          font-weight: 500;
          color: var(--primary-text-color);
          margin: 0 0 16px 0;
        }

        .progress-item {
          margin-bottom: 20px;
        }

        .progress-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }

        .progress-label {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 14px;
          color: var(--primary-text-color);
        }

        .progress-label ha-icon {
          --mdc-icon-size: 18px;
        }

        .progress-value {
          font-size: 14px;
          font-weight: 600;
          color: var(--primary-text-color);
        }

        .progress-bar {
          height: 24px;
          background: var(--secondary-background-color);
          border-radius: 12px;
          overflow: hidden;
          position: relative;
        }

        .progress-fill {
          height: 100%;
          transition: width 0.3s ease;
          border-radius: 12px;
        }

        .progress-fill.ok {
          background: linear-gradient(90deg, #4caf50, #66bb6a);
        }

        .progress-fill.warning {
          background: linear-gradient(90deg, #ff9800, #ffa726);
        }

        .progress-fill.critical {
          background: linear-gradient(90deg, #f44336, #ef5350);
        }

        .pace-indicator {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px;
          border-radius: 8px;
          margin-top: 12px;
          font-size: 14px;
          font-weight: 500;
        }

        .pace-indicator.ok {
          background: rgba(76, 175, 80, 0.1);
          color: #4caf50;
        }

        .pace-indicator.warning {
          background: rgba(255, 152, 0, 0.1);
          color: #ff9800;
        }

        .pace-indicator ha-icon {
          --mdc-icon-size: 20px;
        }

        .monthly-stats {
          display: flex;
          justify-content: space-around;
          margin-bottom: 12px;
        }

        .monthly-item {
          text-align: center;
        }

        .monthly-label {
          display: block;
          font-size: 12px;
          color: var(--secondary-text-color);
          margin-bottom: 4px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .monthly-value {
          display: block;
          font-size: 18px;
          font-weight: 600;
          color: var(--primary-text-color);
        }

        .monthly-progress {
          height: 16px;
          margin-bottom: 8px;
        }

        .monthly-percentage {
          text-align: center;
          font-size: 12px;
          color: var(--secondary-text-color);
        }

        .projection-stats {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .projection-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px;
          background: var(--secondary-background-color);
          border-radius: 8px;
        }

        .projection-item.warning {
          background: rgba(255, 152, 0, 0.1);
        }

        .projection-label {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 14px;
          color: var(--primary-text-color);
        }

        .projection-label ha-icon {
          --mdc-icon-size: 20px;
        }

        .projection-value {
          font-size: 18px;
          font-weight: 600;
          color: var(--primary-text-color);
        }

        .projection-value.warning {
          color: #ff9800;
        }

        .alerts-section {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .alert {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 500;
        }

        .alert ha-icon {
          --mdc-icon-size: 24px;
        }

        .alert.warning {
          background: rgba(255, 152, 0, 0.15);
          color: #e65100;
          border-left: 4px solid #ff9800;
        }

        .alert.critical {
          background: rgba(244, 67, 54, 0.15);
          color: #b71c1c;
          border-left: 4px solid #f44336;
        }

        .error {
          color: #f44336;
          padding: 16px;
          text-align: center;
        }
      </style>
    `;
  }
}

customElements.define('car-rental-card', CarRentalCard);

// Register the card with Home Assistant
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'car-rental-card',
  name: 'Car Rental Tracker Card',
  description: 'A card to display car rental contract tracking and KM management',
  preview: true,
  documentationURL: 'https://github.com/b0t-at/ha-car-rental-tracker/tree/main/custom_components/car_rental_tracker',
});
