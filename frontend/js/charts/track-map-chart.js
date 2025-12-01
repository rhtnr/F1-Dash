/**
 * Track Map Chart
 * Shows track layout with driver position and telemetry data
 */

import { BaseChart } from './base-chart.js';
import { getDriverColor } from '../utils/colors.js';

export class TrackMapChart extends BaseChart {
    constructor(container, options = {}) {
        super(container, {
            margin: { top: 20, right: 20, bottom: 20, left: 20 },
            ...options,
        });

        this.xScale = null;
        this.yScale = null;
        this.year = options.year || 2025;
        this.turnMarkers = [];
    }

    setYear(year) {
        this.year = year;
    }

    getColor(lap, index) {
        return getDriverColor(lap.driver_id, this.year);
    }

    setupScales(data) {
        if (!data || !data.laps || data.laps.length === 0) return;

        // Get all position data from all laps
        const allPoints = data.laps.flatMap(l =>
            (l.telemetry || []).filter(p => p.x != null && p.y != null)
        );

        if (allPoints.length === 0) return;

        const xExtent = d3.extent(allPoints, d => d.x);
        const yExtent = d3.extent(allPoints, d => d.y);

        // Calculate aspect ratio
        const dataWidth = xExtent[1] - xExtent[0];
        const dataHeight = yExtent[1] - yExtent[0];
        const dataAspect = dataWidth / dataHeight;
        const chartAspect = this.width / this.height;

        let scale;
        if (dataAspect > chartAspect) {
            // Data is wider, fit to width
            scale = this.width / dataWidth;
        } else {
            // Data is taller, fit to height
            scale = this.height / dataHeight;
        }

        // Center the track
        const offsetX = (this.width - dataWidth * scale) / 2;
        const offsetY = (this.height - dataHeight * scale) / 2;

        this.xScale = d3.scaleLinear()
            .domain(xExtent)
            .range([offsetX, offsetX + dataWidth * scale]);

        this.yScale = d3.scaleLinear()
            .domain(yExtent)
            .range([this.height - offsetY, offsetY]); // Invert Y for proper orientation
    }

    render(data) {
        if (!data || !data.laps || data.laps.length === 0) {
            this.showNoData('No track data available');
            return;
        }

        // Check if we have position data
        const hasPositionData = data.laps.some(l =>
            (l.telemetry || []).some(p => p.x != null && p.y != null)
        );

        if (!hasPositionData) {
            this.showNoData('Track position data not available for this session');
            return;
        }

        // Draw track outline from first lap
        const firstLap = data.laps.find(l =>
            (l.telemetry || []).some(p => p.x != null && p.y != null)
        );

        if (firstLap && firstLap.telemetry) {
            this.drawTrackOutline(firstLap.telemetry);
            this.detectAndDrawTurns(firstLap.telemetry);
        }

        // Draw each lap's telemetry as colored overlay
        data.laps.forEach((lap, i) => {
            if (!lap.telemetry || lap.telemetry.length === 0) return;
            this.drawLapTrace(lap, i, data.selectedDistance);
        });

        // Add legend
        this.addLegend(data.laps);

        // Add distance indicator if provided
        if (data.selectedDistance != null) {
            this.drawDistanceMarker(data);
        }
    }

    drawTrackOutline(telemetry) {
        const points = telemetry.filter(p => p.x != null && p.y != null);
        if (points.length === 0) return;

        const line = d3.line()
            .x(d => this.xScale(d.x))
            .y(d => this.yScale(d.y))
            .curve(d3.curveCardinal.tension(0.5));

        // Draw track background (wider, darker line)
        this.chartGroup
            .append('path')
            .datum(points)
            .attr('class', 'track-outline data-element')
            .attr('d', line)
            .attr('stroke', '#3d4a5c')
            .attr('stroke-width', 12)
            .attr('fill', 'none')
            .attr('stroke-linecap', 'round')
            .attr('stroke-linejoin', 'round');

        // Draw track center (thinner, lighter line)
        this.chartGroup
            .append('path')
            .datum(points)
            .attr('class', 'track-center data-element')
            .attr('d', line)
            .attr('stroke', '#5a6a7a')
            .attr('stroke-width', 6)
            .attr('fill', 'none')
            .attr('stroke-linecap', 'round')
            .attr('stroke-linejoin', 'round');
    }

    detectAndDrawTurns(telemetry) {
        const points = telemetry.filter(p => p.x != null && p.y != null && p.speed != null);
        if (points.length < 10) return;

        // Find local speed minima (corners)
        const turns = [];
        const windowSize = 20;
        const speedThreshold = 0.85; // Points slower than 85% of surrounding speeds

        for (let i = windowSize; i < points.length - windowSize; i++) {
            const currentSpeed = points[i].speed;
            const surroundingSpeeds = [];

            for (let j = i - windowSize; j <= i + windowSize; j++) {
                if (j !== i) surroundingSpeeds.push(points[j].speed);
            }

            const avgSurrounding = surroundingSpeeds.reduce((a, b) => a + b, 0) / surroundingSpeeds.length;

            // Is this a local minimum and significantly slower?
            if (currentSpeed < avgSurrounding * speedThreshold) {
                // Check if this is the minimum in the immediate vicinity
                let isMinimum = true;
                for (let j = i - 5; j <= i + 5; j++) {
                    if (j !== i && j >= 0 && j < points.length && points[j].speed < currentSpeed) {
                        isMinimum = false;
                        break;
                    }
                }

                if (isMinimum) {
                    // Avoid duplicates (turns too close together)
                    const lastTurn = turns[turns.length - 1];
                    if (!lastTurn || Math.abs(points[i].distance - lastTurn.distance) > 200) {
                        turns.push({
                            x: points[i].x,
                            y: points[i].y,
                            distance: points[i].distance,
                            speed: currentSpeed,
                            index: turns.length + 1
                        });
                    }
                }
            }
        }

        // Draw turn markers
        turns.forEach(turn => {
            const g = this.chartGroup
                .append('g')
                .attr('class', 'turn-marker data-element')
                .attr('transform', `translate(${this.xScale(turn.x)}, ${this.yScale(turn.y)})`);

            // Circle background
            g.append('circle')
                .attr('r', 12)
                .attr('fill', '#e94560')
                .attr('stroke', '#fff')
                .attr('stroke-width', 2);

            // Turn number
            g.append('text')
                .attr('text-anchor', 'middle')
                .attr('dominant-baseline', 'central')
                .attr('fill', '#fff')
                .attr('font-size', '10px')
                .attr('font-weight', 'bold')
                .text(turn.index);
        });

        this.turnMarkers = turns;
    }

    drawLapTrace(lap, index, selectedDistance) {
        const points = lap.telemetry.filter(p => p.x != null && p.y != null);
        if (points.length === 0) return;

        const color = this.getColor(lap, index);

        // Create gradient based on speed
        const gradientId = `speed-gradient-${index}`;
        const maxSpeed = d3.max(points, d => d.speed) || 350;
        const minSpeed = d3.min(points, d => d.speed) || 0;

        // Draw line segments with color based on speed
        const lineGenerator = d3.line()
            .x(d => this.xScale(d.x))
            .y(d => this.yScale(d.y))
            .curve(d3.curveCardinal.tension(0.5));

        // Draw trace line
        this.chartGroup
            .append('path')
            .datum(points)
            .attr('class', 'lap-trace data-element')
            .attr('d', lineGenerator)
            .attr('stroke', color)
            .attr('stroke-width', 3)
            .attr('fill', 'none')
            .attr('opacity', 0.8);
    }

    drawDistanceMarker(data) {
        const distance = data.selectedDistance;

        data.laps.forEach((lap, i) => {
            if (!lap.telemetry || lap.telemetry.length === 0) return;

            // Find point at this distance
            const point = lap.telemetry.reduce((prev, curr) =>
                Math.abs(curr.distance - distance) < Math.abs(prev.distance - distance)
                    ? curr : prev
            );

            if (point.x == null || point.y == null) return;

            const color = this.getColor(lap, i);

            // Draw position marker
            this.chartGroup
                .append('circle')
                .attr('class', 'position-marker data-element')
                .attr('cx', this.xScale(point.x))
                .attr('cy', this.yScale(point.y))
                .attr('r', 8)
                .attr('fill', color)
                .attr('stroke', '#fff')
                .attr('stroke-width', 2);
        });
    }

    addLegend(laps) {
        const legend = this.chartGroup
            .append('g')
            .attr('class', 'legend')
            .attr('transform', `translate(10, 10)`);

        laps.forEach((lap, i) => {
            const color = this.getColor(lap, i);
            const g = legend.append('g')
                .attr('transform', `translate(0, ${i * 20})`);

            g.append('line')
                .attr('x1', 0)
                .attr('x2', 20)
                .attr('y1', 0)
                .attr('y2', 0)
                .attr('stroke', color)
                .attr('stroke-width', 3);

            g.append('text')
                .attr('x', 25)
                .attr('y', 4)
                .attr('fill', '#eaeaea')
                .attr('font-size', '11px')
                .text(`${lap.driver_id} L${lap.lap_number}`);
        });
    }

    setSelectedDistance(distance) {
        if (this._lastData) {
            this._lastData.selectedDistance = distance;
            this.update(this._lastData);
        }
    }
}

export default TrackMapChart;
