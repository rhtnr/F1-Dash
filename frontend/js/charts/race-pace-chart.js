/**
 * Race Pace Chart
 * Box plot showing lap time distribution by driver with pace analysis
 */

import { BaseChart } from './base-chart.js';
import { getCompoundColor, getDriverColor } from '../utils/colors.js';
import { formatLapTime } from '../utils/formatters.js';

export class RacePaceChart extends BaseChart {
    constructor(container, options = {}) {
        super(container, {
            margin: { top: 30, right: 30, bottom: 60, left: 70 },
            ...options,
        });

        this.xScale = null;
        this.yScale = null;
        this.year = options.year || 2025;
    }

    setYear(year) {
        this.year = year;
    }

    setupScales(data) {
        if (!data || !data.drivers || Object.keys(data.drivers).length === 0) return;

        const drivers = Object.keys(data.drivers);
        const allTimes = Object.values(data.drivers).flat();

        if (allTimes.length === 0) return;

        // X: Drivers
        this.xScale = d3.scaleBand()
            .domain(drivers)
            .range([0, this.width])
            .padding(0.3);

        // Y: Lap times (using 5th and 95th percentile for range)
        const sortedTimes = allTimes.sort((a, b) => a - b);
        const minTime = d3.quantile(sortedTimes, 0.05);
        const maxTime = d3.quantile(sortedTimes, 0.95);

        this.yScale = d3.scaleLinear()
            .domain([minTime * 0.99, maxTime * 1.01]) // Normal: smaller values at bottom
            .range([0, this.height]);
    }

    render(data) {
        if (!data || !data.drivers || Object.keys(data.drivers).length === 0) {
            this.showNoData('No race pace data available. Load a session first.');
            return;
        }

        // Add grid
        this.addGrid(this.xScale, this.yScale, { showX: false });

        // Add axes
        this.addXAxis(this.xScale, { label: 'Driver' });
        this.addYAxis(this.yScale, {
            label: 'Lap Time',
            tickFormat: d => formatLapTime(d),
        });

        // Draw box plots for each driver
        Object.entries(data.drivers).forEach(([driver, times], index) => {
            if (times.length === 0) return;
            this.drawBoxPlot(driver, times, index);
        });

        // Add reference line for median of all times
        const allTimes = Object.values(data.drivers).flat();
        const overallMedian = d3.median(allTimes);
        if (overallMedian) {
            this.chartGroup
                .append('line')
                .attr('class', 'median-reference data-element')
                .attr('x1', 0)
                .attr('x2', this.width)
                .attr('y1', this.yScale(overallMedian))
                .attr('y2', this.yScale(overallMedian))
                .attr('stroke', '#e94560')
                .attr('stroke-width', 2)
                .attr('stroke-dasharray', '5,5')
                .attr('opacity', 0.7);

            // Label
            this.chartGroup
                .append('text')
                .attr('class', 'median-label data-element')
                .attr('x', this.width - 5)
                .attr('y', this.yScale(overallMedian) - 5)
                .attr('text-anchor', 'end')
                .attr('fill', '#e94560')
                .attr('font-size', '10px')
                .text(`Median: ${formatLapTime(overallMedian)}`);
        }
    }

    drawBoxPlot(driver, times, index) {
        const sortedTimes = times.sort((a, b) => a - b);

        // Calculate box plot statistics
        const q1 = d3.quantile(sortedTimes, 0.25);
        const median = d3.quantile(sortedTimes, 0.5);
        const q3 = d3.quantile(sortedTimes, 0.75);
        const iqr = q3 - q1;
        const min = Math.max(d3.min(sortedTimes), q1 - 1.5 * iqr);
        const max = Math.min(d3.max(sortedTimes), q3 + 1.5 * iqr);

        const x = this.xScale(driver);
        const boxWidth = this.xScale.bandwidth();
        const color = getDriverColor(driver, this.year);

        const g = this.chartGroup
            .append('g')
            .attr('class', 'box-plot data-element')
            .attr('transform', `translate(${x}, 0)`);

        // Whisker lines
        g.append('line')
            .attr('class', 'whisker')
            .attr('x1', boxWidth / 2)
            .attr('x2', boxWidth / 2)
            .attr('y1', this.yScale(min))
            .attr('y2', this.yScale(q1))
            .attr('stroke', color)
            .attr('stroke-width', 1);

        g.append('line')
            .attr('class', 'whisker')
            .attr('x1', boxWidth / 2)
            .attr('x2', boxWidth / 2)
            .attr('y1', this.yScale(q3))
            .attr('y2', this.yScale(max))
            .attr('stroke', color)
            .attr('stroke-width', 1);

        // Whisker caps
        g.append('line')
            .attr('class', 'whisker-cap')
            .attr('x1', boxWidth * 0.25)
            .attr('x2', boxWidth * 0.75)
            .attr('y1', this.yScale(min))
            .attr('y2', this.yScale(min))
            .attr('stroke', color)
            .attr('stroke-width', 1);

        g.append('line')
            .attr('class', 'whisker-cap')
            .attr('x1', boxWidth * 0.25)
            .attr('x2', boxWidth * 0.75)
            .attr('y1', this.yScale(max))
            .attr('y2', this.yScale(max))
            .attr('stroke', color)
            .attr('stroke-width', 1);

        // Box - ensure positive height with Math.abs and handle edge cases
        const boxY = Math.min(this.yScale(q1), this.yScale(q3));
        const boxHeight = Math.abs(this.yScale(q1) - this.yScale(q3));

        g.append('rect')
            .attr('class', 'box')
            .attr('x', 0)
            .attr('y', boxY)
            .attr('width', boxWidth)
            .attr('height', Math.max(boxHeight, 1))
            .attr('fill', color)
            .attr('fill-opacity', 0.3)
            .attr('stroke', color)
            .attr('stroke-width', 2)
            .on('mouseenter', (event) => this.handleMouseEnter(event, driver, {
                min, q1, median, q3, max, count: times.length
            }))
            .on('mouseleave', () => this.hideTooltip());

        // Median line
        g.append('line')
            .attr('class', 'median-line')
            .attr('x1', 0)
            .attr('x2', boxWidth)
            .attr('y1', this.yScale(median))
            .attr('y2', this.yScale(median))
            .attr('stroke', color)
            .attr('stroke-width', 3);

        // Individual points (jittered) for outliers
        const outliers = sortedTimes.filter(t => t < min || t > max);
        outliers.forEach(t => {
            g.append('circle')
                .attr('class', 'outlier')
                .attr('cx', boxWidth / 2 + (Math.random() - 0.5) * boxWidth * 0.5)
                .attr('cy', this.yScale(t))
                .attr('r', 3)
                .attr('fill', color)
                .attr('fill-opacity', 0.5);
        });
    }

    handleMouseEnter(event, driver, stats) {
        const content = `
            <div class="tooltip-title">${driver} - Race Pace</div>
            <div class="tooltip-content">
                <div class="tooltip-row">
                    <span class="tooltip-label">Laps:</span>
                    <span class="tooltip-value">${stats.count}</span>
                </div>
                <div class="tooltip-row">
                    <span class="tooltip-label">Median:</span>
                    <span class="tooltip-value">${formatLapTime(stats.median)}</span>
                </div>
                <div class="tooltip-row">
                    <span class="tooltip-label">Q1 (25%):</span>
                    <span class="tooltip-value">${formatLapTime(stats.q1)}</span>
                </div>
                <div class="tooltip-row">
                    <span class="tooltip-label">Q3 (75%):</span>
                    <span class="tooltip-value">${formatLapTime(stats.q3)}</span>
                </div>
                <div class="tooltip-row">
                    <span class="tooltip-label">Best:</span>
                    <span class="tooltip-value">${formatLapTime(stats.min)}</span>
                </div>
            </div>
        `;
        this.showTooltip(event, content);
    }
}

export default RacePaceChart;
