/**
 * Color utilities for F1 visualization
 */

// Tire compound colors
export const COMPOUND_COLORS = {
    SOFT: '#FF3333',
    MEDIUM: '#FCD500',
    HARD: '#EBEBEB',
    INTERMEDIATE: '#43B02A',
    WET: '#0067AD',
    UNKNOWN: '#888888',
};

// Team colors by year (official FastF1 colors)
export const TEAM_COLORS_BY_YEAR = {
    2025: {
        'Red Bull': '#0600ef',
        'Red Bull Racing': '#0600ef',
        'Ferrari': '#e80020',
        'Mercedes': '#27f4d2',
        'McLaren': '#ff8000',
        'Aston Martin': '#00665f',
        'Alpine': '#ff87bc',
        'Williams': '#00a0dd',
        'RB': '#fcd700',
        'Racing Bulls': '#fcd700',
        'Sauber': '#00e700',
        'Kick Sauber': '#00e700',
        'Haas': '#b6babd',
        'Haas F1 Team': '#b6babd',
    },
    2024: {
        'Red Bull': '#3671C6',
        'Red Bull Racing': '#3671C6',
        'Ferrari': '#E80020',
        'Mercedes': '#27F4D2',
        'McLaren': '#FF8000',
        'Aston Martin': '#229971',
        'Alpine': '#FF87BC',
        'Williams': '#64C4FF',
        'RB': '#6692FF',
        'AlphaTauri': '#6692FF',
        'Sauber': '#52E252',
        'Kick Sauber': '#52E252',
        'Haas': '#B6BABD',
        'Haas F1 Team': '#B6BABD',
    },
};

// Driver to team mapping by year
export const DRIVER_TEAMS_BY_YEAR = {
    2025: {
        // Red Bull
        'VER': { team: 'Red Bull', position: 1 },
        'LAW': { team: 'Red Bull', position: 2 },
        // Ferrari
        'LEC': { team: 'Ferrari', position: 1 },
        'HAM': { team: 'Ferrari', position: 2 },
        // Mercedes
        'RUS': { team: 'Mercedes', position: 1 },
        'ANT': { team: 'Mercedes', position: 2 },
        // McLaren
        'NOR': { team: 'McLaren', position: 1 },
        'PIA': { team: 'McLaren', position: 2 },
        // Aston Martin
        'ALO': { team: 'Aston Martin', position: 1 },
        'STR': { team: 'Aston Martin', position: 2 },
        // Alpine
        'GAS': { team: 'Alpine', position: 1 },
        'DOO': { team: 'Alpine', position: 2 },
        'COL': { team: 'Alpine', position: 2 }, // Colapinto replacement
        // Williams
        'ALB': { team: 'Williams', position: 1 },
        'SAI': { team: 'Williams', position: 2 },
        // RB / Racing Bulls
        'TSU': { team: 'RB', position: 1 },
        'HAD': { team: 'RB', position: 2 },
        // Sauber
        'HUL': { team: 'Sauber', position: 1 },
        'BOR': { team: 'Sauber', position: 2 },
        // Haas
        'OCO': { team: 'Haas', position: 1 },
        'BEA': { team: 'Haas', position: 2 },
    },
    2024: {
        // Red Bull
        'VER': { team: 'Red Bull', position: 1 },
        'PER': { team: 'Red Bull', position: 2 },
        // Ferrari
        'LEC': { team: 'Ferrari', position: 1 },
        'SAI': { team: 'Ferrari', position: 2 },
        // Mercedes
        'HAM': { team: 'Mercedes', position: 1 },
        'RUS': { team: 'Mercedes', position: 2 },
        // McLaren
        'NOR': { team: 'McLaren', position: 1 },
        'PIA': { team: 'McLaren', position: 2 },
        // Aston Martin
        'ALO': { team: 'Aston Martin', position: 1 },
        'STR': { team: 'Aston Martin', position: 2 },
        // Alpine
        'GAS': { team: 'Alpine', position: 1 },
        'OCO': { team: 'Alpine', position: 2 },
        // Williams
        'ALB': { team: 'Williams', position: 1 },
        'SAR': { team: 'Williams', position: 2 },
        'COL': { team: 'Williams', position: 2 }, // Colapinto mid-season
        // RB / AlphaTauri
        'TSU': { team: 'RB', position: 1 },
        'RIC': { team: 'RB', position: 2 },
        'LAW': { team: 'RB', position: 2 }, // Lawson mid-season
        // Sauber
        'BOT': { team: 'Sauber', position: 1 },
        'ZHO': { team: 'Sauber', position: 2 },
        // Haas
        'MAG': { team: 'Haas', position: 1 },
        'HUL': { team: 'Haas', position: 2 },
        'BEA': { team: 'Haas', position: 2 }, // Bearman substitute
    },
};

// Legacy team colors (fallback)
export const TEAM_COLORS = TEAM_COLORS_BY_YEAR[2025];

// D3 color scale for drivers (fallback only)
export const DRIVER_COLORS = d3.scaleOrdinal(d3.schemeTableau10);

/**
 * Get color for a tire compound
 */
export function getCompoundColor(compound) {
    return COMPOUND_COLORS[compound?.toUpperCase()] || COMPOUND_COLORS.UNKNOWN;
}

/**
 * Get color for a team (with year support)
 * @param {string} teamName - Team name
 * @param {number} year - Season year (default: 2025)
 */
export function getTeamColor(teamName, year = 2025) {
    const yearColors = TEAM_COLORS_BY_YEAR[year] || TEAM_COLORS_BY_YEAR[2025];

    // Direct match
    if (yearColors[teamName]) {
        return yearColors[teamName];
    }

    // Fuzzy match
    for (const [name, color] of Object.entries(yearColors)) {
        if (teamName?.toLowerCase().includes(name.toLowerCase())) {
            return color;
        }
    }
    return '#888888';
}

/**
 * Get color for a driver based on team (with teammate differentiation)
 * @param {string} driverId - Driver abbreviation (e.g., 'VER', 'HAM')
 * @param {number} year - Season year (default: 2025)
 * @returns {string} Hex color code
 */
export function getDriverColor(driverId, year = 2025) {
    const yearDrivers = DRIVER_TEAMS_BY_YEAR[year] || DRIVER_TEAMS_BY_YEAR[2025];
    const driverInfo = yearDrivers[driverId];

    if (driverInfo) {
        const teamColor = getTeamColor(driverInfo.team, year);
        // Driver 1 gets base color, Driver 2 gets a lighter variant
        if (driverInfo.position === 2) {
            return lightenColor(teamColor, 25);
        }
        return teamColor;
    }

    // Fallback to D3 scale for unknown drivers
    return DRIVER_COLORS(driverId);
}

/**
 * Get both driver color and team info
 * @param {string} driverId - Driver abbreviation
 * @param {number} year - Season year
 * @returns {object} Object with color, team, and position
 */
export function getDriverInfo(driverId, year = 2025) {
    const yearDrivers = DRIVER_TEAMS_BY_YEAR[year] || DRIVER_TEAMS_BY_YEAR[2025];
    const driverInfo = yearDrivers[driverId];

    if (driverInfo) {
        return {
            color: getDriverColor(driverId, year),
            team: driverInfo.team,
            teamColor: getTeamColor(driverInfo.team, year),
            position: driverInfo.position,
        };
    }

    return {
        color: DRIVER_COLORS(driverId),
        team: 'Unknown',
        teamColor: '#888888',
        position: 1,
    };
}

/**
 * Lighten a color by a percentage
 */
export function lightenColor(color, percent) {
    const num = parseInt(color.replace('#', ''), 16);
    const amt = Math.round(2.55 * percent);
    const R = (num >> 16) + amt;
    const G = (num >> 8 & 0x00FF) + amt;
    const B = (num & 0x0000FF) + amt;
    return '#' + (
        0x1000000 +
        (R < 255 ? (R < 1 ? 0 : R) : 255) * 0x10000 +
        (G < 255 ? (G < 1 ? 0 : G) : 255) * 0x100 +
        (B < 255 ? (B < 1 ? 0 : B) : 255)
    ).toString(16).slice(1);
}

/**
 * Darken a color by a percentage
 */
export function darkenColor(color, percent) {
    return lightenColor(color, -percent);
}
