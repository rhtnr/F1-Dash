/**
 * Strategy Chart
 * Horizontal bar chart showing tire strategies for each driver
 */

import { BaseChart } from './base-chart.js';
import { getCompoundColor } from '../utils/colors.js';
import { formatLapTime } from '../utils/formatters.js';

export class StrategyChart extends BaseChart {
    constructor(container, options = {}) {
        super(container, {
            margin: { top: 30, right: 30, bottom: 40, left: 60 },
            ...options,
        });

        this.xScale = null;
        this.yScale = null;
    }

    setupScales(data) {
        if (!data || !data.strategies || data.strategies.length === 0) return;

        const strategies = data.strategies;

        // Get max lap
        const maxLap = d3.max(strategies, s =>
            d3.max(s.stints, stint => stint.end_lap)
        );

        // X: Lap number
        this.xScale = d3.scaleLinear()
            .domain([0, maxLap])
            .range([0, this.width]);

        // Y: Drivers
        const drivers = strategies.map(s => s.driver_id);
        this.yScale = d3.scaleBand()
            .domain(drivers)
            .range([0, this.height])
            .padding(0.2);
    }

    render(data) {
        if (!data || !data.strategies || data.strategies.length === 0) {
            this.showNoData('No strategy data available');
            return;
        }

        const strategies = data.strategies;

        // Add axes
        this.addXAxis(this.xScale, { label: 'Lap' });

        // Y axis with driver names
        this.chartGroup
            .append('g')
            .attr('class', 'y-axis axis')
            .call(d3.axisLeft(this.yScale));

        // Draw stint bars for each driver
        strategies.forEach(strategy => {
            const driverGroup = this.chartGroup
                .append('g')
                .attr('class', 'driver-stints data-element');

            strategy.stints.forEach(stint => {
                const x = this.xScale(stint.start_lap);
                const width = this.xScale(stint.end_lap) - this.xScale(stint.start_lap);
                const y = this.yScale(strategy.driver_id);
                const height = this.yScale.bandwidth();

                // Stint bar
                driverGroup
                    .append('rect')
                    .attr('class', 'stint-bar')
                    .attr('x', x)
                    .attr('y', y)
                    .attr('width', Math.max(width, 2))
                    .attr('height', height)
                    .attr('fill', getCompoundColor(stint.compound))
                    .attr('rx', 2)
                    .on('mouseenter', (event) => this.handleMouseEnter(event, stint, strategy.driver_id))
                    .on('mouseleave', () => this.hideTooltip());

                // Compound label (if stint is wide enough)
                if (width > 20) {
                    driverGroup
                        .append('text')
                        .attr('class', 'stint-label')
                        .attr('x', x + width / 2)
                        .attr('y', y + height / 2)
                        .attr('text-anchor', 'middle')
                        .attr('dominant-baseline', 'middle')
                        .attr('fill', stint.compound === 'HARD' ? '#1a1a2e' : '#1a1a2e')
                        .text(stint.compound.charAt(0));
                }
            });
        });

        // Add legend
        this.addCompoundLegend();
    }

    handleMouseEnter(event, stint, driverId) {
        const avgTime = stint.avg_lap_time
            ? formatLapTime(stint.avg_lap_time)
            : '--';
        const degradation = stint.degradation_rate != null
            ? `${stint.degradation_rate.toFixed(3)}s/lap`
            : '--';

        const content = `
            <div class="tooltip-title">${driverId} - Stint ${stint.stint_number}</div>
            <div class="tooltip-content">
                <div class="tooltip-row">
                    <span class="tooltip-label">Compound:</span>
                    <span class="tooltip-value">${stint.compound}</span>
                </div>
                <div class="tooltip-row">
                    <span class="tooltip-label">Laps:</span>
                    <span class="tooltip-value">${stint.start_lap} - ${stint.end_lap} (${stint.total_laps})</span>
                </div>
                <div class="tooltip-row">
                    <span class="tooltip-label">Avg Lap:</span>
                    <span class="tooltip-value">${avgTime}</span>
                </div>
                <div class="tooltip-row">
                    <span class="tooltip-label">Degradation:</span>
                    <span class="tooltip-value">${degradation}</span>
                </div>
            </div>
        `;
        this.showTooltip(event, content);
    }

    addCompoundLegend() {
        const compounds = ['SOFT', 'MEDIUM', 'HARD', 'INTERMEDIATE', 'WET'];

        const legend = this.chartGroup
            .append('g')
            .attr('class', 'legend')
            .attr('transform', `translate(0, -15)`);

        compounds.forEach((compound, i) => {
            const g = legend.append('g')
                .attr('transform', `translate(${i * 100}, 0)`);

            g.append('rect')
                .attr('width', 14)
                .attr('height', 14)
                .attr('fill', getCompoundColor(compound))
                .attr('rx', 2);

            g.append('text')
                .attr('x', 20)
                .attr('y', 11)
                .attr('fill', '#8892a0')
                .attr('font-size', '11px')
                .text(compound.charAt(0) + compound.slice(1).toLowerCase());
        });
    }
}

export default StrategyChart;
