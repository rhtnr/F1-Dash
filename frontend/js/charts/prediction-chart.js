/**
 * Race Prediction Chart
 * Displays predicted finishing order with practice session data
 */

import { BaseChart } from './base-chart.js';
import { DRIVER_COLORS } from '../utils/colors.js';

export class PredictionChart extends BaseChart {
    constructor(container, options = {}) {
        super(container, {
            margin: { top: 40, right: 200, bottom: 50, left: 70 },
            ...options,
        });

        this.xScale = null;
        this.yScale = null;
    }

    setupScales(data) {
        if (!data || !data.predictions || data.predictions.length === 0) return;

        const predictions = data.predictions;
        const drivers = predictions.map(p => p.driver);

        // Y: Drivers (predicted order)
        this.yScale = d3.scaleBand()
            .domain(drivers)
            .range([0, this.height])
            .padding(0.2);

        // X: Position (1-20)
        this.xScale = d3.scaleLinear()
            .domain([0, 20])
            .range([0, this.width]);
    }

    render(data) {
        if (!data || !data.predictions || data.predictions.length === 0) {
            this.showNoData('No predictions available. Select an event with practice sessions.');
            return;
        }

        const predictions = data.predictions;
        const hasActual = predictions.some(p => p.actual_position != null);

        // Add grid
        this.addGrid(this.xScale, this.yScale);

        // Add X axis at top
        this.chartGroup
            .append('g')
            .attr('class', 'x-axis')
            .call(d3.axisTop(this.xScale).ticks(20))
            .selectAll('text')
            .attr('fill', '#aaa')
            .attr('font-size', '10px');

        // X axis label
        this.chartGroup
            .append('text')
            .attr('class', 'x-label')
            .attr('x', this.width / 2)
            .attr('y', -25)
            .attr('text-anchor', 'middle')
            .attr('fill', '#aaa')
            .attr('font-size', '12px')
            .text('Position');

        // Draw bars for each prediction
        predictions.forEach((pred, index) => {
            this.drawPredictionRow(pred, index, hasActual);
        });

        // Add legend if we have actual results
        if (hasActual) {
            this.addLegend();
        }

        // Add metrics summary if available
        if (data.metrics) {
            this.addMetricsSummary(data.metrics);
        }
    }

    drawPredictionRow(pred, index, hasActual) {
        const y = this.yScale(pred.driver);
        const barHeight = this.yScale.bandwidth();
        const color = DRIVER_COLORS(pred.driver);

        const g = this.chartGroup
            .append('g')
            .attr('class', 'prediction-row data-element')
            .attr('transform', `translate(0, ${y})`);

        // Driver label
        g.append('text')
            .attr('class', 'driver-label')
            .attr('x', -10)
            .attr('y', barHeight / 2)
            .attr('text-anchor', 'end')
            .attr('dominant-baseline', 'middle')
            .attr('fill', color)
            .attr('font-size', '12px')
            .attr('font-weight', 'bold')
            .text(`${pred.rank}. ${pred.driver}`);

        // Predicted position marker
        const predictedX = this.xScale(pred.predicted_position);
        g.append('circle')
            .attr('class', 'predicted-marker')
            .attr('cx', predictedX)
            .attr('cy', barHeight / 2)
            .attr('r', 8)
            .attr('fill', color)
            .attr('fill-opacity', 0.8)
            .attr('stroke', '#fff')
            .attr('stroke-width', 2);

        // Actual position marker (if available)
        if (hasActual && pred.actual_position != null) {
            const actualX = this.xScale(pred.actual_position);

            // Draw line connecting predicted and actual
            g.append('line')
                .attr('class', 'position-line')
                .attr('x1', predictedX)
                .attr('y1', barHeight / 2)
                .attr('x2', actualX)
                .attr('y2', barHeight / 2)
                .attr('stroke', pred.position_error <= 3 ? '#4ade80' : '#f87171')
                .attr('stroke-width', 2)
                .attr('stroke-dasharray', '4,4');

            // Actual position diamond
            const diamond = d3.symbol().type(d3.symbolDiamond).size(100);
            g.append('path')
                .attr('class', 'actual-marker')
                .attr('d', diamond)
                .attr('transform', `translate(${actualX}, ${barHeight / 2})`)
                .attr('fill', pred.position_error <= 3 ? '#4ade80' : '#f87171')
                .attr('stroke', '#fff')
                .attr('stroke-width', 1);

            // Error badge
            const errorColor = pred.position_error === 0 ? '#4ade80' :
                              pred.position_error <= 3 ? '#fbbf24' : '#f87171';
            g.append('text')
                .attr('class', 'error-badge')
                .attr('x', this.width + 10)
                .attr('y', barHeight / 2)
                .attr('dominant-baseline', 'middle')
                .attr('fill', errorColor)
                .attr('font-size', '11px')
                .text(`${pred.position_error === 0 ? 'Exact' : (pred.position_error > 0 ? '+' : '') + pred.position_error}`);
        }

        // Practice session positions tooltip
        const fpInfo = [];
        if (pred.fp1_position) fpInfo.push(`FP1: P${pred.fp1_position}`);
        if (pred.fp2_position) fpInfo.push(`FP2: P${pred.fp2_position}`);
        if (pred.fp3_position) fpInfo.push(`FP3: P${pred.fp3_position}`);

        if (fpInfo.length > 0) {
            g.append('text')
                .attr('class', 'fp-info')
                .attr('x', this.width + 50)
                .attr('y', barHeight / 2)
                .attr('dominant-baseline', 'middle')
                .attr('fill', '#888')
                .attr('font-size', '10px')
                .text(fpInfo.join(' | '));
        }

        // Hover effect
        g.on('mouseenter', (event) => this.handleMouseEnter(event, pred))
         .on('mouseleave', () => this.hideTooltip());
    }

    addLegend() {
        const legend = this.chartGroup
            .append('g')
            .attr('class', 'legend')
            .attr('transform', `translate(${this.width + 10}, ${this.height - 60})`);

        // Predicted marker
        legend.append('circle')
            .attr('cx', 10)
            .attr('cy', 10)
            .attr('r', 6)
            .attr('fill', '#888');

        legend.append('text')
            .attr('x', 25)
            .attr('y', 14)
            .attr('fill', '#aaa')
            .attr('font-size', '10px')
            .text('Predicted');

        // Actual marker
        const diamond = d3.symbol().type(d3.symbolDiamond).size(60);
        legend.append('path')
            .attr('d', diamond)
            .attr('transform', 'translate(10, 30)')
            .attr('fill', '#4ade80');

        legend.append('text')
            .attr('x', 25)
            .attr('y', 34)
            .attr('fill', '#aaa')
            .attr('font-size', '10px')
            .text('Actual');
    }

    addMetricsSummary(metrics) {
        const summary = this.chartGroup
            .append('g')
            .attr('class', 'metrics-summary')
            .attr('transform', `translate(${this.width + 10}, 0)`);

        const items = [
            { label: 'MAE', value: `${metrics.mae.toFixed(2)} pos` },
            { label: 'Within 3 pos', value: `${metrics.within_3_positions.toFixed(0)}%` },
            { label: 'Podium', value: `${metrics.podium_correct}/3` },
            { label: 'Winner', value: metrics.winner_correct ? 'Yes' : 'No' },
        ];

        items.forEach((item, i) => {
            summary.append('text')
                .attr('x', 0)
                .attr('y', i * 18)
                .attr('fill', '#aaa')
                .attr('font-size', '10px')
                .text(`${item.label}: `);

            summary.append('text')
                .attr('x', 80)
                .attr('y', i * 18)
                .attr('fill', item.label === 'Winner' ?
                    (metrics.winner_correct ? '#4ade80' : '#f87171') : '#fff')
                .attr('font-size', '10px')
                .attr('font-weight', 'bold')
                .text(item.value);
        });
    }

    handleMouseEnter(event, pred) {
        const content = `
            <div class="tooltip-title">${pred.driver}</div>
            <div class="tooltip-content">
                <div class="tooltip-row">
                    <span class="tooltip-label">Predicted:</span>
                    <span class="tooltip-value">P${pred.rank} (${pred.predicted_position.toFixed(1)})</span>
                </div>
                ${pred.actual_position != null ? `
                <div class="tooltip-row">
                    <span class="tooltip-label">Actual:</span>
                    <span class="tooltip-value">P${pred.actual_position}</span>
                </div>
                <div class="tooltip-row">
                    <span class="tooltip-label">Error:</span>
                    <span class="tooltip-value" style="color: ${pred.position_error <= 3 ? '#4ade80' : '#f87171'}">
                        ${pred.position_error} positions
                    </span>
                </div>
                ` : ''}
                <div class="tooltip-section">
                    <div class="tooltip-subtitle">Practice Sessions</div>
                    ${pred.fp1_position ? `
                    <div class="tooltip-row">
                        <span class="tooltip-label">FP1:</span>
                        <span class="tooltip-value">P${pred.fp1_position} (+${pred.fp1_best_delta?.toFixed(3) || '-'}s)</span>
                    </div>` : ''}
                    ${pred.fp2_position ? `
                    <div class="tooltip-row">
                        <span class="tooltip-label">FP2:</span>
                        <span class="tooltip-value">P${pred.fp2_position} (+${pred.fp2_best_delta?.toFixed(3) || '-'}s)</span>
                    </div>` : ''}
                    ${pred.fp3_position ? `
                    <div class="tooltip-row">
                        <span class="tooltip-label">FP3:</span>
                        <span class="tooltip-value">P${pred.fp3_position} (+${pred.fp3_best_delta?.toFixed(3) || '-'}s)</span>
                    </div>` : ''}
                </div>
            </div>
        `;
        this.showTooltip(event, content);
    }
}

export default PredictionChart;
