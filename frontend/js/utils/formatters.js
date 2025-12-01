/**
 * Formatting utilities for F1 data
 */

/**
 * Format lap time from seconds to M:SS.mmm
 */
export function formatLapTime(seconds) {
    if (seconds == null || isNaN(seconds)) {
        return '--:--.---';
    }

    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    const secsStr = secs.toFixed(3).padStart(6, '0');

    return `${minutes}:${secsStr}`;
}

/**
 * Format lap time delta (difference)
 */
export function formatDelta(seconds) {
    if (seconds == null || isNaN(seconds)) {
        return '--.---';
    }

    const sign = seconds >= 0 ? '+' : '-';
    const abs = Math.abs(seconds);

    if (abs >= 60) {
        return formatLapTime(abs);
    }

    return `${sign}${abs.toFixed(3)}`;
}

/**
 * Format speed in km/h
 */
export function formatSpeed(kmh) {
    if (kmh == null) return '--';
    return `${Math.round(kmh)} km/h`;
}

/**
 * Format percentage
 */
export function formatPercent(value) {
    if (value == null) return '--';
    return `${Math.round(value)}%`;
}

/**
 * Format driver name for display
 */
export function formatDriverName(driver) {
    if (typeof driver === 'string') {
        return driver;
    }
    return driver?.id || driver?.abbreviation || '--';
}

/**
 * Format session type for display
 */
export function formatSessionType(type) {
    const types = {
        'FP1': 'Practice 1',
        'FP2': 'Practice 2',
        'FP3': 'Practice 3',
        'Q': 'Qualifying',
        'SS': 'Sprint Shootout',
        'S': 'Sprint',
        'R': 'Race',
    };
    return types[type] || type;
}

/**
 * Format compound name
 */
export function formatCompound(compound) {
    return compound?.charAt(0).toUpperCase() + compound?.slice(1).toLowerCase();
}

/**
 * Format number with commas
 */
export function formatNumber(num, decimals = 0) {
    if (num == null) return '--';
    return num.toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
    });
}

/**
 * Format distance in meters/kilometers
 */
export function formatDistance(meters) {
    if (meters == null) return '--';
    if (meters >= 1000) {
        return `${(meters / 1000).toFixed(2)} km`;
    }
    return `${Math.round(meters)} m`;
}
