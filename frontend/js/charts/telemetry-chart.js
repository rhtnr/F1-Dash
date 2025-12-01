/**
 * Telemetry Chart
 * Speed trace and throttle/brake visualization
 */

import { BaseChart } from './base-chart.js';
import { formatSpeed, formatLapTime } from '../utils/formatters.js';
import { getDriverColor } from '../utils/colors.js';

export class TelemetryChart extends BaseChart {
    constructor(container, options = {}) {
        super(container, {
            margin: { top: 30, right: 80, bottom: 50, left: 70 },
            ...options,
        });

        this.xScale = null;
        this.ySpeedScale = null;
        this.year = options.year || 2025;
    }

    setYear(year) {
        this.year = year;
    }

    getColor(lap, index) {
        // Use driver's team color
        return getDriverColor(lap.driver_id, this.year);
    }

    setupScales(data) {
        if (!data || !data.laps || data.laps.length === 0) return;

        // Get max distance from all laps
        const allPoints = data.laps.flatMap(l => l.telemetry || []);
        const maxDistance = d3.max(allPoints, d => d.distance) || 5000;
        const maxSpeed = d3.max(allPoints, d => d.speed) || 350;

        // X: Distance
        this.xScale = d3.scaleLinear()
            .domain([0, maxDistance])
            .range([0, this.width]);

        // Y: Speed
        this.ySpeedScale = d3.scaleLinear()
            .domain([0, maxSpeed * 1.05])
            .range([this.height, 0]);
    }

    render(data) {
        if (!data || !data.laps || data.laps.length === 0) {
            this.showNoData('No telemetry data available. Select drivers and laps to compare.');
            return;
        }

        // Add grid
        this.addGrid(this.xScale, this.ySpeedScale);

        // Add axes
        this.addXAxis(this.xScale, {
            label: 'Distance (m)',
            tickFormat: d => d >= 1000 ? `${d/1000}km` : d,
        });
        this.addYAxis(this.ySpeedScale, {
            label: 'Speed (km/h)',
        });

        // Draw speed traces
        const line = d3.line()
            .x(d => this.xScale(d.distance))
            .y(d => this.ySpeedScale(d.speed))
            .curve(d3.curveMonotoneX);

        data.laps.forEach((lap, i) => {
            if (!lap.telemetry || lap.telemetry.length === 0) return;

            const color = this.getColor(lap, i);

            // Speed line
            this.chartGroup
                .append('path')
                .datum(lap.telemetry)
                .attr('class', 'speed-line data-element')
                .attr('d', line)
                .attr('stroke', color)
                .attr('fill', 'none')
                .attr('stroke-width', 2);
        });

        // Add legend
        this.addLegend(data.laps);

        // Add interactive crosshair
        this.addCrosshair(data);
    }

    addLegend(laps) {
        const legend = this.chartGroup
            .append('g')
            .attr('class', 'legend')
            .attr('transform', `translate(${this.width + 10}, 0)`);

        laps.forEach((lap, i) => {
            const color = this.getColor(lap, i);
            const g = legend.append('g')
                .attr('transform', `translate(0, ${i * 25})`);

            g.append('line')
                .attr('x1', 0)
                .attr('x2', 20)
                .attr('y1', 6)
                .attr('y2', 6)
                .attr('stroke', color)
                .attr('stroke-width', 2);

            g.append('text')
                .attr('x', 25)
                .attr('y', 10)
                .attr('fill', '#eaeaea')
                .attr('font-size', '11px')
                .text(`${lap.driver_id} L${lap.lap_number}`);
        });
    }

    addCrosshair(data) {
        const crosshairGroup = this.chartGroup
            .append('g')
            .attr('class', 'crosshair')
            .style('display', 'none');

        // Vertical line
        crosshairGroup.append('line')
            .attr('class', 'crosshair-line')
            .attr('y1', 0)
            .attr('y2', this.height)
            .attr('stroke', '#8892a0')
            .attr('stroke-dasharray', '4,4');

        // Value labels
        const labels = crosshairGroup.append('g')
            .attr('class', 'crosshair-labels');

        // Overlay for mouse events
        this.chartGroup.append('rect')
            .attr('class', 'overlay')
            .attr('width', this.width)
            .attr('height', this.height)
            .attr('fill', 'none')
            .attr('pointer-events', 'all')
            .on('mousemove', (event) => this.handleMouseMove(event, data, crosshairGroup))
            .on('mouseout', () => crosshairGroup.style('display', 'none'));
    }

    handleMouseMove(event, data, crosshairGroup) {
        const [mouseX] = d3.pointer(event);
        const distance = this.xScale.invert(mouseX);

        crosshairGroup.style('display', null);
        crosshairGroup.select('.crosshair-line')
            .attr('x1', mouseX)
            .attr('x2', mouseX);

        // Find nearest points for each lap
        const labels = crosshairGroup.select('.crosshair-labels');
        labels.selectAll('*').remove();

        data.laps.forEach((lap, i) => {
            if (!lap.telemetry || lap.telemetry.length === 0) return;

            // Find closest point
            const point = lap.telemetry.reduce((prev, curr) =>
                Math.abs(curr.distance - distance) < Math.abs(prev.distance - distance)
                    ? curr : prev
            );

            const color = this.getColor(lap, i);
            const y = this.ySpeedScale(point.speed);

            // Point marker
            labels.append('circle')
                .attr('cx', mouseX)
                .attr('cy', y)
                .attr('r', 5)
                .attr('fill', color)
                .attr('stroke', '#1a1a2e')
                .attr('stroke-width', 2);

            // Value label
            labels.append('text')
                .attr('x', mouseX + 10)
                .attr('y', y + (i * 15) - 5)
                .attr('fill', color)
                .attr('font-size', '11px')
                .text(`${lap.driver_id}: ${Math.round(point.speed)} km/h`);
        });
    }
}

export default TelemetryChart;
