/**
 * Position Chart
 * Line chart showing position changes throughout the race
 */

import { BaseChart } from './base-chart.js';
import { getDriverColor } from '../utils/colors.js';

export class PositionChart extends BaseChart {
    constructor(container, options = {}) {
        super(container, {
            margin: { top: 30, right: 100, bottom: 50, left: 50 },
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
        if (!data || !data.positions || Object.keys(data.positions).length === 0) return;

        const positions = data.positions;
        const maxLap = d3.max(Object.values(positions).flat(), d => d.lap);
        const driverCount = Object.keys(positions).length;

        // X: Lap number
        this.xScale = d3.scaleLinear()
            .domain([1, maxLap])
            .range([0, this.width]);

        // Y: Position (1 at top, 20 at bottom)
        this.yScale = d3.scaleLinear()
            .domain([1, Math.max(20, driverCount)])
            .range([0, this.height]);
    }

    render(data) {
        if (!data || !data.positions || Object.keys(data.positions).length === 0) {
            this.showNoData('No position data available. Load a race session.');
            return;
        }

        const positions = data.positions;

        // Add grid
        this.addGrid(this.xScale, this.yScale);

        // Add axes
        this.addXAxis(this.xScale, { label: 'Lap' });
        this.addYAxis(this.yScale, {
            label: 'Position',
            ticks: 10,
        });

        // Draw position lines for each driver
        const line = d3.line()
            .x(d => this.xScale(d.lap))
            .y(d => this.yScale(d.position))
            .curve(d3.curveStepAfter);

        Object.entries(positions).forEach(([driver, posData], index) => {
            if (posData.length === 0) return;

            const color = getDriverColor(driver, this.year);
            const sortedData = posData.sort((a, b) => a.lap - b.lap);

            // Draw line
            this.chartGroup
                .append('path')
                .datum(sortedData)
                .attr('class', 'position-line data-element')
                .attr('d', line)
                .attr('stroke', color)
                .attr('fill', 'none')
                .attr('stroke-width', 2)
                .attr('opacity', 0.8);

            // Draw dots at key points (start, end, and position changes)
            const keyPoints = this.getKeyPoints(sortedData);
            keyPoints.forEach(point => {
                this.chartGroup
                    .append('circle')
                    .attr('class', 'position-dot data-element')
                    .attr('cx', this.xScale(point.lap))
                    .attr('cy', this.yScale(point.position))
                    .attr('r', 4)
                    .attr('fill', color)
                    .attr('stroke', '#1a1a2e')
                    .attr('stroke-width', 1)
                    .on('mouseenter', (event) => this.handleMouseEnter(event, driver, point))
                    .on('mouseleave', () => this.hideTooltip());
            });
        });

        // Add legend
        this.addLegend(Object.keys(positions));
    }

    getKeyPoints(data) {
        if (data.length === 0) return [];

        const points = [data[0]]; // Start point
        let lastPos = data[0].position;

        // Add position change points
        for (let i = 1; i < data.length; i++) {
            if (data[i].position !== lastPos) {
                points.push(data[i]);
                lastPos = data[i].position;
            }
        }

        // Add end point
        if (data.length > 1) {
            points.push(data[data.length - 1]);
        }

        return points;
    }

    handleMouseEnter(event, driver, point) {
        const content = `
            <div class="tooltip-title">${driver}</div>
            <div class="tooltip-content">
                <div class="tooltip-row">
                    <span class="tooltip-label">Lap:</span>
                    <span class="tooltip-value">${point.lap}</span>
                </div>
                <div class="tooltip-row">
                    <span class="tooltip-label">Position:</span>
                    <span class="tooltip-value">P${point.position}</span>
                </div>
            </div>
        `;
        this.showTooltip(event, content);
    }

    addLegend(drivers) {
        const legend = this.chartGroup
            .append('g')
            .attr('class', 'legend')
            .attr('transform', `translate(${this.width + 10}, 0)`);

        drivers.slice(0, 20).forEach((driver, i) => {
            const color = getDriverColor(driver, this.year);
            const g = legend.append('g')
                .attr('transform', `translate(0, ${i * 18})`);

            g.append('line')
                .attr('x1', 0)
                .attr('x2', 15)
                .attr('y1', 6)
                .attr('y2', 6)
                .attr('stroke', color)
                .attr('stroke-width', 2);

            g.append('text')
                .attr('x', 20)
                .attr('y', 10)
                .attr('fill', '#eaeaea')
                .attr('font-size', '10px')
                .text(driver);
        });
    }
}

export default PositionChart;
