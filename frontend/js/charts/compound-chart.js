/**
 * Compound Performance Chart
 * Bar chart showing lap time statistics by tire compound with fuel & degradation corrections
 */

import { BaseChart } from './base-chart.js';
import { getCompoundColor } from '../utils/colors.js';
import { formatLapTime } from '../utils/formatters.js';

export class CompoundChart extends BaseChart {
    constructor(container, options = {}) {
        super(container, {
            margin: { top: 30, right: 30, bottom: 80, left: 70 },
            ...options,
        });

        this.xScale = null;
        this.yScale = null;
    }

    setupScales(data) {
        if (!data || !data.compounds || Object.keys(data.compounds).length === 0) return;

        const compounds = Object.keys(data.compounds);

        // Get min/max from all relevant metrics
        const allTimes = [];
        Object.values(data.compounds).forEach(c => {
            if (c.fastest) allTimes.push(c.fastest);
            if (c.fastest_fuel_corrected) allTimes.push(c.fastest_fuel_corrected);
            if (c.fresh_tire_pace) allTimes.push(c.fresh_tire_pace);
        });

        if (allTimes.length === 0) return;

        // X: Compounds
        this.xScale = d3.scaleBand()
            .domain(compounds)
            .range([0, this.width])
            .padding(0.2);

        // Y: Lap times (normal: smaller values at bottom)
        const minTime = d3.min(allTimes) * 0.998;
        const maxTime = d3.max(allTimes) * 1.002;

        this.yScale = d3.scaleLinear()
            .domain([minTime, maxTime])
            .range([0, this.height]);
    }

    render(data) {
        if (!data || !data.compounds || Object.keys(data.compounds).length === 0) {
            this.showNoData('No compound performance data available. Load a session first.');
            return;
        }

        // Add grid
        this.addGrid(this.xScale, this.yScale, { showX: false });

        // Add axes (hide X-axis ticks since we draw custom compound labels)
        this.addXAxis(this.xScale, { label: '', tickFormat: () => '' });
        this.addYAxis(this.yScale, {
            label: 'Lap Time',
            tickFormat: d => formatLapTime(d),
        });

        // Draw bars for each compound
        Object.entries(data.compounds).forEach(([compound, stats]) => {
            if (!stats.fastest) return;
            this.drawCompoundBar(compound, stats);
        });

        // Add legend
        this.addLegend();
    }

    drawCompoundBar(compound, stats) {
        const x = this.xScale(compound);
        const barWidth = this.xScale.bandwidth();
        const color = getCompoundColor(compound);
        const subBarWidth = barWidth / 3 - 4;

        const g = this.chartGroup
            .append('g')
            .attr('class', 'compound-bar data-element')
            .attr('transform', `translate(${x}, 0)`);

        // Draw 3 sub-bars for comparison
        const metrics = [
            { key: 'fastest', label: 'Raw Fastest', offset: 0 },
            { key: 'fastest_fuel_corrected', label: 'Fuel Corrected', offset: subBarWidth + 4 },
            { key: 'fresh_tire_pace', label: 'Fresh Tire', offset: (subBarWidth + 4) * 2 },
        ];

        metrics.forEach((metric, i) => {
            const value = stats[metric.key];
            if (!value) return;

            const barY = this.yScale(value);
            const barHeight = barY; // Bar grows from 0 up to the value

            // Bar
            g.append('rect')
                .attr('class', `${metric.key}-bar`)
                .attr('x', metric.offset)
                .attr('y', 0)
                .attr('width', subBarWidth)
                .attr('height', Math.max(barHeight, 1))
                .attr('fill', color)
                .attr('fill-opacity', i === 0 ? 0.8 : (i === 1 ? 0.5 : 0.3))
                .attr('stroke', color)
                .attr('stroke-width', 1)
                .on('mouseenter', (event) => this.handleMouseEnter(event, compound, stats))
                .on('mouseleave', () => this.hideTooltip());

            // Time label on top of bar
            g.append('text')
                .attr('class', 'time-label')
                .attr('x', metric.offset + subBarWidth / 2)
                .attr('y', barY + 12)
                .attr('text-anchor', 'middle')
                .attr('fill', color)
                .attr('font-size', '9px')
                .attr('font-weight', i === 0 ? 'bold' : 'normal')
                .text(formatLapTime(value));
        });

        // Compound name label at bottom
        g.append('text')
            .attr('class', 'compound-label')
            .attr('x', barWidth / 2)
            .attr('y', this.height + 20)
            .attr('text-anchor', 'middle')
            .attr('fill', color)
            .attr('font-size', '12px')
            .attr('font-weight', 'bold')
            .text(compound);

        // Lap count
        g.append('text')
            .attr('class', 'count-label')
            .attr('x', barWidth / 2)
            .attr('y', this.height + 35)
            .attr('text-anchor', 'middle')
            .attr('fill', '#888')
            .attr('font-size', '10px')
            .text(`${stats.count} laps`);

        // Fastest lap driver info
        if (stats.fastest_lap) {
            g.append('text')
                .attr('class', 'driver-label')
                .attr('x', barWidth / 2)
                .attr('y', this.height + 50)
                .attr('text-anchor', 'middle')
                .attr('fill', '#aaa')
                .attr('font-size', '9px')
                .text(`${stats.fastest_lap.driver} L${stats.fastest_lap.lap_number} (T${stats.fastest_lap.tyre_life})`);
        }
    }

    addLegend() {
        const legendData = [
            { label: 'Raw Fastest', opacity: 0.8 },
            { label: 'Fuel Corrected', opacity: 0.5 },
            { label: 'Fresh Tire Pace', opacity: 0.3 },
        ];

        // Position legend horizontally at the top
        const legend = this.chartGroup
            .append('g')
            .attr('class', 'legend data-element')
            .attr('transform', `translate(${this.width / 2 - 150}, -15)`);

        legendData.forEach((item, i) => {
            const lg = legend.append('g')
                .attr('transform', `translate(${i * 110}, 0)`);

            lg.append('rect')
                .attr('width', 12)
                .attr('height', 12)
                .attr('fill', '#888')
                .attr('fill-opacity', item.opacity)
                .attr('stroke', '#888');

            lg.append('text')
                .attr('x', 16)
                .attr('y', 10)
                .attr('fill', '#aaa')
                .attr('font-size', '10px')
                .text(item.label);
        });
    }

    handleMouseEnter(event, compound, stats) {
        const fastestLap = stats.fastest_lap;
        const fuelDelta = stats.fastest_fuel_corrected - stats.fastest;
        const freshDelta = stats.fresh_tire_pace - stats.fastest;

        let fastestLapInfo = '';
        if (fastestLap) {
            fastestLapInfo = `
                <div class="tooltip-section">
                    <div class="tooltip-subtitle">Fastest Lap</div>
                    <div class="tooltip-row">
                        <span class="tooltip-label">Driver:</span>
                        <span class="tooltip-value">${fastestLap.driver}</span>
                    </div>
                    <div class="tooltip-row">
                        <span class="tooltip-label">Lap:</span>
                        <span class="tooltip-value">${fastestLap.lap_number}</span>
                    </div>
                    <div class="tooltip-row">
                        <span class="tooltip-label">Tyre Life:</span>
                        <span class="tooltip-value">${fastestLap.tyre_life} laps</span>
                    </div>
                </div>
            `;
        }

        const content = `
            <div class="tooltip-title">${compound}</div>
            <div class="tooltip-content">
                <div class="tooltip-row">
                    <span class="tooltip-label">Lap Count:</span>
                    <span class="tooltip-value">${stats.count}</span>
                </div>
                <div class="tooltip-section">
                    <div class="tooltip-subtitle">Raw Times</div>
                    <div class="tooltip-row">
                        <span class="tooltip-label">Fastest:</span>
                        <span class="tooltip-value">${formatLapTime(stats.fastest)}</span>
                    </div>
                    <div class="tooltip-row">
                        <span class="tooltip-label">Average:</span>
                        <span class="tooltip-value">${formatLapTime(stats.average)}</span>
                    </div>
                </div>
                <div class="tooltip-section">
                    <div class="tooltip-subtitle">Fuel Corrected</div>
                    <div class="tooltip-row">
                        <span class="tooltip-label">Fastest:</span>
                        <span class="tooltip-value">${formatLapTime(stats.fastest_fuel_corrected)} (+${fuelDelta.toFixed(3)}s)</span>
                    </div>
                </div>
                <div class="tooltip-section">
                    <div class="tooltip-subtitle">Fresh Tire Pace</div>
                    <div class="tooltip-row">
                        <span class="tooltip-label">Baseline:</span>
                        <span class="tooltip-value">${formatLapTime(stats.fresh_tire_pace)} (+${freshDelta.toFixed(3)}s)</span>
                    </div>
                </div>
                ${fastestLapInfo}
            </div>
        `;
        this.showTooltip(event, content);
    }
}

export default CompoundChart;
