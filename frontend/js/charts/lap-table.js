/**
 * Lap Times Table Component
 * Interactive table showing lap times with click-to-telemetry functionality
 */

import { getCompoundColor } from '../utils/colors.js';
import { formatLapTime, formatDelta } from '../utils/formatters.js';
import { clearElement, createOption, populateSelect, escapeHtml } from '../utils/security.js';

export class LapTimesTable {
    constructor(container, options = {}) {
        this.container = document.querySelector(container);
        this.options = {
            onLapClick: null,
            onCompareClick: null,
            ...options,
        };

        this.laps = [];
        this.drivers = [];
        this.selectedLaps = new Set();
        this.sortColumn = 'lap_number';
        this.sortDirection = 'asc';
        this.fastestLap = null;
    }

    update(data, drivers = []) {
        this.laps = data || [];
        this.drivers = drivers;

        // Find fastest lap
        const validLaps = this.laps.filter(l => l.lap_time_seconds != null);
        if (validLaps.length > 0) {
            this.fastestLap = validLaps.reduce((min, l) =>
                l.lap_time_seconds < min.lap_time_seconds ? l : min
            );
        }

        this.render();
    }

    render() {
        if (!this.container) return;

        clearElement(this.container);

        if (!this.laps || this.laps.length === 0) {
            const noData = document.createElement('div');
            noData.className = 'no-data';
            noData.textContent = 'No lap data available';
            this.container.appendChild(noData);
            return;
        }

        // Create table wrapper
        const wrapper = document.createElement('div');
        wrapper.className = 'lap-table-wrapper';

        // Create controls
        const controls = this.createControls();
        wrapper.appendChild(controls);

        // Create table
        const table = document.createElement('table');
        table.className = 'lap-table';

        // Create header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');

        const headers = [
            { text: '', className: 'th-select', sortKey: null },
            { text: 'Driver', className: 'th-sortable', sortKey: 'driver_id' },
            { text: 'Lap', className: 'th-sortable', sortKey: 'lap_number' },
            { text: 'Time', className: 'th-sortable', sortKey: 'lap_time_seconds' },
            { text: 'Delta', className: 'th-sortable', sortKey: 'delta' },
            { text: 'Tyre', className: 'th-compound', sortKey: null },
            { text: 'Life', className: 'th-sortable', sortKey: 'tyre_life' },
            { text: 'S1', className: 'th-sortable', sortKey: 'sector_1_seconds' },
            { text: 'S2', className: 'th-sortable', sortKey: 'sector_2_seconds' },
            { text: 'S3', className: 'th-sortable', sortKey: 'sector_3_seconds' },
        ];

        headers.forEach(header => {
            const th = document.createElement('th');
            th.className = header.className;
            th.textContent = header.text;

            if (header.sortKey) {
                th.dataset.sort = header.sortKey;
                th.addEventListener('click', () => this.handleSort(header.sortKey));

                const sortIndicator = document.createElement('span');
                sortIndicator.className = 'sort-indicator';
                sortIndicator.textContent = this.getSortIndicator(header.sortKey);
                th.appendChild(sortIndicator);
            }

            headerRow.appendChild(th);
        });

        thead.appendChild(headerRow);
        table.appendChild(thead);

        // Create body
        const tbody = document.createElement('tbody');
        const sortedLaps = this.getSortedLaps();

        sortedLaps.forEach(lap => {
            const row = this.createLapRow(lap);
            tbody.appendChild(row);
        });

        table.appendChild(tbody);
        wrapper.appendChild(table);

        this.container.appendChild(wrapper);
    }

    createControls() {
        const controls = document.createElement('div');
        controls.className = 'lap-table-controls';

        // Driver filter
        const driverFilter = document.createElement('div');
        driverFilter.className = 'driver-filter-select';

        const label = document.createElement('label');
        label.textContent = 'Filter by Driver:';
        driverFilter.appendChild(label);

        const select = document.createElement('select');
        select.id = 'table-driver-filter';
        select.className = 'select-input';

        const driverOptions = this.drivers.map(d => ({ value: d, text: d }));
        populateSelect(select, driverOptions, 'All Drivers');

        select.addEventListener('change', (e) => {
            this.filterByDriver(e.target.value);
        });
        driverFilter.appendChild(select);
        controls.appendChild(driverFilter);

        // Compare button
        const compareBtn = document.createElement('button');
        compareBtn.className = 'btn btn-secondary compare-laps-btn';
        compareBtn.textContent = 'Compare Selected (0)';
        compareBtn.disabled = true;
        compareBtn.addEventListener('click', () => this.handleCompare());
        this.compareBtn = compareBtn;
        controls.appendChild(compareBtn);

        return controls;
    }

    createLapRow(lap) {
        const row = document.createElement('tr');
        row.className = 'lap-row';
        row.dataset.lapId = lap.id;

        // Add classes for special laps
        if (lap.is_personal_best) row.classList.add('personal-best');
        if (this.fastestLap && lap.id === this.fastestLap.id) row.classList.add('fastest-lap');
        if (!lap.is_valid_for_analysis) row.classList.add('invalid-lap');

        // Calculate delta from fastest
        const delta = lap.lap_time_seconds && this.fastestLap
            ? lap.lap_time_seconds - this.fastestLap.lap_time_seconds
            : null;

        const compoundColor = getCompoundColor(lap.compound);
        const compoundInitial = lap.compound ? lap.compound.charAt(0) : '-';

        // Build row cells using safe DOM methods
        // Checkbox cell
        const selectTd = document.createElement('td');
        selectTd.className = 'td-select';
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'lap-checkbox';
        checkbox.dataset.lapId = lap.id;
        checkbox.checked = this.selectedLaps.has(lap.id);
        selectTd.appendChild(checkbox);
        row.appendChild(selectTd);

        // Driver cell
        const driverTd = document.createElement('td');
        driverTd.className = 'td-driver';
        driverTd.textContent = lap.driver_id;
        row.appendChild(driverTd);

        // Lap number cell
        const lapNumTd = document.createElement('td');
        lapNumTd.className = 'td-lap-number';
        lapNumTd.textContent = lap.lap_number;
        row.appendChild(lapNumTd);

        // Lap time cell
        const lapTimeTd = document.createElement('td');
        lapTimeTd.className = 'td-lap-time' + (lap.is_personal_best ? ' pb' : '');
        lapTimeTd.textContent = formatLapTime(lap.lap_time_seconds);
        row.appendChild(lapTimeTd);

        // Delta cell
        const deltaTd = document.createElement('td');
        let deltaClass = 'td-delta';
        if (delta === 0) deltaClass += ' delta-zero';
        else if (delta > 0) deltaClass += ' delta-slower';
        deltaTd.className = deltaClass;
        deltaTd.textContent = delta === 0 ? '-' : formatDelta(delta);
        row.appendChild(deltaTd);

        // Compound cell
        const compoundTd = document.createElement('td');
        compoundTd.className = 'td-compound';
        const badge = document.createElement('span');
        badge.className = 'compound-badge';
        badge.style.backgroundColor = compoundColor;
        badge.textContent = compoundInitial;
        compoundTd.appendChild(badge);
        row.appendChild(compoundTd);

        // Tyre life cell
        const tyreLifeTd = document.createElement('td');
        tyreLifeTd.className = 'td-tyre-life';
        tyreLifeTd.textContent = lap.tyre_life ?? '-';
        row.appendChild(tyreLifeTd);

        // Sector cells
        [lap.sector_1_seconds, lap.sector_2_seconds, lap.sector_3_seconds].forEach(sectorTime => {
            const sectorTd = document.createElement('td');
            sectorTd.className = 'td-sector';
            sectorTd.textContent = this.formatSector(sectorTime);
            row.appendChild(sectorTd);
        });

        // Add checkbox handler
        checkbox.addEventListener('change', (e) => {
            e.stopPropagation();
            this.handleLapSelect(lap, e.target.checked);
        });

        // Add row click handler for telemetry
        row.addEventListener('click', (e) => {
            if (e.target.type !== 'checkbox') {
                this.handleLapClick(lap);
            }
        });

        return row;
    }

    formatSector(seconds) {
        if (seconds == null) return '-';
        return seconds.toFixed(3);
    }

    getSortedLaps() {
        const laps = [...this.laps];

        return laps.sort((a, b) => {
            let aVal = a[this.sortColumn];
            let bVal = b[this.sortColumn];

            // Handle null values
            if (aVal == null && bVal == null) return 0;
            if (aVal == null) return 1;
            if (bVal == null) return -1;

            // Compare
            if (typeof aVal === 'string') {
                aVal = aVal.toLowerCase();
                bVal = bVal.toLowerCase();
            }

            if (aVal < bVal) return this.sortDirection === 'asc' ? -1 : 1;
            if (aVal > bVal) return this.sortDirection === 'asc' ? 1 : -1;
            return 0;
        });
    }

    handleSort(column) {
        if (this.sortColumn === column) {
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortColumn = column;
            this.sortDirection = 'asc';
        }
        this.render();
    }

    getSortIndicator(column) {
        if (this.sortColumn !== column) return '';
        return this.sortDirection === 'asc' ? ' ▲' : ' ▼';
    }

    handleLapSelect(lap, checked) {
        if (checked) {
            this.selectedLaps.add(lap.id);
        } else {
            this.selectedLaps.delete(lap.id);
        }
        this.updateCompareButton();
    }

    updateCompareButton() {
        if (this.compareBtn) {
            const count = this.selectedLaps.size;
            this.compareBtn.textContent = `Compare Selected (${count})`;
            this.compareBtn.disabled = count < 2;
        }
    }

    handleLapClick(lap) {
        if (this.options.onLapClick) {
            this.options.onLapClick(lap);
        }
    }

    handleCompare() {
        if (this.options.onCompareClick && this.selectedLaps.size >= 2) {
            const selectedLapData = this.laps.filter(l => this.selectedLaps.has(l.id));
            this.options.onCompareClick(selectedLapData);
        }
    }

    filterByDriver(driverId) {
        const rows = this.container.querySelectorAll('.lap-row');
        rows.forEach(row => {
            const rowDriver = row.querySelector('.td-driver').textContent;
            if (!driverId || rowDriver === driverId) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    clearSelection() {
        this.selectedLaps.clear();
        this.updateCompareButton();
        this.container.querySelectorAll('.lap-checkbox').forEach(cb => {
            cb.checked = false;
        });
    }

    getSelectedLaps() {
        return this.laps.filter(l => this.selectedLaps.has(l.id));
    }
}

export default LapTimesTable;
