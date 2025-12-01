/**
 * Multi-Channel Telemetry Chart
 * Shows Speed, Throttle/Brake, RPM, Gear, DRS, and Delta in synchronized panels
 */

import { BaseChart } from './base-chart.js';
import { formatSpeed, formatDelta } from '../utils/formatters.js';
import { getDriverColor } from '../utils/colors.js';

export class MultiTelemetryChart extends BaseChart {
    constructor(container, options = {}) {
        super(container, {
            margin: { top: 20, right: 80, bottom: 30, left: 60 },
            ...options,
        });

        this.channels = ['speed', 'delta', 'throttle', 'rpm', 'gear', 'drs'];
        this.channelHeights = {
            speed: 0.35,
            delta: 0.15,
            throttle: 0.15,
            rpm: 0.15,
            gear: 0.1,
            drs: 0.1,
        };
        this.xScale = null;
        this.channelScales = {};
        this.referenceLap = null;
        this.year = options.year || 2025;
    }

    setYear(year) {
        this.year = year;
    }

    getColor(lap, index) {
        return getDriverColor(lap.driver_id, this.year);
    }

    setupScales(data) {
        if (!data || !data.laps || data.laps.length === 0) return;

        const allPoints = data.laps.flatMap(l => l.telemetry || []);
        const maxDistance = d3.max(allPoints, d => d.distance) || 5000;

        // X: Distance (shared across all channels)
        this.xScale = d3.scaleLinear()
            .domain([0, maxDistance])
            .range([0, this.width]);

        // Calculate channel heights
        let yOffset = 0;
        const padding = 10;

        this.channels.forEach(channel => {
            const channelHeight = this.height * this.channelHeights[channel] - padding;
            const domain = this.getChannelDomain(channel, allPoints);

            this.channelScales[channel] = {
                y: d3.scaleLinear()
                    .domain(domain)
                    .range([yOffset + channelHeight, yOffset]),
                height: channelHeight,
                offset: yOffset,
            };

            yOffset += channelHeight + padding;
        });

        // Set reference lap for delta calculation (first lap)
        if (data.laps.length > 0) {
            this.referenceLap = data.laps[0];
        }
    }

    getChannelDomain(channel, points) {
        switch (channel) {
            case 'speed':
                return [0, (d3.max(points, d => d.speed) || 350) * 1.05];
            case 'delta':
                return [-2, 2]; // +/- 2 seconds
            case 'throttle':
                return [0, 100];
            case 'rpm':
                return [0, (d3.max(points, d => d.rpm) || 15000) * 1.05];
            case 'gear':
                return [0, 8];
            case 'drs':
                return [0, 1];
            default:
                return [0, 100];
        }
    }

    render(data) {
        if (!data || !data.laps || data.laps.length === 0) {
            this.showNoData('No telemetry data available. Select drivers and laps to compare.');
            return;
        }

        // Draw each channel
        this.channels.forEach(channel => {
            this.drawChannel(channel, data);
        });

        // Add interactive crosshair
        this.addCrosshair(data);

        // Add legend
        this.addLegend(data.laps);
    }

    drawChannel(channel, data) {
        const scale = this.channelScales[channel];
        const g = this.chartGroup
            .append('g')
            .attr('class', `channel-${channel} data-element`)
            .attr('transform', `translate(0, 0)`);

        // Background
        g.append('rect')
            .attr('x', 0)
            .attr('y', scale.offset)
            .attr('width', this.width)
            .attr('height', scale.height)
            .attr('fill', '#1f2940')
            .attr('opacity', 0.5);

        // Channel label
        g.append('text')
            .attr('x', -5)
            .attr('y', scale.offset + 12)
            .attr('text-anchor', 'end')
            .attr('fill', '#8892a0')
            .attr('font-size', '10px')
            .attr('font-weight', 'bold')
            .text(this.getChannelLabel(channel));

        // Y axis for this channel
        const axis = d3.axisLeft(scale.y).ticks(3);
        if (channel === 'gear') {
            axis.tickValues([1, 2, 3, 4, 5, 6, 7, 8]);
        }
        if (channel === 'drs') {
            axis.tickValues([0, 1]).tickFormat(d => d === 1 ? 'ON' : 'OFF');
        }

        g.append('g')
            .attr('class', 'axis')
            .call(axis)
            .selectAll('text')
            .attr('fill', '#8892a0')
            .attr('font-size', '9px');

        // Draw data for each lap
        data.laps.forEach((lap, i) => {
            if (!lap.telemetry || lap.telemetry.length === 0) return;
            this.drawChannelData(g, channel, lap, i, data);
        });
    }

    drawChannelData(g, channel, lap, index, data) {
        const scale = this.channelScales[channel];
        const color = this.getColor(lap, index);

        const getValue = (point) => {
            switch (channel) {
                case 'speed': return point.speed;
                case 'throttle': return point.throttle;
                case 'rpm': return point.rpm;
                case 'gear': return point.gear;
                case 'drs': return point.drs ? 1 : 0;
                case 'delta': return this.calculateDelta(point, lap, data);
                default: return 0;
            }
        };

        if (channel === 'throttle') {
            // Draw throttle as area
            const area = d3.area()
                .x(d => this.xScale(d.distance))
                .y0(scale.y(0))
                .y1(d => scale.y(getValue(d)))
                .curve(d3.curveMonotoneX);

            g.append('path')
                .datum(lap.telemetry)
                .attr('fill', color)
                .attr('fill-opacity', 0.3)
                .attr('d', area);

            // Draw brake overlay (inverted, from bottom)
            const brakeArea = d3.area()
                .x(d => this.xScale(d.distance))
                .y0(scale.y(0))
                .y1(d => scale.y(d.brake ? 100 : 0))
                .curve(d3.curveMonotoneX);

            g.append('path')
                .datum(lap.telemetry)
                .attr('fill', '#e94560')
                .attr('fill-opacity', 0.5)
                .attr('d', brakeArea);

        } else if (channel === 'drs') {
            // Draw DRS as rectangles
            let drsStart = null;
            lap.telemetry.forEach((point, i) => {
                const drsOn = point.drs && point.drs > 0;
                if (drsOn && drsStart === null) {
                    drsStart = point.distance;
                } else if (!drsOn && drsStart !== null) {
                    g.append('rect')
                        .attr('x', this.xScale(drsStart))
                        .attr('y', scale.offset)
                        .attr('width', this.xScale(point.distance) - this.xScale(drsStart))
                        .attr('height', scale.height)
                        .attr('fill', color)
                        .attr('opacity', 0.5);
                    drsStart = null;
                }
            });
        } else if (channel === 'gear') {
            // Draw gear as step line
            const line = d3.line()
                .x(d => this.xScale(d.distance))
                .y(d => scale.y(getValue(d)))
                .curve(d3.curveStepAfter);

            g.append('path')
                .datum(lap.telemetry)
                .attr('stroke', color)
                .attr('stroke-width', 2)
                .attr('fill', 'none')
                .attr('d', line);
        } else {
            // Draw as line
            const line = d3.line()
                .x(d => this.xScale(d.distance))
                .y(d => scale.y(getValue(d)))
                .curve(d3.curveMonotoneX);

            g.append('path')
                .datum(lap.telemetry)
                .attr('stroke', color)
                .attr('stroke-width', 2)
                .attr('fill', 'none')
                .attr('d', line);

            // For delta, add zero line
            if (channel === 'delta') {
                g.append('line')
                    .attr('x1', 0)
                    .attr('x2', this.width)
                    .attr('y1', scale.y(0))
                    .attr('y2', scale.y(0))
                    .attr('stroke', '#8892a0')
                    .attr('stroke-dasharray', '4,4')
                    .attr('opacity', 0.5);
            }
        }
    }

    calculateDelta(point, lap, data) {
        if (!this.referenceLap || !this.referenceLap.telemetry) return 0;
        if (lap === this.referenceLap) return 0;

        // Find corresponding point in reference lap by distance
        const refPoint = this.referenceLap.telemetry.reduce((prev, curr) =>
            Math.abs(curr.distance - point.distance) < Math.abs(prev.distance - point.distance)
                ? curr : prev
        );

        // Calculate time delta (simplified - based on speed difference)
        // In reality this would need accumulated time data
        if (point.time_ms && refPoint.time_ms) {
            return (point.time_ms - refPoint.time_ms) / 1000;
        }

        // Estimate from speed (lower speed = behind)
        const speedDiff = refPoint.speed - point.speed;
        return speedDiff * 0.01; // Rough approximation
    }

    getChannelLabel(channel) {
        const labels = {
            speed: 'SPEED',
            delta: 'DELTA',
            throttle: 'THROT/BRK',
            rpm: 'RPM',
            gear: 'GEAR',
            drs: 'DRS',
        };
        return labels[channel] || channel.toUpperCase();
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
            .attr('stroke', '#fff')
            .attr('stroke-width', 1)
            .attr('stroke-dasharray', '4,4')
            .attr('opacity', 0.7);

        // Value labels group
        const valuesGroup = crosshairGroup.append('g')
            .attr('class', 'crosshair-values');

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

        // Update value labels
        const valuesGroup = crosshairGroup.select('.crosshair-values');
        valuesGroup.selectAll('*').remove();

        // Distance label
        valuesGroup.append('text')
            .attr('x', mouseX + 5)
            .attr('y', 12)
            .attr('fill', '#fff')
            .attr('font-size', '10px')
            .text(`${Math.round(distance)}m`);

        // Show values for each lap at this distance
        data.laps.forEach((lap, i) => {
            if (!lap.telemetry || lap.telemetry.length === 0) return;

            const point = lap.telemetry.reduce((prev, curr) =>
                Math.abs(curr.distance - distance) < Math.abs(prev.distance - distance)
                    ? curr : prev
            );

            const color = this.getColor(lap, i);
            const speedScale = this.channelScales.speed;

            // Point marker on speed chart
            valuesGroup.append('circle')
                .attr('cx', mouseX)
                .attr('cy', speedScale.y(point.speed))
                .attr('r', 5)
                .attr('fill', color)
                .attr('stroke', '#fff')
                .attr('stroke-width', 2);

            // Value text
            valuesGroup.append('text')
                .attr('x', this.width + 5)
                .attr('y', speedScale.offset + 15 + i * 45)
                .attr('fill', color)
                .attr('font-size', '11px')
                .attr('font-weight', 'bold')
                .text(lap.driver_id);

            valuesGroup.append('text')
                .attr('x', this.width + 5)
                .attr('y', speedScale.offset + 28 + i * 45)
                .attr('fill', color)
                .attr('font-size', '10px')
                .text(`${Math.round(point.speed)} km/h`);

            valuesGroup.append('text')
                .attr('x', this.width + 5)
                .attr('y', speedScale.offset + 40 + i * 45)
                .attr('fill', color)
                .attr('font-size', '10px')
                .text(`G${point.gear} ${point.throttle}% ${point.brake ? 'BRK' : ''}`);
        });
    }

    addLegend(laps) {
        // Position legend at the top-right corner, inside the chart margin area
        const legendWidth = laps.length * 85;
        const legend = this.svg
            .append('g')
            .attr('class', 'legend')
            .attr('transform', `translate(${this.options.margin.left + this.width - legendWidth + 10}, ${this.options.margin.top - 5})`);

        laps.forEach((lap, i) => {
            const color = this.getColor(lap, i);
            const g = legend.append('g')
                .attr('transform', `translate(${i * 90}, 0)`);

            g.append('line')
                .attr('x1', 0)
                .attr('x2', 16)
                .attr('y1', 6)
                .attr('y2', 6)
                .attr('stroke', color)
                .attr('stroke-width', 3);

            g.append('text')
                .attr('x', 20)
                .attr('y', 10)
                .attr('fill', '#eaeaea')
                .attr('font-size', '11px')
                .text(`${lap.driver_id} L${lap.lap_number}`);
        });
    }

    setReferenceLap(lap) {
        this.referenceLap = lap;
        if (this._lastData) {
            this.update(this._lastData);
        }
    }
}

export default MultiTelemetryChart;
