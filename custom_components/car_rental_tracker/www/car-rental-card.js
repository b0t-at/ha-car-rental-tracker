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

// ---------------------------------------------------------------------------
// Localisation
// ---------------------------------------------------------------------------

const DEFAULT_LANGUAGE = 'en';

// Placeholders use {name}; values are filled in by translate().
const TRANSLATIONS = {
  en: {
    card_name: 'Car Rental Tracker Card',
    card_description: 'A card to display car rental contract tracking and KM management',
    default_title: 'Car Rental Tracker',
    stat_odometer: 'Current Odometer',
    stat_total_driven: 'Total Driven',
    stat_km_remaining: 'KM Remaining',
    stat_days_remaining: 'Days Left',
    section_progress: 'Progress Overview',
    progress_time: 'Time Elapsed',
    progress_km: 'KM Usage',
    pace_on_track: 'On Pace',
    pace_ahead: '{percent} Ahead - Slow Down!',
    pace_behind: '{percent} Behind - You Can Drive More',
    section_month: 'This Month',
    monthly_driven: 'Driven',
    monthly_remaining: 'Remaining',
    monthly_allowance: 'Allowance',
    monthly_bar_label: 'Monthly allowance used',
    monthly_used: '{percent} of monthly allowance used',
    section_projections: 'Projections',
    projection_km: 'Projected KM at End',
    projection_overage: 'Projected Overage',
    projection_cost: 'Estimated Cost',
    alert_critical: 'CRITICAL: You have exceeded your KM allowance!',
    alert_overage: 'WARNING: You are projected to exceed your allowance by {distance}',
    alert_pace: 'You are driving faster than your contract pace. Consider slowing down.',
    status_ok: 'OK',
    status_warning: 'Warning',
    status_critical: 'Critical',
    unavailable: 'Unavailable',
    percent: '{value}%',
    error_entity_not_found: 'Entity not found: {entity}',
    error_sensors_missing:
      'Related Car Rental Tracker sensors not found. Please check the configured entity.',
    error_entity_required:
      "Please set 'entity' to a sensor of your Car Rental Tracker device " +
      '(for example its Status sensor, sensor.car_rental_tracker_<start_date>_status)',
    error_title_type: "'title' must be a string",
  },
  de: {
    card_name: 'Car-Rental-Tracker-Karte',
    card_description: 'Eine Karte zur Anzeige deines Mietwagenvertrags und zur Verwaltung der Kilometer',
    default_title: 'Car Rental Tracker',
    stat_odometer: 'Kilometer­stand',
    stat_total_driven: 'Insgesamt gefahren',
    stat_km_remaining: 'Verbleibende km',
    stat_days_remaining: 'Verbleibende Tage',
    section_progress: 'Fortschrittsübersicht',
    progress_time: 'Vergangene Zeit',
    progress_km: 'Genutzte Kilometer',
    pace_on_track: 'Im Plan',
    pace_ahead: '{percent} über dem Plan – fahr langsamer!',
    pace_behind: '{percent} unter dem Plan – du kannst mehr fahren',
    section_month: 'Dieser Monat',
    monthly_driven: 'Gefahren',
    monthly_remaining: 'Verbleibend',
    monthly_allowance: 'Kontingent',
    monthly_bar_label: 'Genutztes Monatskontingent',
    monthly_used: '{percent} des Monatskontingents genutzt',
    section_projections: 'Prognosen',
    projection_km: 'Prognostizierte km bei Vertragsende',
    projection_overage: 'Prognostizierte Mehrkilometer',
    projection_cost: 'Geschätzte Kosten',
    alert_critical: 'KRITISCH: Du hast dein Kilometerkontingent überschritten!',
    alert_overage: 'WARNUNG: Laut Prognose überschreitest du dein Kontingent um {distance}',
    alert_pace: 'Du fährst mehr, als dein Vertrag vorsieht. Fahr am besten etwas weniger.',
    status_ok: 'OK',
    status_warning: 'Warnung',
    status_critical: 'Kritisch',
    unavailable: 'Nicht verfügbar',
    percent: '{value} %',
    error_entity_not_found: 'Entität nicht gefunden: {entity}',
    error_sensors_missing:
      'Zugehörige Car-Rental-Tracker-Sensoren nicht gefunden. Bitte überprüfe die konfigurierte Entität.',
    error_entity_required:
      "Bitte setze 'entity' auf einen Sensor deines Car-Rental-Tracker-Geräts " +
      '(zum Beispiel dessen Status-Sensor, sensor.car_rental_tracker_<start_date>_status)',
    error_title_type: "'title' muss eine Zeichenkette sein",
  },
};

// 'de-AT' / 'de_AT' -> 'de'; anything without a dictionary -> DEFAULT_LANGUAGE.
const toSupportedLanguage = (tag) => {
  const base = typeof tag === 'string' ? tag.split(/[-_]/)[0].toLowerCase() : '';
  return Object.prototype.hasOwnProperty.call(TRANSLATIONS, base) ? base : DEFAULT_LANGUAGE;
};

// Language of the HA frontend; before hass exists, fall back to the page/browser.
const resolveLanguage = (hass) => {
  const fromHass = hass && ((hass.locale && hass.locale.language) || hass.language);
  if (fromHass) {
    return toSupportedLanguage(fromHass);
  }
  const doc = typeof document !== 'undefined' && document.documentElement;
  const nav = typeof navigator !== 'undefined' && navigator.language;
  return toSupportedLanguage((doc && doc.lang) || nav || DEFAULT_LANGUAGE);
};

const translate = (language, key, params = {}) => {
  const dict = TRANSLATIONS[language] || TRANSLATIONS[DEFAULT_LANGUAGE];
  const template = dict[key] !== undefined ? dict[key] : TRANSLATIONS[DEFAULT_LANGUAGE][key];
  if (template === undefined) {
    return key;
  }
  return template.replace(/\{(\w+)\}/g, (match, name) =>
    Object.prototype.hasOwnProperty.call(params, name) ? String(params[name]) : match
  );
};

const HTML_ESCAPES = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
const escapeHtml = (text) => String(text).replace(/[&<>"']/g, (c) => HTML_ESCAPES[c]);

// ---------------------------------------------------------------------------
// Markup
// ---------------------------------------------------------------------------

const progressItem = (ref, icon, label) => `
  <div class="progress-item">
    <div class="progress-header">
      <span class="progress-label">
        <ha-icon icon="${icon}"></ha-icon>
        ${escapeHtml(label)}
      </span>
      <span class="progress-value" data-ref="${ref}Value"></span>
    </div>
    <div class="progress-bar" data-ref="${ref}Bar" role="progressbar"
         aria-label="${escapeHtml(label)}" aria-valuemin="0" aria-valuemax="100">
      <div class="progress-fill" data-ref="${ref}Fill"></div>
    </div>
  </div>
`;

const statItem = (ref, icon, label) => `
  <div class="stat-item">
    <div class="stat-icon"><ha-icon icon="${icon}"></ha-icon></div>
    <div class="stat-value" data-ref="${ref}"></div>
    <div class="stat-label">${escapeHtml(label)}</div>
  </div>
`;

const monthlyItem = (ref, label) => `
  <div class="monthly-item">
    <span class="monthly-label">${escapeHtml(label)}</span>
    <span class="monthly-value" data-ref="${ref}"></span>
  </div>
`;

const projectionItem = (ref, icon, label) => `
  <div class="projection-item" data-ref="${ref}Row">
    <div class="projection-label">
      <ha-icon icon="${icon}"></ha-icon>
      ${escapeHtml(label)}
    </div>
    <div class="projection-value" data-ref="${ref}"></div>
  </div>
`;

// Static, translated markup only: every dynamic value is set later via
// textContent/attributes. Rebuilt whenever the UI language changes.
const cardTemplate = (t) => `
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
        ${statItem('odometer', 'mdi:counter', t('stat_odometer'))}
        ${statItem('totalDriven', 'mdi:map-marker-distance', t('stat_total_driven'))}
        ${statItem('kmRemaining', 'mdi:gauge', t('stat_km_remaining'))}
        ${statItem('daysRemaining', 'mdi:calendar-clock', t('stat_days_remaining'))}
      </div>

      <section class="section">
        <h3>${escapeHtml(t('section_progress'))}</h3>
        ${progressItem('time', 'mdi:clock-outline', t('progress_time'))}
        ${progressItem('km', 'mdi:speedometer', t('progress_km'))}
        <div class="pace-indicator" data-ref="pace">
          <ha-icon data-ref="paceIcon"></ha-icon>
          <span data-ref="paceText"></span>
        </div>
      </section>

      <section class="section">
        <h3>${escapeHtml(t('section_month'))}</h3>
        <div class="monthly-stats">
          ${monthlyItem('monthlyDriven', t('monthly_driven'))}
          ${monthlyItem('monthlyRemaining', t('monthly_remaining'))}
          ${monthlyItem('monthlyAllowance', t('monthly_allowance'))}
        </div>
        <div class="progress-bar monthly-progress" data-ref="monthlyBar" role="progressbar"
             aria-label="${escapeHtml(t('monthly_bar_label'))}" aria-valuemin="0" aria-valuemax="100">
          <div class="progress-fill" data-ref="monthlyFill"></div>
        </div>
        <div class="monthly-percentage" data-ref="monthlyValue"></div>
      </section>

      <section class="section">
        <h3>${escapeHtml(t('section_projections'))}</h3>
        <div class="projection-stats">
          ${projectionItem('projected', 'mdi:chart-line', t('projection_km'))}
          ${projectionItem('overage', 'mdi:alert-circle', t('projection_overage'))}
          ${projectionItem('cost', 'mdi:cash', t('projection_cost'))}
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
    this._lang = null;
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
      throw new Error(this._t('error_entity_required'));
    }
    if (config.title !== undefined && typeof config.title !== 'string') {
      throw new Error(this._t('error_title_type'));
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
    if (
      previous.locale !== hass.locale ||
      previous.language !== hass.language ||
      previous.config !== hass.config
    ) {
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

  // Translate with the current HA language (browser language before hass is set).
  _t(key, params) {
    return translate(resolveLanguage(this._hass), key, params);
  }

  _formatPercent(value) {
    return this._t('percent', { value: this._formatNumber(value, 1) });
  }

  _syncLanguage() {
    const lang = resolveLanguage(this._hass);
    if (lang === this._lang) {
      return;
    }
    // Labels live in the static markup, so a language change rebuilds it.
    this._lang = lang;
    this._refs = null;
    this._alertsSignature = null;
  }

  _ensureDom() {
    if (this._refs) {
      return;
    }
    const template = cardTemplate((key, params) => this._t(key, params));
    this.shadowRoot.innerHTML = `<style>${CarRentalCard._styles()}</style>${template}`;
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
      return this._t('error_entity_not_found', { entity: entityId });
    }
    if (!sensors.total_driven) {
      return this._t('error_sensors_missing');
    }
    return null;
  }

  _render() {
    this._syncLanguage();
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

    this._refs.title.textContent = this._config.title || this._t('default_title');
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
    } else if (STATUS_CLASSES.includes(stateObj.state)) {
      badge.textContent = this._t(`status_${stateObj.state}`);
    } else {
      badge.textContent = UNAVAILABLE_STATES.includes(stateObj.state)
        ? this._t('unavailable')
        : stateObj.state;
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
      [text, cls, icon] = [this._t('pace_on_track'), 'ok', 'mdi:check-circle'];
    } else if (difference > 0) {
      text = this._t('pace_ahead', { percent: this._formatPercent(difference) });
      [cls, icon] = ['warning', 'mdi:alert-circle'];
    } else {
      text = this._t('pace_behind', { percent: this._formatPercent(-difference) });
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
      : this._t('monthly_used', { percent: this._formatPercent(progress) });
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
        message: this._t('alert_critical'),
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
        message: this._t('alert_overage', {
          distance: this._formatDistance(s.projected_overage),
        }),
      });
    }
    if (kmProgress !== null && timeProgress !== null && kmProgress > timeProgress + PACE_WARNING_PCT) {
      alerts.push({
        cls: 'warning',
        icon: 'mdi:speedometer-slow',
        message: this._t('alert_pace'),
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
      bar.setAttribute('aria-valuetext', this._t('unavailable'));
    } else {
      bar.setAttribute('aria-valuenow', String(Math.round(clamped)));
      bar.setAttribute('aria-valuetext', this._formatPercent(value));
    }
    const label = this._refs[`${ref}Value`];
    if (label && ref !== 'monthly') {
      label.textContent = value === null ? DASH : this._formatPercent(value);
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
    // Registered before any hass object exists, so the HA page language
    // (<html lang>, set by the frontend) or the browser language is used.
    name: translate(resolveLanguage(null), 'card_name'),
    description: translate(resolveLanguage(null), 'card_description'),
    preview: true,
    documentationURL: 'https://github.com/b0t-at/ha-car-rental-tracker#readme',
  });
}
