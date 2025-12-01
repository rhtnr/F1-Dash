/**
 * Security utilities for safe DOM manipulation
 * Prevents XSS attacks by escaping HTML and using safe DOM methods
 */

/**
 * Escape HTML special characters to prevent XSS
 * @param {string} text - The text to escape
 * @returns {string} - Escaped text safe for HTML insertion
 */
export function escapeHtml(text) {
    if (text === null || text === undefined) {
        return '';
    }
    const str = String(text);
    const htmlEscapes = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
        '/': '&#x2F;',
    };
    return str.replace(/[&<>"'/]/g, char => htmlEscapes[char]);
}

/**
 * Create a text node (automatically safe from XSS)
 * @param {string} text - The text content
 * @returns {Text} - A text node
 */
export function createTextNode(text) {
    return document.createTextNode(text ?? '');
}

/**
 * Safely set text content of an element
 * @param {HTMLElement} element - The element
 * @param {string} text - The text to set
 */
export function setTextContent(element, text) {
    if (element) {
        element.textContent = text ?? '';
    }
}

/**
 * Create an option element safely
 * @param {string} value - The option value
 * @param {string} text - The display text
 * @param {boolean} selected - Whether the option is selected
 * @returns {HTMLOptionElement} - The option element
 */
export function createOption(value, text, selected = false) {
    const option = document.createElement('option');
    option.value = String(value ?? '');
    option.textContent = String(text ?? '');
    if (selected) {
        option.selected = true;
    }
    return option;
}

/**
 * Safely populate a select element with options
 * @param {HTMLSelectElement} select - The select element
 * @param {Array<{value: string, text: string}>} options - The options to add
 * @param {string} placeholder - Optional placeholder text
 */
export function populateSelect(select, options, placeholder = '') {
    if (!select) return;

    // Clear existing options safely
    while (select.firstChild) {
        select.removeChild(select.firstChild);
    }

    // Add placeholder if provided
    if (placeholder) {
        select.appendChild(createOption('', placeholder));
    }

    // Add options safely
    options.forEach(opt => {
        select.appendChild(createOption(opt.value, opt.text, opt.selected));
    });
}

/**
 * Create a table cell with text content
 * @param {string} text - The cell text
 * @param {string} className - Optional CSS class
 * @returns {HTMLTableCellElement} - The table cell
 */
export function createTableCell(text, className = '') {
    const td = document.createElement('td');
    td.textContent = String(text ?? '');
    if (className) {
        td.className = className;
    }
    return td;
}

/**
 * Create a table row with cells
 * @param {Array<string|{text: string, className: string}>} cells - Cell contents
 * @returns {HTMLTableRowElement} - The table row
 */
export function createTableRow(cells) {
    const tr = document.createElement('tr');
    cells.forEach(cell => {
        if (typeof cell === 'object') {
            tr.appendChild(createTableCell(cell.text, cell.className));
        } else {
            tr.appendChild(createTableCell(cell));
        }
    });
    return tr;
}

/**
 * Create a span element with text
 * @param {string} text - The text content
 * @param {string} className - Optional CSS class
 * @returns {HTMLSpanElement} - The span element
 */
export function createSpan(text, className = '') {
    const span = document.createElement('span');
    span.textContent = String(text ?? '');
    if (className) {
        span.className = className;
    }
    return span;
}

/**
 * Create a div element with text
 * @param {string} text - The text content
 * @param {string} className - Optional CSS class
 * @returns {HTMLDivElement} - The div element
 */
export function createDiv(text = '', className = '') {
    const div = document.createElement('div');
    if (text) {
        div.textContent = String(text);
    }
    if (className) {
        div.className = className;
    }
    return div;
}

/**
 * Safely append multiple children to an element
 * @param {HTMLElement} parent - The parent element
 * @param {Array<HTMLElement|string>} children - Children to append
 */
export function appendChildren(parent, children) {
    if (!parent) return;
    children.forEach(child => {
        if (typeof child === 'string') {
            parent.appendChild(createTextNode(child));
        } else if (child) {
            parent.appendChild(child);
        }
    });
}

/**
 * Clear all children from an element
 * @param {HTMLElement} element - The element to clear
 */
export function clearElement(element) {
    if (element) {
        while (element.firstChild) {
            element.removeChild(element.firstChild);
        }
    }
}

/**
 * Validate and sanitize a string for use as an ID
 * @param {string} id - The ID to validate
 * @returns {string} - Sanitized ID
 */
export function sanitizeId(id) {
    if (!id) return '';
    // Only allow alphanumeric, underscore, and hyphen
    return String(id).replace(/[^a-zA-Z0-9_-]/g, '');
}

/**
 * Validate and sanitize a number
 * @param {any} value - The value to validate
 * @param {number} defaultValue - Default value if invalid
 * @param {number} min - Minimum allowed value
 * @param {number} max - Maximum allowed value
 * @returns {number} - Sanitized number
 */
export function sanitizeNumber(value, defaultValue = 0, min = -Infinity, max = Infinity) {
    const num = Number(value);
    if (isNaN(num)) return defaultValue;
    return Math.max(min, Math.min(max, num));
}

/**
 * Create a safe HTML string for tooltip content
 * Uses escapeHtml for all dynamic values
 * @param {object} data - The data object
 * @returns {string} - Safe HTML string
 */
export function createTooltipContent(data) {
    const title = escapeHtml(data.title || '');
    const rows = (data.rows || []).map(row => {
        const label = escapeHtml(row.label);
        const value = escapeHtml(row.value);
        return `<div class="tooltip-row">
            <span class="tooltip-label">${label}:</span>
            <span class="tooltip-value">${value}</span>
        </div>`;
    }).join('');

    return `<div class="tooltip-title">${title}</div>
        <div class="tooltip-content">${rows}</div>`;
}

export default {
    escapeHtml,
    createTextNode,
    setTextContent,
    createOption,
    populateSelect,
    createTableCell,
    createTableRow,
    createSpan,
    createDiv,
    appendChildren,
    clearElement,
    sanitizeId,
    sanitizeNumber,
    createTooltipContent,
};
