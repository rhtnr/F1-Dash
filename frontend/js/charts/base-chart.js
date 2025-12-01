/**
 * Base Chart Class
 * Provides common functionality for all D3.js charts
 */

export class BaseChart {
    constructor(container, options = {}) {
        this.container = d3.select(container);
        this.options = {
            margin: { top: 20, right: 30, bottom: 40, left: 60 },
            ...options,
        };

        this.svg = null;
        this.chartGroup = null;
        this.tooltip = null;
        this.width = 0;
        this.height = 0;
    }

    /**
     * Initialize the chart
     */
    init() {
        // Clear existing content
        this.container.selectAll('*').remove();

        // Get container dimensions
        const rect = this.container.node().getBoundingClientRect();
        const totalWidth = rect.width || 800;
        const totalHeight = rect.height || 400;

        this.width = totalWidth - this.options.margin.left - this.options.margin.right;
        this.height = totalHeight - this.options.margin.top - this.options.margin.bottom;

        // Create SVG
        this.svg = this.container
            .append('svg')
            .attr('width', totalWidth)
            .attr('height', totalHeight)
            .attr('viewBox', `0 0 ${totalWidth} ${totalHeight}`)
            .attr('preserveAspectRatio', 'xMidYMid meet');

        // Create chart group with margins
        this.chartGroup = this.svg
            .append('g')
            .attr('transform', `translate(${this.options.margin.left},${this.options.margin.top})`);

        // Create tooltip
        this.createTooltip();

        return this;
    }

    /**
     * Create tooltip element
     */
    createTooltip() {
        // Remove existing tooltip
        d3.select('body').selectAll('.tooltip').remove();

        this.tooltip = d3.select('body')
            .append('div')
            .attr('class', 'tooltip')
            .style('opacity', 0);
    }

    /**
     * Show tooltip
     */
    showTooltip(event, content) {
        this.tooltip
            .html(content)
            .style('opacity', 1)
            .style('left', `${event.pageX + 10}px`)
            .style('top', `${event.pageY - 10}px`);
    }

    /**
     * Hide tooltip
     */
    hideTooltip() {
        this.tooltip.style('opacity', 0);
    }

    /**
     * Add X axis
     */
    addXAxis(scale, options = {}) {
        const {
            label = '',
            tickFormat = null,
            ticks = null,
        } = options;

        const axis = d3.axisBottom(scale);
        if (tickFormat) axis.tickFormat(tickFormat);
        if (ticks) axis.ticks(ticks);

        this.chartGroup
            .append('g')
            .attr('class', 'x-axis axis')
            .attr('transform', `translate(0,${this.height})`)
            .call(axis);

        if (label) {
            this.chartGroup
                .append('text')
                .attr('class', 'axis-label')
                .attr('x', this.width / 2)
                .attr('y', this.height + 35)
                .attr('text-anchor', 'middle')
                .text(label);
        }
    }

    /**
     * Add Y axis
     */
    addYAxis(scale, options = {}) {
        const {
            label = '',
            tickFormat = null,
            ticks = null,
        } = options;

        const axis = d3.axisLeft(scale);
        if (tickFormat) axis.tickFormat(tickFormat);
        if (ticks) axis.ticks(ticks);

        this.chartGroup
            .append('g')
            .attr('class', 'y-axis axis')
            .call(axis);

        if (label) {
            this.chartGroup
                .append('text')
                .attr('class', 'axis-label')
                .attr('transform', 'rotate(-90)')
                .attr('x', -this.height / 2)
                .attr('y', -45)
                .attr('text-anchor', 'middle')
                .text(label);
        }
    }

    /**
     * Add grid lines
     */
    addGrid(xScale, yScale, options = {}) {
        const { showX = true, showY = true } = options;

        if (showY) {
            this.chartGroup
                .append('g')
                .attr('class', 'grid')
                .call(
                    d3.axisLeft(yScale)
                        .tickSize(-this.width)
                        .tickFormat('')
                );
        }

        if (showX) {
            this.chartGroup
                .append('g')
                .attr('class', 'grid')
                .attr('transform', `translate(0,${this.height})`)
                .call(
                    d3.axisBottom(xScale)
                        .tickSize(-this.height)
                        .tickFormat('')
                );
        }
    }

    /**
     * Show no data message
     */
    showNoData(message = 'No data available') {
        this.chartGroup
            .append('text')
            .attr('class', 'no-data-message')
            .attr('x', this.width / 2)
            .attr('y', this.height / 2)
            .text(message);
    }

    /**
     * Clear chart content (preserve axes setup)
     */
    clear() {
        if (this.chartGroup) {
            this.chartGroup.selectAll('.data-element').remove();
        }
    }

    /**
     * Destroy the chart
     */
    destroy() {
        if (this.svg) {
            this.svg.remove();
        }
        if (this.tooltip) {
            this.tooltip.remove();
        }
    }

    /**
     * Resize the chart
     */
    resize() {
        this.init();
        if (this._lastData) {
            this.render(this._lastData);
        }
    }

    /**
     * Abstract methods - must be implemented by subclasses
     */
    setupScales(data) {
        throw new Error('setupScales() must be implemented');
    }

    render(data) {
        throw new Error('render() must be implemented');
    }

    /**
     * Update chart with new data
     */
    update(data) {
        this._lastData = data;
        this.init();
        this.setupScales(data);
        this.render(data);
    }
}

export default BaseChart;
