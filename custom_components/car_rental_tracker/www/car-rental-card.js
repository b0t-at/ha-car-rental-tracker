/**
 * Car Rental Tracker Card for Home Assistant
 *
 * A custom Lovelace card for visualizing car rental contract status,
 * KM usage, and projections.
 *
 * Config:
 *   type: custom:car-rental-card
 *   entity: <any sensor of a Car Rental Tracker device, e.g. its Status sensor>
 *   title: <optional card title>
 */

const CARD_TYPE = 'car-rental-card';
const PLATFORM = 'car_rental_tracker';
const DASH = '—';
const UNAVAILABLE_STATES = ['unknown', 'unavailable'];
const STATUS_CLASSES = ['ok', 'warning', 'critical'];

// Sensor keys; each equals the sensor's translation_key and entity_id suffix.
const SENSOR_KEYS = [
  'current_odometer',
  'total_driven',
  'km_allowed',
  'km_remaining',
  'km_projected',
  'time_progress',
  'km_progress',
  'monthly_driven',
  'monthly_remaining',
  'monthly_allowance',
  'days_remaining',
  'days_elapsed',
  'projected_overage',
  'projected_cost',
  'status',
];

// Card is "ahead of pace" when usage exceeds time elapsed by more than this.
const PACE_TOLERANCE_PCT = 5;
const PACE_WARNING_PCT = 10;
const CARD_SIZE = 12;
const CARD_SIZE_ERROR = 2;

const progressItem = (ref, icon, label) => `
  <div class="progress-item">
    <div class="progress-header">
      <span class="progress-label">
        <ha-icon icon="${icon}"></ha-icon>
        ${label}
      </span>
      <span class="progress-value" data-ref="${ref}Value"></span>
    </div>
    <div class="progress-bar" data-ref="${ref}Bar" role="progressbar"
         aria-label="${label}" aria-valuemin="0" aria-valuemax="100">
      <div class="progress-fill" data-ref="${ref}Fill"></div>
    </div>
  </div>
`;

const statItem = (ref, icon, label) => `
  <div class="stat-item">
    <div class="stat-icon"><ha-icon icon="${icon}"></ha-icon></div>
    <div class="stat-value" data-ref="${ref}"></div>
    <div class="stat-label">${label}</div>
  </div>
`;

const monthlyItem = (ref, label) => `
  <div class="monthly-item">
    <span class="monthly-label">${label}</span>
    <span class="monthly-value" data-ref="${ref}"></span>
  </div>
`;

const projectionItem = (ref, icon, label) => `
  <div class="projection-item" data-ref="${ref}Row">
    <div class="projection-label">
      <ha-icon icon="${icon}"></ha-icon>
      ${label}
    </div>
    <div class="projection-value" data-ref="${ref}"></div>
  </div>
`;

// Static markup only: every dynamic value is set later via textContent/attributes.
const CARD_TEMPLATE = `
  <ha-card>
    <div class="message" data-ref="message" hidden></div>
    <div class="content" data-ref="content">
      <div class="card-header">
        <div class="header-title">
          <ha-icon icon="mdi:car"></ha-icon>
          <h2 data-ref="title"></h2>
        </div>
        <div class="status-badge" data-ref="status"></div>
      </div>

      <div class="main-stats">
        ${statItem('odometer', 'mdi:counter', 'Current Odometer')}
        ${statItem('totalDriven', 'mdi:map-marker-distance', 'Total Driven')}
        ${statItem('kmRemaining', 'mdi:gauge', 'KM Remaining')}
        ${statItem('daysRemaining', 'mdi:calendar-clock', 'Days Left')}
      </div>

      <section class="section">
        <h3>Progress Overview</h3>
        ${progressItem('time', 'mdi:clock-outline', 'Time Elapsed')}
        ${progressItem('km', 'mdi:speedometer', 'KM Usage')}
        <div class="pace-indicator" data-ref="pace">
          <ha-icon data-ref="paceIcon"></ha-icon>
          <span data-ref="paceText"></span>
        </div>
      </section>

      <section class="section">
        <h3>This Month</h3>
        <div class="monthly-stats">
          ${monthlyItem('monthlyDriven', 'Driven')}
          ${monthlyItem('monthlyRemaining', 'Remaining')}
          ${monthlyItem('monthlyAllowance', 'Allowance')}
        </div>
        <div class="progress-bar monthly-progress" data-ref="monthlyBar" role="progressbar"
             aria-label="Monthly allowance used" aria-valuemin="0" aria-valuemax="100">
          <div class="progress-fill" data-ref="monthlyFill"></div>
        </div>
        <div class="monthly-percentage" data-ref="monthlyValue"></div>
      </section>

      <section class="section">
        <h3>Projections</h3>
        <div class="projection-stats">
          ${projectionItem('projected', 'mdi:chart-line', 'Projected KM at End')}
          ${projectionItem('overage', 'mdi:alert-circle', 'Projected Overage')}
          ${projectionItem('cost', 'mdi:cash', 'Estimated Cost')}
        </div>
      </section>

      <div class="alerts" data-ref="alerts" role="status"></div>
    </div>
  </ha-card>
`;

class CarRentalCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._config = null;
    this._hass = null;
    this._ids = null;
    this._entitiesRef = undefined;
    this._refs = null;
    this._alertsSignature = null;
    this._isError = false;
  }

  static getStubConfig(hass) {
    const registry = Object.values((hass && hass.entities) || {});
    const fromRegistry = registry.find(
      (e) => e.platform === PLATFORM && e.translation_key === 'status'
    );
    if (fromRegistry) {
      return { entity: fromRegistry.entity_id };
    }
    const fromStates = Object.keys((hass && hass.states) || {}).find(
      (id) => id.startsWith(`sensor.${PLATFORM}_`) && id.endsWith('_status')
    );
    return { entity: fromStates || '' };
  }

  setConfig(config) {
    if (!config || typeof config.entity !== 'string' || !config.entity.includes('.')) {
      throw new Error(
        "Please set 'entity' to a sensor of your Car Rental Tracker device " +
        '(for example its Status sensor, sensor.car_rental_tracker_<start_date>_status)'
      );
    }
    if (config.title !== undefined && typeof config.title !== 'string') {
      throw new Error("'title' must be a string");
    }
    this._config = { ...config };
    this._ids = null;
    if (this._hass) {
      this._resolveIds();
      this._render();
    }
  }

  set hass(hass) {
    const previous = this._hass;
    this._hass = hass;
    if (!this._config) {
      return;
    }
    const needsResolve = !this._ids || hass.entities !== this._entitiesRef;
    if (needsResolve) {
      this._resolveIds();
    }
    if (!needsResolve && previous && !this._hasRelevantChange(previous, hass)) {
      return;
    }
    this._render();
  }

  getCardSize() {
    return this._isError ? CARD_SIZE_ERROR : CARD_SIZE;
  }

  getGridOptions() {
    return { columns: 12, min_columns: 6 };
  }

  // ---------------------------------------------------------------------------
  // Entity resolution
  // ---------------------------------------------------------------------------

  _resolveIds() {
    const hass = this._hass;
    const entityId = this._config.entity;
    const registry = hass.entities || {};
    const entry = registry[entityId];
    this._entitiesRef = hass.entities;
    this._ids = entry && entry.device_id
      ? this._resolveFromDevice(registry, entry.device_id)
      : this._resolveFromPrefix(entityId);
  }

  _resolveFromDevice(registry, deviceId) {
    const siblings = Object.values(registry).filter(
      (e) => e.device_id === deviceId && e.entity_id.startsWith('sensor.')
    );
    const ids = {};
    for (const e of siblings) {
      if (SENSOR_KEYS.includes(e.translation_key)) {
        ids[e.translation_key] = e.entity_id;
      }
    }
    // Legacy fallback: registry without translation_key -> match id suffix.
    for (const key of SENSOR_KEYS) {
      if (ids[key]) {
        continue;
      }
      const match = siblings.find((e) => e.entity_id.endsWith(`_${key}`));
      if (match) {
        ids[key] = match.entity_id;
      }
    }
    return ids;
  }

  _resolveFromPrefix(entityId) {
    // No registry info: derive siblings from the configured id's suffix.
    const key = SENSOR_KEYS.find((k) => entityId.endsWith(`_${k}`));
    if (!key) {
      return { status: entityId };
    }
    const base = entityId.slice(0, -(key.length + 1));
    const ids = {};
    for (const k of SENSOR_KEYS) {
      ids[k] = `${base}_${k}`;
    }
    return ids;
  }

  _hasRelevantChange(previous, hass) {
    if (previous.locale !== hass.locale || previous.config !== hass.config) {
      return true;
    }
    const ids = [this._config.entity, ...Object.values(this._ids || {})];
    return ids.some((id) => previous.states[id] !== hass.states[id]);
  }

  _sensors() {
    const sensors = {};
    for (const [key, id] of Object.entries(this._ids || {})) {
      sensors[key] = this._hass.states[id];
    }
    return sensors;
  }

  // ---------------------------------------------------------------------------
  // Rendering
  // ---------------------------------------------------------------------------

  _ensureDom() {
    if (this._refs) {
      return;
    }
    this.shadowRoot.innerHTML = `<style>${CarRentalCard._styles()}</style>${CARD_TEMPLATE}`;
    this._refs = {};
    this.shadowRoot.querySelectorAll('[data-ref]').forEach((el) => {
      this._refs[el.dataset.ref] = el;
    });
    this._refs.overageRow.classList.add('warning');
    this._refs.costRow.classList.add('warning');
  }

  _findError(sensors) {
    const entityId = this._config.entity;
    const hass = this._hass;
    if (!hass.states[entityId] && !(hass.entities && hass.entities[entityId])) {
      return `Entity not found: ${entityId}`;
    }
    if (!sensors.total_driven) {
      return 'Related Car Rental Tracker sensors not found. Please check the configured entity.';
    }
    return null;
  }

  _render() {
    this._ensureDom();
    const sensors = this._sensors();
    const error = this._findError(sensors);
    this._isError = Boolean(error);
    this._refs.message.hidden = !error;
    this._refs.content.hidden = Boolean(error);
    if (error) {
      this._refs.message.textContent = error;
      return;
    }

    this._refs.title.textContent = this._config.title || 'Car Rental Tracker';
    this._renderStatus(sensors.status);
    this._renderMainStats(sensors);
    this._renderProgress(sensors);
    this._renderMonthly(sensors);
    this._renderProjections(sensors);
    this._renderAlerts(sensors);
  }

  _renderStatus(stateObj) {
    const status = this._statusClass(stateObj);
    const badge = this._refs.status;
    badge.className = `status-badge status-${status}`;
    if (!stateObj) {
      badge.textContent = DASH;
    } else if (typeof this._hass.formatEntityState === 'function') {
      badge.textContent = this._hass.formatEntityState(stateObj);
    } else {
      badge.textContent = stateObj.state;
    }
  }

  _renderMainStats(s) {
    this._refs.odometer.textContent = this._formatDistance(s.current_odometer, 0);
    this._refs.totalDriven.textContent = this._formatDistance(s.total_driven);
    this._refs.kmRemaining.textContent = this._formatDistance(s.km_remaining);
    const days = this._num(s.days_remaining);
    this._refs.daysRemaining.textContent = days === null ? DASH : this._formatNumber(days, 0);
  }

  _renderProgress(s) {
    const timeProgress = this._num(s.time_progress);
    const kmProgress = this._num(s.km_progress);
    const kmClass = kmProgress === null ? 'unknown' : this._statusClass(s.status);
    this._setBar('time', timeProgress, timeProgress === null ? 'unknown' : 'neutral');
    this._setBar('km', kmProgress, kmClass);
    this._renderPace(timeProgress, kmProgress);
  }

  _renderPace(timeProgress, kmProgress) {
    const pace = this._refs.pace;
    pace.hidden = timeProgress === null || kmProgress === null;
    if (pace.hidden) {
      return;
    }
    const difference = kmProgress - timeProgress;
    let text;
    let cls;
    let icon;
    if (Math.abs(difference) < PACE_TOLERANCE_PCT) {
      [text, cls, icon] = ['On Pace', 'ok', 'mdi:check-circle'];
    } else if (difference > 0) {
      text = `${this._formatNumber(difference, 1)}% Ahead - Slow Down!`;
      [cls, icon] = ['warning', 'mdi:alert-circle'];
    } else {
      text = `${this._formatNumber(-difference, 1)}% Behind - You Can Drive More`;
      [cls, icon] = ['ok', 'mdi:information'];
    }
    pace.className = `pace-indicator ${cls}`;
    this._refs.paceIcon.setAttribute('icon', icon);
    this._refs.paceText.textContent = text;
  }

  _renderMonthly(s) {
    const driven = this._num(s.monthly_driven);
    const remaining = this._num(s.monthly_remaining);
    let allowance = this._num(s.monthly_allowance);
    let allowanceObj = s.monthly_allowance;
    if (allowance === null && driven !== null && remaining !== null) {
      // Older integration versions without the Monthly Allowance sensor.
      allowance = driven + remaining;
      allowanceObj = s.monthly_driven;
    }
    const progress = driven !== null && allowance > 0 ? (driven / allowance) * 100 : null;

    this._refs.monthlyDriven.textContent = this._formatDistance(s.monthly_driven);
    this._refs.monthlyRemaining.textContent = this._formatDistance(s.monthly_remaining);
    this._refs.monthlyAllowance.textContent = allowance === null
      ? DASH
      : `${this._formatNumber(allowance, 1)} ${this._unit(allowanceObj, 'km')}`;

    // After the contract ends the monthly sensors are frozen at the last
    // contract month, so that month counts as fully elapsed.
    const contractEnded = this._num(s.days_remaining) === 0;
    const elapsedPct = contractEnded ? 100 : this._monthElapsedPct();
    this._setBar('monthly', progress, this._progressClass(progress, elapsedPct));
    this._refs.monthlyValue.textContent = progress === null
      ? DASH
      : `${this._formatNumber(progress, 1)}% of monthly allowance used`;
  }

  _renderProjections(s) {
    const overage = this._num(s.projected_overage);
    const isOver = overage !== null && overage > 0;
    const projected = this._refs.projected;
    projected.textContent = this._formatDistance(s.km_projected);
    projected.classList.toggle('warning', isOver);
    this._refs.overageRow.hidden = !isOver;
    this._refs.costRow.hidden = !isOver;
    if (isOver) {
      this._refs.overage.textContent = this._formatDistance(s.projected_overage);
      this._refs.cost.textContent = this._formatCost(s.projected_cost);
    }
  }

  _renderAlerts(s) {
    const alerts = this._buildAlerts(s);
    const signature = JSON.stringify(alerts);
    if (signature === this._alertsSignature) {
      return;
    }
    this._alertsSignature = signature;
    const container = this._refs.alerts;
    container.replaceChildren(
      ...alerts.map(({ cls, icon, message }) => {
        const row = document.createElement('div');
        row.className = `alert ${cls}`;
        const iconEl = document.createElement('ha-icon');
        iconEl.setAttribute('icon', icon);
        const text = document.createElement('span');
        text.textContent = message;
        row.append(iconEl, text);
        return row;
      })
    );
    container.hidden = alerts.length === 0;
  }

  _buildAlerts(s) {
    const status = this._statusClass(s.status);
    if (status === 'critical') {
      return [{
        cls: 'critical',
        icon: 'mdi:alert-circle',
        message: 'CRITICAL: You have exceeded your KM allowance!',
      }];
    }
    if (status !== 'warning') {
      return [];
    }
    const alerts = [];
    const overage = this._num(s.projected_overage);
    const kmProgress = this._num(s.km_progress);
    const timeProgress = this._num(s.time_progress);
    if (overage !== null && overage > 0) {
      alerts.push({
        cls: 'warning',
        icon: 'mdi:alert',
        message: `WARNING: You are projected to exceed your allowance by ${this._formatDistance(s.projected_overage)}`,
      });
    }
    if (kmProgress !== null && timeProgress !== null && kmProgress > timeProgress + PACE_WARNING_PCT) {
      alerts.push({
        cls: 'warning',
        icon: 'mdi:speedometer-slow',
        message: 'You are driving faster than your contract pace. Consider slowing down.',
      });
    }
    return alerts;
  }

  _setBar(ref, value, cls) {
    const bar = this._refs[`${ref}Bar`];
    const fill = this._refs[`${ref}Fill`];
    const clamped = value === null ? 0 : Math.max(0, Math.min(value, 100));
    fill.className = `progress-fill ${cls}`;
    fill.style.width = `${clamped}%`;
    if (value === null) {
      bar.removeAttribute('aria-valuenow');
      bar.setAttribute('aria-valuetext', 'Unavailable');
    } else {
      bar.setAttribute('aria-valuenow', String(Math.round(clamped)));
      bar.setAttribute('aria-valuetext', `${this._formatNumber(value, 1)}%`);
    }
    const label = this._refs[`${ref}Value`];
    if (label && ref !== 'monthly') {
      label.textContent = value === null ? DASH : `${this._formatNumber(value, 1)}%`;
    }
  }

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------

  _statusClass(stateObj) {
    const state = stateObj && stateObj.state;
    return STATUS_CLASSES.includes(state) ? state : 'unknown';
  }

  _progressClass(progress, elapsedPct) {
    if (progress === null) {
      return 'unknown';
    }
    if (progress >= 100) {
      return 'critical';
    }
    if (progress > elapsedPct + PACE_WARNING_PCT) {
      return 'warning';
    }
    return 'ok';
  }

  _monthElapsedPct() {
    const now = new Date();
    const daysInMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
    const secondsToday = now.getHours() * 3600 + now.getMinutes() * 60 + now.getSeconds();
    return ((now.getDate() - 1 + secondsToday / 86400) / daysInMonth) * 100;
  }

  _num(stateObj) {
    if (!stateObj || UNAVAILABLE_STATES.includes(stateObj.state)) {
      return null;
    }
    const num = Number.parseFloat(stateObj.state);
    return Number.isFinite(num) ? num : null;
  }

  _unit(stateObj, fallback) {
    const unit = stateObj && stateObj.attributes && stateObj.attributes.unit_of_measurement;
    return unit || fallback;
  }

  _language() {
    return (this._hass.locale && this._hass.locale.language) || this._hass.language || undefined;
  }

  _formatNumber(value, digits = 1) {
    const options = { maximumFractionDigits: digits };
    try {
      return value.toLocaleString(this._language(), options);
    } catch (err) {
      return value.toLocaleString(undefined, options);
    }
  }

  _formatDistance(stateObj, digits = 1) {
    const num = this._num(stateObj);
    if (num === null) {
      return DASH;
    }
    return `${this._formatNumber(num, digits)} ${this._unit(stateObj, 'km')}`;
  }

  _formatCost(stateObj) {
    const num = this._num(stateObj);
    if (num === null) {
      return DASH;
    }
    const currency = this._unit(stateObj, this._hass.config && this._hass.config.currency);
    if (!currency) {
      return this._formatNumber(num, 2);
    }
    try {
      return new Intl.NumberFormat(this._language(), { style: 'currency', currency }).format(num);
    } catch (err) {
      return `${this._formatNumber(num, 2)} ${currency}`;
    }
  }

  static _styles() {
    return `
      :host {
        display: block;
        --crt-ok: var(--success-color, #4caf50);
        --crt-warning: var(--warning-color, #ffa600);
        --crt-critical: var(--error-color, #db4437);
        --crt-neutral: var(--primary-color, #03a9f4);
        --crt-unknown: var(--disabled-text-color, #9e9e9e);
      }
      [hidden] { display: none !important; }
      ha-card { padding: 16px; }

      .content { display: flex; flex-direction: column; gap: 24px; }
      .message { color: var(--crt-critical); padding: 16px; text-align: center; }

      .card-header {
        display: flex; justify-content: space-between; align-items: center; gap: 12px;
      }
      .header-title { display: flex; align-items: center; gap: 12px; min-width: 0; }
      .header-title ha-icon { --mdc-icon-size: 32px; color: var(--primary-color); }
      .header-title h2 {
        margin: 0; font-size: 24px; font-weight: 500;
        color: var(--primary-text-color); overflow-wrap: anywhere;
      }

      .status-badge {
        --badge-color: var(--crt-unknown);
        padding: 6px 16px; border-radius: 16px; font-size: 12px; font-weight: 600;
        letter-spacing: 0.5px; text-transform: uppercase; white-space: nowrap;
        color: var(--primary-text-color);
        border: 1px solid var(--badge-color);
        background: transparent;
        background: color-mix(in srgb, var(--badge-color) 25%, transparent);
      }
      .status-ok { --badge-color: var(--crt-ok); }
      .status-warning { --badge-color: var(--crt-warning); }
      .status-critical { --badge-color: var(--crt-critical); }

      .main-stats {
        display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 16px;
      }
      .stat-item {
        text-align: center; padding: 16px; border-radius: 8px;
        background: var(--secondary-background-color);
      }
      .stat-icon ha-icon { --mdc-icon-size: 32px; color: var(--primary-color); }
      .stat-value {
        font-size: 24px; font-weight: 600; margin: 8px 0 4px 0; color: var(--primary-text-color);
      }
      .stat-label, .monthly-label {
        font-size: 12px; color: var(--secondary-text-color);
        text-transform: uppercase; letter-spacing: 0.5px;
      }

      .section { border-top: 1px solid var(--divider-color, rgba(0, 0, 0, 0.12)); padding-top: 16px; }
      .section h3 {
        font-size: 18px; font-weight: 500; margin: 0 0 16px 0; color: var(--primary-text-color);
      }

      .progress-item { margin-bottom: 20px; }
      .progress-header {
        display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;
      }
      .progress-label {
        display: flex; align-items: center; gap: 8px; font-size: 14px;
        color: var(--primary-text-color);
      }
      .progress-label ha-icon { --mdc-icon-size: 18px; }
      .progress-value { font-size: 14px; font-weight: 600; color: var(--primary-text-color); }

      .progress-bar {
        height: 24px; border-radius: 12px; overflow: hidden; position: relative;
        background: var(--secondary-background-color);
      }
      .progress-fill { height: 100%; width: 0; border-radius: 12px; transition: width 0.3s ease; }
      .progress-fill.ok { background: var(--crt-ok); }
      .progress-fill.warning { background: var(--crt-warning); }
      .progress-fill.critical { background: var(--crt-critical); }
      .progress-fill.neutral { background: var(--crt-neutral); }
      .progress-fill.unknown { background: var(--crt-unknown); }

      .pace-indicator {
        --pace-color: var(--crt-ok);
        display: flex; align-items: center; gap: 8px; padding: 12px; border-radius: 8px;
        font-size: 14px; font-weight: 500; color: var(--primary-text-color);
        background: var(--secondary-background-color);
        background: color-mix(in srgb, var(--pace-color) 12%, transparent);
      }
      .pace-indicator.warning { --pace-color: var(--crt-warning); }
      .pace-indicator ha-icon { --mdc-icon-size: 20px; color: var(--pace-color); }

      .monthly-stats { display: flex; justify-content: space-around; gap: 8px; margin-bottom: 12px; }
      .monthly-item { text-align: center; }
      .monthly-label { display: block; margin-bottom: 4px; }
      .monthly-value {
        display: block; font-size: 18px; font-weight: 600; color: var(--primary-text-color);
      }
      .monthly-progress { height: 16px; margin-bottom: 8px; }
      .monthly-percentage { text-align: center; font-size: 12px; color: var(--secondary-text-color); }

      .projection-stats { display: flex; flex-direction: column; gap: 12px; }
      .projection-item {
        display: flex; justify-content: space-between; align-items: center; gap: 8px;
        padding: 12px; border-radius: 8px; background: var(--secondary-background-color);
      }
      .projection-item.warning {
        border-left: 4px solid var(--crt-warning);
        background: color-mix(in srgb, var(--crt-warning) 12%, transparent);
      }
      .projection-label {
        display: flex; align-items: center; gap: 8px; font-size: 14px;
        color: var(--primary-text-color);
      }
      .projection-label ha-icon { --mdc-icon-size: 20px; }
      .projection-value { font-size: 18px; font-weight: 600; color: var(--primary-text-color); }
      .projection-value.warning { text-decoration: underline var(--crt-warning) 2px; }

      .alerts { display: flex; flex-direction: column; gap: 12px; }
      .alert {
        --alert-color: var(--crt-warning);
        display: flex; align-items: center; gap: 12px; padding: 12px; border-radius: 8px;
        font-size: 14px; font-weight: 500; color: var(--primary-text-color);
        border-left: 4px solid var(--alert-color);
        background: var(--secondary-background-color);
        background: color-mix(in srgb, var(--alert-color) 15%, transparent);
      }
      .alert.critical { --alert-color: var(--crt-critical); }
      .alert ha-icon { --mdc-icon-size: 24px; color: var(--alert-color); }
    `;
  }
}

if (!customElements.get(CARD_TYPE)) {
  customElements.define(CARD_TYPE, CarRentalCard);

  // Register the card with Home Assistant's card picker.
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: CARD_TYPE,
    name: 'Car Rental Tracker Card',
    description: 'A card to display car rental contract tracking and KM management',
    preview: true,
    documentationURL: 'https://github.com/b0t-at/ha-car-rental-tracker#readme',
  });
}
