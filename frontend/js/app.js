/**
 * F1-Dash - Main Application
 */

import { api } from './api/client.js';
import { LapTimesChart } from './charts/lap-times-chart.js';
import { StrategyChart } from './charts/strategy-chart.js';
import { TelemetryChart } from './charts/telemetry-chart.js';
import { TrackMapChart } from './charts/track-map-chart.js';
import { LapTimesTable } from './charts/lap-table.js';
import { RacePaceChart } from './charts/race-pace-chart.js';
import { PositionChart } from './charts/position-chart.js';
import { MultiTelemetryChart } from './charts/multi-telemetry-chart.js';
import { CompoundChart } from './charts/compound-chart.js';
import { PredictionChart } from './charts/prediction-chart.js';
import {
    createOption,
    populateSelect,
    clearElement,
    createDiv,
    createSpan,
    setTextContent,
    escapeHtml,
    sanitizeNumber,
} from './utils/security.js';

class F1DashApp {
    constructor() {
        // State
        this.currentSession = null;
        this.currentYear = 2025;
        this.laps = [];
        this.drivers = [];
        this.charts = {};
        this.lapTable = null;

        // DOM Elements
        this.yearSelect = document.getElementById('year-select');
        this.eventSelect = document.getElementById('event-select');
        this.sessionSelect = document.getElementById('session-select');
        this.loadBtn = document.getElementById('load-btn');
        this.loadingOverlay = document.getElementById('loading-overlay');

        // Initialize
        this.init();
    }

    async init() {
        console.log('Initializing F1-Dash...');

        // Parse URL parameters first
        this.parseUrlParams();

        // Setup event listeners
        this.setupEventListeners();

        // Initialize charts
        this.initCharts();

        // Load initial data
        await this.loadYears();

        // Apply URL state if present
        await this.applyUrlState();
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchSection(link.dataset.section);
            });
        });

        // Session selectors
        this.yearSelect.addEventListener('change', () => this.onYearChange());
        this.eventSelect.addEventListener('change', () => this.onEventChange());
        this.sessionSelect.addEventListener('change', () => this.onSessionChange());
        this.loadBtn.addEventListener('click', () => this.loadSessionData());

        // Chart controls
        document.getElementById('valid-only')?.addEventListener('change', () => {
            this.updateLapTimesChart();
            this.updateLapTable();
        });

        document.getElementById('hide-outliers')?.addEventListener('change', () => {
            this.updateLapTimesChart();
            this.updateLapTable();
        });

        // Compare fastest laps button
        document.getElementById('compare-fastest-btn')?.addEventListener('click', () => {
            this.compareFastestLaps();
        });

        // Telemetry comparison
        document.getElementById('compare-telemetry-btn')?.addEventListener('click', () => {
            this.compareTelemetry();
        });

        // Telemetry driver selection - populate laps
        document.getElementById('telemetry-driver1')?.addEventListener('change', (e) => {
            this.populateLapSelect('telemetry-lap1', e.target.value);
        });
        document.getElementById('telemetry-driver2')?.addEventListener('change', (e) => {
            this.populateLapSelect('telemetry-lap2', e.target.value);
        });

        // Prediction controls
        document.getElementById('load-prediction-btn')?.addEventListener('click', () => {
            this.loadPrediction();
        });

        document.getElementById('show-backtest')?.addEventListener('change', () => {
            this.loadPrediction();
        });

        // Window resize
        window.addEventListener('resize', () => this.handleResize());

        // URL state change (browser back/forward)
        window.addEventListener('popstate', () => {
            this.parseUrlParams();
            this.applyUrlState();
        });
    }

    initCharts() {
        this.charts.lapTimes = new LapTimesChart('#lap-times-chart');
        this.charts.strategy = new StrategyChart('#strategy-chart');
        this.charts.telemetry = new TelemetryChart('#speed-trace-chart');
        this.charts.trackMap = new TrackMapChart('#track-map-chart');
        this.charts.racePace = new RacePaceChart('#race-pace-chart');
        this.charts.position = new PositionChart('#position-chart');
        this.charts.multiTelemetry = new MultiTelemetryChart('#multi-telemetry-chart');
        this.charts.compound = new CompoundChart('#compound-chart');
        this.charts.prediction = new PredictionChart('#prediction-chart');

        // Initialize lap table with callbacks
        this.lapTable = new LapTimesTable('#lap-times-table', {
            onLapClick: (lap) => this.handleLapClick(lap),
            onCompareClick: (laps) => this.handleCompareLaps(laps),
        });

        // Check model status on init
        this.checkModelStatus();
    }

    switchSection(sectionId) {
        // Update nav
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.toggle('active', link.dataset.section === sectionId);
        });

        // Update sections
        document.querySelectorAll('.chart-section').forEach(section => {
            section.classList.toggle('active', section.id === sectionId);
        });

        // Update URL
        this.updateUrl({ section: sectionId });

        // Resize charts for the new section
        setTimeout(() => this.handleResize(), 100);
    }

    showLoading(show = true) {
        this.loadingOverlay.classList.toggle('hidden', !show);
    }

    // Data Loading
    async loadYears() {
        try {
            // Use schedule endpoint for all FastF1 available years
            const data = await api.getScheduleYears();
            const options = data.years.map(year => ({
                value: String(year),
                text: String(year),
            }));
            populateSelect(this.yearSelect, options, 'Select Year');
        } catch (error) {
            console.error('Failed to load years:', error);
            // Default years if API fails
            const currentYear = new Date().getFullYear();
            const options = [];
            for (let year = currentYear; year >= 2018; year--) {
                options.push({ value: String(year), text: String(year) });
            }
            populateSelect(this.yearSelect, options, 'Select Year');
        }
    }

    async onYearChange() {
        const year = this.yearSelect.value;
        this.eventSelect.disabled = !year;
        populateSelect(this.eventSelect, [], 'Select Event');
        this.sessionSelect.disabled = true;
        populateSelect(this.sessionSelect, [], 'Select Session');
        this.loadBtn.disabled = true;
        this.updatePredictionButton();

        if (!year) return;

        try {
            // Use schedule endpoint for all FastF1 available events
            const data = await api.getScheduleEvents(year);
            const options = data.events.map(event => ({
                value: String(event.round_number),
                text: `R${event.round_number} - ${event.event_name}`,
            }));
            populateSelect(this.eventSelect, options, 'Select Event');
        } catch (error) {
            console.error('Failed to load events:', error);
        }
    }

    async onEventChange() {
        const year = this.yearSelect.value;
        const round = this.eventSelect.value;

        this.sessionSelect.disabled = !round;
        populateSelect(this.sessionSelect, [], 'Select Session');
        this.loadBtn.disabled = true;
        this.updatePredictionButton();

        if (!round) return;

        try {
            // Use schedule endpoint for all FastF1 available sessions
            const data = await api.getScheduleSessions(year, round);
            const options = data.sessions.map(session => ({
                value: session.session_type,
                text: session.session_name,
            }));
            populateSelect(this.sessionSelect, options, 'Select Session');
        } catch (error) {
            console.error('Failed to load sessions:', error);
        }
    }

    onSessionChange() {
        this.loadBtn.disabled = !this.sessionSelect.value;
    }

    async loadSessionData() {
        const sessionType = this.sessionSelect.value;
        if (!sessionType) return;

        const year = parseInt(this.yearSelect.value);
        const roundNumber = parseInt(this.eventSelect.value);

        this.showLoading(true);

        // Update all charts with the selected year for proper team colors
        this.updateChartsYear(year);

        try {
            // First, try to ingest the session if not already ingested
            // This will return quickly if already exists
            console.log(`Ingesting session: ${year} R${roundNumber} ${sessionType}`);
            const ingestionResult = await api.ingestSession(year, roundNumber, sessionType, {
                includeTelemetry: false,
                force: false,
            });

            if (!ingestionResult.success) {
                throw new Error(ingestionResult.message || 'Failed to ingest session');
            }

            const sessionId = ingestionResult.session_id;
            console.log(`Session ID: ${sessionId}`);

            // Load session details
            const sessionData = await api.getSession(sessionId);
            this.currentSession = sessionData;

            // Load laps
            const lapsData = await api.getSessionLaps(sessionId, { validOnly: false });
            this.laps = lapsData.laps;

            // Get unique drivers
            this.drivers = [...new Set(this.laps.map(l => l.driver_id))].sort();

            // Update driver filters
            this.updateDriverFilters();

            // Update telemetry driver selects
            this.updateTelemetryDriverSelects();

            // Enable compare fastest button
            const compareFastestBtn = document.getElementById('compare-fastest-btn');
            if (compareFastestBtn) {
                compareFastestBtn.disabled = false;
            }

            // Update URL with session info
            this.updateUrl({
                year: year,
                round: roundNumber,
                sessionType: sessionType,
            });

            // Update all charts
            await this.updateAllCharts();

            console.log(`Loaded ${this.laps.length} laps for ${this.drivers.length} drivers`);
        } catch (error) {
            console.error('Failed to load session data:', error);
            alert(`Failed to load session data: ${error.message}`);
        } finally {
            this.showLoading(false);
        }
    }

    updateDriverFilters() {
        const container = document.getElementById('driver-checkboxes');
        if (!container) return;

        clearElement(container);

        this.drivers.forEach(driver => {
            const label = document.createElement('label');
            label.className = 'driver-checkbox';

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.value = driver;
            checkbox.checked = true;

            const span = document.createElement('span');
            span.textContent = driver;

            label.appendChild(checkbox);
            label.appendChild(span);

            checkbox.addEventListener('change', () => {
                this.updateLapTimesChart();
                this.updateLapTable();
            });

            container.appendChild(label);
        });
    }

    updateTelemetryDriverSelects() {
        const selects = ['telemetry-driver1', 'telemetry-driver2'];
        const options = this.drivers.map(driver => ({
            value: driver,
            text: driver,
        }));

        selects.forEach(selectId => {
            const select = document.getElementById(selectId);
            if (!select) return;

            populateSelect(select, options, 'Select Driver');
        });
    }

    populateLapSelect(selectId, driverId) {
        const select = document.getElementById(selectId);
        if (!select) return;

        if (!driverId) {
            populateSelect(select, [], 'Fastest');
            return;
        }

        const driverLaps = this.laps
            .filter(l => l.driver_id === driverId && l.lap_time_seconds != null)
            .sort((a, b) => a.lap_number - b.lap_number);

        const options = driverLaps.map(lap => ({
            value: String(lap.lap_number),
            text: `Lap ${lap.lap_number}`,
        }));
        populateSelect(select, options, 'Fastest');
    }

    getSelectedDrivers() {
        const checkboxes = document.querySelectorAll('#driver-checkboxes input:checked');
        return Array.from(checkboxes).map(cb => cb.value);
    }

    /**
     * Filter outliers using IQR method.
     * Outliers are lap times outside 1.5 * IQR from Q1/Q3.
     */
    filterOutliers(laps) {
        if (!laps.length) return laps;

        // Get all valid lap times
        const times = laps
            .filter(l => l.lap_time_seconds != null)
            .map(l => l.lap_time_seconds)
            .sort((a, b) => a - b);

        if (times.length < 4) return laps;

        // Calculate Q1, Q3, and IQR
        const q1Index = Math.floor(times.length * 0.25);
        const q3Index = Math.floor(times.length * 0.75);
        const q1 = times[q1Index];
        const q3 = times[q3Index];
        const iqr = q3 - q1;

        // Define bounds (1.5 * IQR is standard)
        const lowerBound = q1 - 1.5 * iqr;
        const upperBound = q3 + 1.5 * iqr;

        // Filter laps within bounds
        return laps.filter(l => {
            if (l.lap_time_seconds == null) return false;
            return l.lap_time_seconds >= lowerBound && l.lap_time_seconds <= upperBound;
        });
    }

    async updateAllCharts() {
        await Promise.all([
            this.updateLapTimesChart(),
            this.updateLapTable(),
            this.updateStrategyChart(),
            this.updateCompoundChart(),
            this.updateRacePaceChart(),
            this.updatePositionChart(),
        ]);
    }

    updateLapTimesChart() {
        if (!this.laps.length) return;

        const validOnly = document.getElementById('valid-only')?.checked ?? true;
        const hideOutliers = document.getElementById('hide-outliers')?.checked ?? true;
        const selectedDrivers = this.getSelectedDrivers();

        let filteredLaps = this.laps;

        if (validOnly) {
            filteredLaps = filteredLaps.filter(l => l.is_valid_for_analysis);
        }

        if (selectedDrivers.length > 0 && selectedDrivers.length < this.drivers.length) {
            filteredLaps = filteredLaps.filter(l => selectedDrivers.includes(l.driver_id));
        }

        if (hideOutliers) {
            filteredLaps = this.filterOutliers(filteredLaps);
        }

        this.charts.lapTimes.update(filteredLaps);
    }

    updateLapTable() {
        if (!this.laps.length || !this.lapTable) return;

        const validOnly = document.getElementById('valid-only')?.checked ?? true;
        const hideOutliers = document.getElementById('hide-outliers')?.checked ?? true;
        const selectedDrivers = this.getSelectedDrivers();

        let filteredLaps = this.laps;

        if (validOnly) {
            filteredLaps = filteredLaps.filter(l => l.is_valid_for_analysis);
        }

        if (selectedDrivers.length > 0 && selectedDrivers.length < this.drivers.length) {
            filteredLaps = filteredLaps.filter(l => selectedDrivers.includes(l.driver_id));
        }

        if (hideOutliers) {
            filteredLaps = this.filterOutliers(filteredLaps);
        }

        this.lapTable.update(filteredLaps, this.drivers);
    }

    async updateStrategyChart() {
        if (!this.currentSession) return;

        try {
            const data = await api.getStrategySummary(this.currentSession.id);
            this.charts.strategy.update(data);
        } catch (error) {
            console.error('Failed to load strategy data:', error);
        }
    }

    async updateCompoundChart() {
        if (!this.currentSession) return;

        try {
            const data = await api.getCompoundPerformance(this.currentSession.id);
            this.charts.compound.update(data);
        } catch (error) {
            console.error('Failed to load compound performance data:', error);
        }
    }

    async updateRacePaceChart() {
        if (!this.laps.length) return;

        // Build distribution data
        const distribution = {};
        this.laps
            .filter(l => l.is_valid_for_analysis && l.lap_time_seconds != null)
            .forEach(lap => {
                if (!distribution[lap.driver_id]) {
                    distribution[lap.driver_id] = [];
                }
                distribution[lap.driver_id].push(lap.lap_time_seconds);
            });

        this.charts.racePace.update({ drivers: distribution });
    }

    async updatePositionChart() {
        if (!this.laps.length) return;

        // Build position data
        const positions = {};
        this.laps
            .filter(l => l.position != null)
            .forEach(lap => {
                if (!positions[lap.driver_id]) {
                    positions[lap.driver_id] = [];
                }
                positions[lap.driver_id].push({
                    lap: lap.lap_number,
                    position: lap.position,
                });
            });

        this.charts.position.update({ positions });
    }

    handleResize() {
        Object.values(this.charts).forEach(chart => {
            if (chart._lastData) {
                chart.resize();
            }
        });
    }

    updateChartsYear(year) {
        this.currentYear = year;
        // Update year on all charts that support it
        Object.values(this.charts).forEach(chart => {
            if (typeof chart.setYear === 'function') {
                chart.setYear(year);
            }
        });
    }

    // Lap click handler - navigate to telemetry
    handleLapClick(lap) {
        // Switch to telemetry section
        this.switchSection('telemetry');

        // Set driver 1 to clicked lap
        const driver1Select = document.getElementById('telemetry-driver1');
        if (driver1Select) {
            driver1Select.value = lap.driver_id;
            this.populateLapSelect('telemetry-lap1', lap.driver_id);

            const lap1Select = document.getElementById('telemetry-lap1');
            if (lap1Select) {
                lap1Select.value = lap.lap_number;
            }
        }

        // Automatically load this lap's telemetry
        this.loadSingleLapTelemetry(lap);
    }

    async loadSingleLapTelemetry(lap) {
        if (!this.currentSession) return;

        this.showLoading(true);

        try {
            const data = await api.getLapTelemetry(
                this.currentSession.id,
                lap.driver_id,
                lap.lap_number
            );

            const telemetryData = {
                laps: [{
                    driver_id: lap.driver_id,
                    lap_number: lap.lap_number,
                    telemetry: data.points,
                }]
            };

            this.charts.telemetry.update(telemetryData);
            this.charts.multiTelemetry.update(telemetryData);
            this.charts.trackMap.update(telemetryData);
        } catch (error) {
            console.error('Failed to load telemetry:', error);
        } finally {
            this.showLoading(false);
        }
    }

    // Compare laps from table selection
    async handleCompareLaps(laps) {
        if (!this.currentSession || laps.length < 2) return;

        this.switchSection('telemetry');
        await this.loadTelemetryComparison(laps.slice(0, 4)); // Max 4 laps
    }

    // Compare fastest laps button handler
    async compareFastestLaps() {
        if (!this.currentSession) return;

        const selectedDrivers = this.getSelectedDrivers();
        if (selectedDrivers.length < 2) {
            alert('Please select at least 2 drivers to compare');
            return;
        }

        // Get fastest lap for each selected driver
        const fastestLaps = [];
        selectedDrivers.slice(0, 4).forEach(driverId => {
            const driverLaps = this.laps
                .filter(l => l.driver_id === driverId && l.lap_time_seconds != null)
                .sort((a, b) => a.lap_time_seconds - b.lap_time_seconds);

            if (driverLaps.length > 0) {
                fastestLaps.push(driverLaps[0]);
            }
        });

        if (fastestLaps.length >= 2) {
            this.switchSection('telemetry');
            await this.loadTelemetryComparison(fastestLaps);
        }
    }

    // Compare telemetry button handler
    async compareTelemetry() {
        if (!this.currentSession) return;

        const driver1 = document.getElementById('telemetry-driver1')?.value;
        const driver2 = document.getElementById('telemetry-driver2')?.value;
        const lap1 = document.getElementById('telemetry-lap1')?.value;
        const lap2 = document.getElementById('telemetry-lap2')?.value;

        if (!driver1) {
            alert('Please select at least one driver');
            return;
        }

        const comparisons = [];

        // Add first driver's lap
        if (lap1) {
            comparisons.push({ driver_id: driver1, lap_number: parseInt(lap1) });
        } else {
            // Find fastest lap
            const fastest = this.laps
                .filter(l => l.driver_id === driver1 && l.lap_time_seconds != null)
                .sort((a, b) => a.lap_time_seconds - b.lap_time_seconds)[0];
            if (fastest) {
                comparisons.push({ driver_id: driver1, lap_number: fastest.lap_number });
            }
        }

        // Add second driver's lap if selected
        if (driver2) {
            if (lap2) {
                comparisons.push({ driver_id: driver2, lap_number: parseInt(lap2) });
            } else {
                const fastest = this.laps
                    .filter(l => l.driver_id === driver2 && l.lap_time_seconds != null)
                    .sort((a, b) => a.lap_time_seconds - b.lap_time_seconds)[0];
                if (fastest) {
                    comparisons.push({ driver_id: driver2, lap_number: fastest.lap_number });
                }
            }
        }

        if (comparisons.length > 0) {
            const laps = comparisons.map(c =>
                this.laps.find(l => l.driver_id === c.driver_id && l.lap_number === c.lap_number)
            ).filter(Boolean);

            await this.loadTelemetryComparison(laps);
        }
    }

    async loadTelemetryComparison(laps) {
        if (!this.currentSession || laps.length === 0) return;

        this.showLoading(true);

        try {
            const comparisons = laps.map(lap => ({
                driver_id: lap.driver_id,
                lap_number: lap.lap_number,
            }));

            const data = await api.compareTelemetry(this.currentSession.id, comparisons);

            const telemetryData = {
                laps: data.laps.map(lap => ({
                    driver_id: lap.driver_id,
                    lap_number: lap.lap_number,
                    telemetry: lap.telemetry,
                }))
            };

            this.charts.telemetry.update(telemetryData);
            this.charts.multiTelemetry.update(telemetryData);
            this.charts.trackMap.update(telemetryData);

            // Update URL with comparison
            this.updateUrl({
                compare: laps.map(l => `${l.driver_id}-${l.lap_number}`).join(','),
            });
        } catch (error) {
            console.error('Failed to load telemetry comparison:', error);
            alert('Failed to load telemetry. Make sure telemetry data was ingested for this session.');
        } finally {
            this.showLoading(false);
        }
    }

    // URL State Management
    parseUrlParams() {
        const params = new URLSearchParams(window.location.search);
        this.urlState = {
            year: params.get('year'),
            round: params.get('round'),
            sessionType: params.get('sessionType'),
            section: params.get('section') || 'lap-times',
            compare: params.get('compare'),
        };
    }

    async applyUrlState() {
        if (!this.urlState) return;

        // Apply section
        if (this.urlState.section) {
            this.switchSection(this.urlState.section);
        }

        // Apply session selection
        if (this.urlState.year) {
            this.yearSelect.value = this.urlState.year;
            await this.onYearChange();

            if (this.urlState.round) {
                this.eventSelect.value = this.urlState.round;
                await this.onEventChange();

                if (this.urlState.sessionType) {
                    this.sessionSelect.value = this.urlState.sessionType;
                    this.onSessionChange();
                    await this.loadSessionData();

                    // Apply telemetry comparison if specified
                    if (this.urlState.compare) {
                        const comparisons = this.urlState.compare.split(',').map(c => {
                            const [driver, lap] = c.split('-');
                            return this.laps.find(l =>
                                l.driver_id === driver && l.lap_number === parseInt(lap)
                            );
                        }).filter(Boolean);

                        if (comparisons.length > 0) {
                            await this.loadTelemetryComparison(comparisons);
                        }
                    }
                }
            }
        }
    }

    updateUrl(params) {
        const url = new URL(window.location);

        Object.entries(params).forEach(([key, value]) => {
            if (value) {
                url.searchParams.set(key, value);
            } else {
                url.searchParams.delete(key);
            }
        });

        window.history.pushState({}, '', url);
    }

    // Get shareable URL
    getShareableUrl() {
        return window.location.href;
    }

    copyShareableUrl() {
        const url = this.getShareableUrl();
        navigator.clipboard.writeText(url).then(() => {
            this.showNotification('URL copied to clipboard!');
        }).catch(err => {
            console.error('Failed to copy URL:', err);
        });
    }

    showNotification(message) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = 'url-notification';

        const span = document.createElement('span');
        span.textContent = message;

        const closeBtn = document.createElement('button');
        closeBtn.textContent = '×';
        closeBtn.addEventListener('click', () => notification.remove());

        notification.appendChild(span);
        notification.appendChild(closeBtn);
        document.body.appendChild(notification);

        // Auto-remove after 3 seconds
        setTimeout(() => notification.remove(), 3000);
    }

    // Prediction methods
    async checkModelStatus() {
        const statusEl = document.getElementById('model-status');
        if (!statusEl) return;

        try {
            const info = await api.getModelInfo();
            const indicator = statusEl.querySelector('.status-indicator');
            const text = statusEl.querySelector('.status-text');

            if (info.status === 'trained') {
                indicator.style.backgroundColor = '#4ade80';
                text.textContent = `Model ready (${info.feature_count} features)`;
                this.modelReady = true;
            } else {
                indicator.style.backgroundColor = '#f87171';
                text.textContent = 'Model not trained';
                this.modelReady = false;
            }
        } catch (error) {
            console.error('Failed to check model status:', error);
            const text = statusEl.querySelector('.status-text');
            text.textContent = 'Error checking model';
        }

        this.updatePredictionButton();
    }

    updatePredictionButton() {
        const btn = document.getElementById('load-prediction-btn');
        if (!btn) return;

        const year = this.yearSelect.value;
        const round = this.eventSelect.value;

        btn.disabled = !this.modelReady || !year || !round;
    }

    async loadPrediction() {
        const year = this.yearSelect.value;
        const round = this.eventSelect.value;

        if (!year || !round) {
            alert('Please select a year and event first');
            return;
        }

        this.showLoading(true);

        try {
            const showBacktest = document.getElementById('show-backtest')?.checked ?? true;

            let data;
            if (showBacktest) {
                // Load backtest (includes actual results)
                const backtest = await api.getBacktest(year, round);
                data = {
                    predictions: backtest.predictions,
                    metrics: backtest.metrics
                };
            } else {
                // Load just predictions
                const predictions = await api.getPrediction(year, round);
                data = { predictions };
            }

            this.charts.prediction.update(data);
            this.updatePredictionTable(data);
        } catch (error) {
            console.error('Failed to load prediction:', error);
            alert(`Failed to load prediction: ${error.message}`);
        } finally {
            this.showLoading(false);
        }
    }

    updatePredictionTable(data) {
        const container = document.getElementById('prediction-table');
        if (!container || !data.predictions) return;

        clearElement(container);

        const hasActual = data.predictions.some(p => p.actual_position != null);

        // Create table
        const table = document.createElement('table');
        table.className = 'data-table';

        // Create header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        const headers = ['Rank', 'Driver', 'Predicted'];
        if (hasActual) {
            headers.push('Actual', 'Error');
        }
        headers.push('FP1', 'FP2', 'FP3');

        headers.forEach(headerText => {
            const th = document.createElement('th');
            th.textContent = headerText;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);

        // Create body
        const tbody = document.createElement('tbody');
        data.predictions.forEach(pred => {
            const row = document.createElement('tr');

            // Rank
            const rankCell = document.createElement('td');
            rankCell.textContent = String(pred.rank);
            row.appendChild(rankCell);

            // Driver (bold)
            const driverCell = document.createElement('td');
            const strong = document.createElement('strong');
            strong.textContent = pred.driver;
            driverCell.appendChild(strong);
            row.appendChild(driverCell);

            // Predicted
            const predictedCell = document.createElement('td');
            predictedCell.textContent = pred.predicted_position.toFixed(1);
            row.appendChild(predictedCell);

            // Actual and Error (if available)
            if (hasActual) {
                const actualCell = document.createElement('td');
                actualCell.textContent = pred.actual_position ?? '-';
                row.appendChild(actualCell);

                const errorCell = document.createElement('td');
                if (pred.position_error != null) {
                    errorCell.className = pred.position_error === 0 ? 'exact' :
                        pred.position_error <= 3 ? 'close' : 'far';
                }
                errorCell.textContent = pred.position_error ?? '-';
                row.appendChild(errorCell);
            }

            // FP1, FP2, FP3
            ['fp1_position', 'fp2_position', 'fp3_position'].forEach(key => {
                const cell = document.createElement('td');
                cell.textContent = pred[key] ? `P${pred[key]}` : '-';
                row.appendChild(cell);
            });

            tbody.appendChild(row);
        });
        table.appendChild(tbody);
        container.appendChild(table);

        // Add metrics if available
        if (data.metrics) {
            const metricsBox = document.createElement('div');
            metricsBox.className = 'metrics-summary-box';

            const title = document.createElement('h4');
            title.textContent = 'Model Performance';
            metricsBox.appendChild(title);

            const metricsGrid = document.createElement('div');
            metricsGrid.className = 'metrics-grid';

            const metricsData = [
                { label: 'MAE', value: `${data.metrics.mae.toFixed(2)} pos` },
                { label: 'Within 1 pos', value: `${data.metrics.within_1_position.toFixed(0)}%` },
                { label: 'Within 3 pos', value: `${data.metrics.within_3_positions.toFixed(0)}%` },
                { label: 'Podium correct', value: `${data.metrics.podium_correct}/3` },
                { label: 'Winner correct', value: data.metrics.winner_correct ? 'Yes' : 'No', className: data.metrics.winner_correct ? 'success' : 'fail' },
            ];

            metricsData.forEach(metric => {
                const metricDiv = document.createElement('div');
                metricDiv.className = 'metric';

                const labelSpan = document.createElement('span');
                labelSpan.className = 'metric-label';
                labelSpan.textContent = metric.label;
                metricDiv.appendChild(labelSpan);

                const valueSpan = document.createElement('span');
                valueSpan.className = 'metric-value' + (metric.className ? ` ${metric.className}` : '');
                valueSpan.textContent = metric.value;
                metricDiv.appendChild(valueSpan);

                metricsGrid.appendChild(metricDiv);
            });

            metricsBox.appendChild(metricsGrid);
            container.appendChild(metricsBox);
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.f1App = new F1DashApp();
});
