/**
 * Lap Times Chart
 * Scatter plot showing lap times over the race/session
 */

import { BaseChart } from './base-chart.js';
import { getDriverColor, getCompoundColor } from '../utils/colors.js';
import { formatLapTime } from '../utils/formatters.js';

export class LapTimesChart extends BaseChart {
    constructor(container, options = {}) {
        super(container, {
            margin: { top: 20, right: 120, bottom: 50, left: 70 },
            ...options,
        });

        this.xScale = null;
        this.yScale = null;
        this.colorScale = null;
        this.selectedDrivers = new Set();
        this.year = options.year || 2025;
    }

    setYear(year) {
        this.year = year;
    }

    setupScales(data) {
        if (!data || data.length === 0) return;

        // Filter to valid laps
        const validData = data.filter(d => d.lap_time_seconds != null);

        // X: Lap number
        const maxLap = d3.max(validData, d => d.lap_number);
        this.xScale = d3.scaleLinear()
            .domain([1, maxLap])
            .range([0, this.width]);

        // Y: Lap time (normal: smaller values at bottom)
        const times = validData.map(d => d.lap_time_seconds);
        const minTime = d3.min(times);
        const maxTime = d3.quantile(times.sort((a, b) => a - b), 0.95); // 95th percentile to exclude outliers

        this.yScale = d3.scaleLinear()
            .domain([minTime * 0.98, maxTime * 1.02])
            .range([0, this.height]);

        // Color: by driver using team colors
        const drivers = [...new Set(validData.map(d => d.driver_id))];
        this.colorScale = (driverId) => getDriverColor(driverId, this.year);
    }

    render(data) {
        if (!data || data.length === 0) {
            this.showNoData('No lap data available');
            return;
        }

        // Filter valid laps
        let validData = data.filter(d => d.lap_time_seconds != null);

        // Filter by selected drivers if any
        if (this.selectedDrivers.size > 0) {
            validData = validData.filter(d => this.selectedDrivers.has(d.driver_id));
        }

        // Add grid
        this.addGrid(this.xScale, this.yScale);

        // Add axes
        this.addXAxis(this.xScale, { label: 'Lap Number' });
        this.addYAxis(this.yScale, {
            label: 'Lap Time',
            tickFormat: d => formatLapTime(d),
        });

        // Group data by driver
        const byDriver = d3.group(validData, d => d.driver_id);

        // Draw lines for each driver
        const line = d3.line()
            .defined(d => d.lap_time_seconds != null)
            .x(d => this.xScale(d.lap_number))
            .y(d => this.yScale(d.lap_time_seconds));

        this.chartGroup.selectAll('.driver-line')
            .data(byDriver)
            .join('path')
            .attr('class', 'driver-line data-element')
            .attr('d', d => line(d[1].sort((a, b) => a.lap_number - b.lap_number)))
            .attr('stroke', d => this.colorScale(d[0]))
            .attr('fill', 'none')
            .attr('stroke-width', 2)
            .attr('opacity', 0.7);

        // Draw points
        this.chartGroup.selectAll('.lap-point')
            .data(validData)
            .join('circle')
            .attr('class', 'lap-point data-element')
            .attr('cx', d => this.xScale(d.lap_number))
            .attr('cy', d => this.yScale(d.lap_time_seconds))
            .attr('r', 4)
            .attr('fill', d => getCompoundColor(d.compound))
            .attr('stroke', d => this.colorScale(d.driver_id))
            .attr('stroke-width', 2)
            .on('mouseenter', (event, d) => this.handleMouseEnter(event, d))
            .on('mouseleave', () => this.hideTooltip());

        // Add legend
        this.addLegend(byDriver);
    }

    handleMouseEnter(event, d) {
        const content = `
            <div class="tooltip-title">${d.driver_id} - Lap ${d.lap_number}</div>
            <div class="tooltip-content">
                <div class="tooltip-row">
                    <span class="tooltip-label">Time:</span>
                    <span class="tooltip-value">${d.lap_time || '--'}</span>
                </div>
                <div class="tooltip-row">
                    <span class="tooltip-label">Compound:</span>
                    <span class="tooltip-value">${d.compound}</span>
                </div>
                <div class="tooltip-row">
                    <span class="tooltip-label">Tyre Life:</span>
                    <span class="tooltip-value">${d.tyre_life} laps</span>
                </div>
                ${d.is_personal_best ? '<div style="color: #9f7aea; margin-top: 4px;">★ Personal Best</div>' : ''}
            </div>
        `;
        this.showTooltip(event, content);
    }

    addLegend(byDriver) {
        const legend = this.chartGroup.append('g')
            .attr('class', 'legend')
            .attr('transform', `translate(${this.width + 10}, 0)`);

        const drivers = Array.from(byDriver.keys());

        // Use two columns if more than 10 drivers to avoid overflow
        const useMultiColumn = drivers.length > 10;
        const itemHeight = 16;
        const columnWidth = 55;

        drivers.forEach((driver, i) => {
            const col = useMultiColumn ? Math.floor(i / Math.ceil(drivers.length / 2)) : 0;
            const row = useMultiColumn ? i % Math.ceil(drivers.length / 2) : i;

            const g = legend.append('g')
                .attr('transform', `translate(${col * columnWidth}, ${row * itemHeight})`);

            g.append('rect')
                .attr('width', 10)
                .attr('height', 10)
                .attr('fill', this.colorScale(driver));

            g.append('text')
                .attr('x', 14)
                .attr('y', 9)
                .attr('fill', '#eaeaea')
                .attr('font-size', '10px')
                .text(driver);
        });
    }

    setSelectedDrivers(drivers) {
        this.selectedDrivers = new Set(drivers);
        if (this._lastData) {
            this.update(this._lastData);
        }
    }
}

export default LapTimesChart;
