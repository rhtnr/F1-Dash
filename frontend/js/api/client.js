/**
 * F1 Plots API Client
 * Handles all communication with the FastAPI backend
 */

const API_BASE_URL = 'http://localhost:8000/api/v1';

class F1ApiClient {
    constructor(baseUrl = API_BASE_URL) {
        this.baseUrl = baseUrl;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        };

        try {
            const response = await fetch(url, config);
            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.detail || `HTTP ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`API Error: ${endpoint}`, error);
            throw error;
        }
    }

    // Schedule (FastF1 available data)
    async getScheduleYears() {
        return this.request('/schedule/years');
    }

    async getScheduleEvents(year) {
        return this.request(`/schedule/events/${year}`);
    }

    async getScheduleSessions(year, roundNumber) {
        return this.request(`/schedule/sessions/${year}/${roundNumber}`);
    }

    // Sessions (ingested data)
    async getYears() {
        return this.request('/sessions/years');
    }

    async getEvents(year) {
        return this.request(`/sessions/events/${year}`);
    }

    async getEventSessions(year, roundNumber) {
        return this.request(`/sessions/${year}/${roundNumber}`);
    }

    async getSession(sessionId) {
        return this.request(`/sessions/id/${sessionId}`);
    }

    async getSessions(year = null, limit = 50) {
        const params = new URLSearchParams();
        if (year) params.append('year', year);
        params.append('limit', limit);
        return this.request(`/sessions?${params}`);
    }

    // Laps
    async getSessionLaps(sessionId, options = {}) {
        const params = new URLSearchParams();
        if (options.driverId) params.append('driver_id', options.driverId);
        if (options.compound) params.append('compound', options.compound);
        if (options.validOnly) params.append('valid_only', 'true');
        return this.request(`/laps/${sessionId}?${params}`);
    }

    async getFastestLaps(sessionId, topN = 10) {
        return this.request(`/laps/${sessionId}/fastest?top_n=${topN}`);
    }

    async getPersonalBests(sessionId) {
        return this.request(`/laps/${sessionId}/personal-bests`);
    }

    async getLapDistribution(sessionId) {
        return this.request(`/laps/${sessionId}/distribution`);
    }

    async getCompoundPerformance(sessionId) {
        return this.request(`/laps/${sessionId}/compound-performance`);
    }

    async compareDrivers(sessionId, driver1, driver2) {
        return this.request(
            `/laps/${sessionId}/compare?driver1=${driver1}&driver2=${driver2}`
        );
    }

    // Strategy
    async getSessionStints(sessionId, driverId = null) {
        const params = driverId ? `?driver_id=${driverId}` : '';
        return this.request(`/strategy/${sessionId}/stints${params}`);
    }

    async getStrategySummary(sessionId) {
        return this.request(`/strategy/${sessionId}/summary`);
    }

    async getCompoundAnalysis(sessionId) {
        return this.request(`/strategy/${sessionId}/compound-analysis`);
    }

    async getStintDegradation(sessionId, driverId, stintNumber) {
        return this.request(
            `/strategy/${sessionId}/degradation/${driverId}/${stintNumber}`
        );
    }

    // Telemetry
    async getLapTelemetry(sessionId, driverId, lapNumber) {
        return this.request(
            `/telemetry/${sessionId}/${driverId}/${lapNumber}`
        );
    }

    async getAvailableTelemetry(sessionId, driverId) {
        return this.request(
            `/telemetry/${sessionId}/${driverId}/available`
        );
    }

    async getSpeedTrace(sessionId, driverId, lapNumber) {
        return this.request(
            `/telemetry/${sessionId}/${driverId}/${lapNumber}/speed-trace`
        );
    }

    async compareTelemetry(sessionId, comparisons) {
        return this.request(`/telemetry/${sessionId}/compare`, {
            method: 'POST',
            body: JSON.stringify(comparisons),
        });
    }

    // Ingestion
    async ingestSession(year, roundNumber, sessionType, options = {}) {
        return this.request('/ingest/session', {
            method: 'POST',
            body: JSON.stringify({
                year,
                round_number: roundNumber,
                session_type: sessionType,
                include_telemetry: options.includeTelemetry || false,
                force: options.force || false,
            }),
        });
    }

    async checkIngestionStatus(year, roundNumber, sessionType) {
        return this.request(
            `/ingest/status/${year}/${roundNumber}/${sessionType}`
        );
    }

    // Predictions
    async getPrediction(year, event) {
        return this.request(`/predictions/race/${year}/${event}`);
    }

    async getBacktest(year, event) {
        return this.request(`/predictions/backtest/${year}/${event}`);
    }

    async getModelInfo() {
        return this.request('/predictions/model/info');
    }

    async trainModel(startYear = 2022, endYear = 2024) {
        return this.request(
            `/predictions/train?start_year=${startYear}&end_year=${endYear}`,
            { method: 'POST' }
        );
    }
}

// Export singleton instance
export const api = new F1ApiClient();
export default api;
