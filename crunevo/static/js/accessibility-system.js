/**
 * Accessibility System
 * Comprehensive accessibility features including ARIA, keyboard navigation, screen reader support
 */

class AccessibilitySystem {
    constructor() {
        this.focusableElements = [
            'a[href]',
            'button:not([disabled])',
            'input:not([disabled])',
            'select:not([disabled])',
            'textarea:not([disabled])',
            '[tabindex]:not([tabindex="-1"])',
            '[contenteditable="true"]'
        ].join(', ');
        
        this.announcements = [];
        this.focusHistory = [];
        this.skipLinks = [];
        this.landmarks = [];
        
        this.settings = {
            highContrast: false,
            reducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
            fontSize: 'normal',
            focusVisible: true,
            screenReaderMode: false
        };
        
        this.init();
    }

    init() {
        this.createAriaLiveRegion();
        this.setupKeyboardNavigation();
        this.setupFocusManagement();
        this.setupSkipLinks();
        this.setupLandmarks();
        this.setupFormAccessibility();
        this.setupModalAccessibility();
        this.setupTooltipAccessibility();
        this.setupTableAccessibility();
        this.setupImageAccessibility();
        this.setupColorContrastToggle();
        this.setupFontSizeControls();
        this.setupScreenReaderSupport();
        this.bindEvents();
        this.loadUserPreferences();
    }

    // ===== ARIA LIVE REGIONS =====
    createAriaLiveRegion() {
        // Create polite announcements region
        const politeRegion = document.createElement('div');
        politeRegion.id = 'aria-live-polite';
        politeRegion.setAttribute('aria-live', 'polite');
        politeRegion.setAttribute('aria-atomic', 'true');
        politeRegion.style.cssText = `
            position: absolute;
            left: -10000px;
            width: 1px;
            height: 1px;
            overflow: hidden;
        `;
        document.body.appendChild(politeRegion);

        // Create assertive announcements region
        const assertiveRegion = document.createElement('div');
        assertiveRegion.id = 'aria-live-assertive';
        assertiveRegion.setAttribute('aria-live', 'assertive');
        assertiveRegion.setAttribute('aria-atomic', 'true');
        assertiveRegion.style.cssText = politeRegion.style.cssText;
        document.body.appendChild(assertiveRegion);

        this.politeRegion = politeRegion;
        this.assertiveRegion = assertiveRegion;
    }

    announce(message, priority = 'polite') {
        const region = priority === 'assertive' ? this.assertiveRegion : this.politeRegion;
        
        // Clear previous message
        region.textContent = '';
        
        // Add new message after a brief delay to ensure screen readers pick it up
        setTimeout(() => {
            region.textContent = message;
            this.announcements.push({
                message,
                priority,
                timestamp: new Date()
            });
        }, 100);
    }

    // ===== KEYBOARD NAVIGATION =====
    setupKeyboardNavigation() {
        document.addEventListener('keydown', (e) => {
            this.handleGlobalKeydown(e);
        });

        // Tab trapping for modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                const modal = document.querySelector('.modal.show');
                if (modal) {
                    this.trapFocus(e, modal);
                }
            }
        });

        // Arrow key navigation for grids and lists
        document.addEventListener('keydown', (e) => {
            if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
                this.handleArrowNavigation(e);
            }
        });
    }

    handleGlobalKeydown(e) {
        // Skip to main content (Alt + M)
        if (e.altKey && e.key === 'm') {
            e.preventDefault();
            this.skipToMain();
        }

        // Skip to navigation (Alt + N)
        if (e.altKey && e.key === 'n') {
            e.preventDefault();
            this.skipToNavigation();
        }

        // Toggle high contrast (Alt + C)
        if (e.altKey && e.key === 'c') {
            e.preventDefault();
            this.toggleHighContrast();
        }

        // Increase font size (Alt + Plus)
        if (e.altKey && e.key === '+') {
            e.preventDefault();
            this.increaseFontSize();
        }

        // Decrease font size (Alt + Minus)
        if (e.altKey && e.key === '-') {
            e.preventDefault();
            this.decreaseFontSize();
        }

        // Escape key handling
        if (e.key === 'Escape') {
            this.handleEscape();
        }
    }

    handleArrowNavigation(e) {
        const target = e.target;
        
        // Grid navigation
        if (target.closest('[role="grid"]')) {
            this.navigateGrid(e);
        }
        
        // List navigation
        if (target.closest('[role="listbox"], [role="menu"]')) {
            this.navigateList(e);
        }
        
        // Block navigation in workspace
        if (target.closest('.workspace-grid')) {
            this.navigateWorkspace(e);
        }
    }

    navigateGrid(e) {
        e.preventDefault();
        const grid = e.target.closest('[role="grid"]');
        const cells = Array.from(grid.querySelectorAll('[role="gridcell"]'));
        const currentIndex = cells.indexOf(e.target.closest('[role="gridcell"]'));
        
        if (currentIndex === -1) return;
        
        const gridWidth = parseInt(grid.getAttribute('aria-colcount')) || Math.sqrt(cells.length);
        let newIndex;
        
        switch (e.key) {
            case 'ArrowUp':
                newIndex = currentIndex - gridWidth;
                break;
            case 'ArrowDown':
                newIndex = currentIndex + gridWidth;
                break;
            case 'ArrowLeft':
                newIndex = currentIndex - 1;
                break;
            case 'ArrowRight':
                newIndex = currentIndex + 1;
                break;
        }
        
        if (newIndex >= 0 && newIndex < cells.length) {
            cells[newIndex].focus();
        }
    }

    navigateList(e) {
        e.preventDefault();
        const list = e.target.closest('[role="listbox"], [role="menu"]');
        const items = Array.from(list.querySelectorAll('[role="option"], [role="menuitem"]'));
        const currentIndex = items.indexOf(e.target);
        
        if (currentIndex === -1) return;
        
        let newIndex;
        
        switch (e.key) {
            case 'ArrowUp':
                newIndex = currentIndex > 0 ? currentIndex - 1 : items.length - 1;
                break;
            case 'ArrowDown':
                newIndex = currentIndex < items.length - 1 ? currentIndex + 1 : 0;
                break;
        }
        
        if (newIndex !== undefined) {
            items[newIndex].focus();
        }
    }

    navigateWorkspace(e) {
        e.preventDefault();
        const workspace = e.target.closest('.workspace-grid');
        const blocks = Array.from(workspace.querySelectorAll('.block'));
        const currentIndex = blocks.indexOf(e.target.closest('.block'));
        
        if (currentIndex === -1) return;
        
        const gridCols = parseInt(getComputedStyle(workspace).gridTemplateColumns.split(' ').length) || 3;
        let newIndex;
        
        switch (e.key) {
            case 'ArrowUp':
                newIndex = currentIndex - gridCols;
                break;
            case 'ArrowDown':
                newIndex = currentIndex + gridCols;
                break;
            case 'ArrowLeft':
                newIndex = currentIndex - 1;
                break;
            case 'ArrowRight':
                newIndex = currentIndex + 1;
                break;
        }
        
        if (newIndex >= 0 && newIndex < blocks.length) {
            blocks[newIndex].focus();
        }
    }

    trapFocus(e, container) {
        const focusableElements = container.querySelectorAll(this.focusableElements);
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        
        if (e.shiftKey && document.activeElement === firstElement) {
            e.preventDefault();
            lastElement.focus();
        } else if (!e.shiftKey && document.activeElement === lastElement) {
            e.preventDefault();
            firstElement.focus();
        }
    }

    // ===== FOCUS MANAGEMENT =====
    setupFocusManagement() {
        // Track focus for restoration
        document.addEventListener('focusin', (e) => {
            this.focusHistory.push(e.target);
            if (this.focusHistory.length > 10) {
                this.focusHistory.shift();
            }
        });

        // Enhanced focus indicators
        document.addEventListener('focusin', (e) => {
            if (this.settings.focusVisible) {
                e.target.classList.add('focus-visible');
            }
        });

        document.addEventListener('focusout', (e) => {
            e.target.classList.remove('focus-visible');
        });

        // Mouse users shouldn't see focus indicators
        document.addEventListener('mousedown', () => {
            document.body.classList.add('using-mouse');
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                document.body.classList.remove('using-mouse');
            }
        });
    }

    restoreFocus() {
        if (this.focusHistory.length > 1) {
            const previousElement = this.focusHistory[this.focusHistory.length - 2];
            if (previousElement && document.contains(previousElement)) {
                previousElement.focus();
            }
        }
    }

    // ===== SKIP LINKS =====
    setupSkipLinks() {
        const skipLinksContainer = document.createElement('div');
        skipLinksContainer.className = 'skip-links';
        skipLinksContainer.innerHTML = `
            <a href="#main-content" class="skip-link">Skip to main content</a>
            <a href="#navigation" class="skip-link">Skip to navigation</a>
            <a href="#search" class="skip-link">Skip to search</a>
        `;
        
        document.body.insertBefore(skipLinksContainer, document.body.firstChild);
        
        // Style skip links
        const style = document.createElement('style');
        style.textContent = `
            .skip-links {
                position: absolute;
                top: -40px;
                left: 6px;
                z-index: 9999;
            }
            
            .skip-link {
                position: absolute;
                top: -40px;
                left: 6px;
                background: #000;
                color: #fff;
                padding: 8px;
                text-decoration: none;
                border-radius: 4px;
                font-weight: bold;
                z-index: 10000;
            }
            
            .skip-link:focus {
                top: 6px;
            }
        `;
        document.head.appendChild(style);
    }

    skipToMain() {
        const main = document.querySelector('#main-content, main, [role="main"]');
        if (main) {
            main.focus();
            main.scrollIntoView();
            this.announce('Skipped to main content');
        }
    }

    skipToNavigation() {
        const nav = document.querySelector('#navigation, nav, [role="navigation"]');
        if (nav) {
            const firstLink = nav.querySelector('a, button');
            if (firstLink) {
                firstLink.focus();
                this.announce('Skipped to navigation');
            }
        }
    }

    // ===== LANDMARKS =====
    setupLandmarks() {
        // Ensure proper landmark roles
        const header = document.querySelector('header');
        if (header && !header.getAttribute('role')) {
            header.setAttribute('role', 'banner');
        }

        const nav = document.querySelector('nav');
        if (nav && !nav.getAttribute('role')) {
            nav.setAttribute('role', 'navigation');
        }

        const main = document.querySelector('main');
        if (main && !main.getAttribute('role')) {
            main.setAttribute('role', 'main');
        }

        const footer = document.querySelector('footer');
        if (footer && !footer.getAttribute('role')) {
            footer.setAttribute('role', 'contentinfo');
        }

        // Add landmark navigation
        this.createLandmarkNavigation();
    }

    createLandmarkNavigation() {
        const landmarks = document.querySelectorAll('[role="banner"], [role="navigation"], [role="main"], [role="contentinfo"], [role="complementary"]');
        
        if (landmarks.length > 1) {
            const landmarkNav = document.createElement('nav');
            landmarkNav.setAttribute('aria-label', 'Page landmarks');
            landmarkNav.className = 'landmark-navigation sr-only';
            
            const list = document.createElement('ul');
            
            landmarks.forEach((landmark, index) => {
                const role = landmark.getAttribute('role');
                const label = landmark.getAttribute('aria-label') || this.getLandmarkLabel(role);
                
                if (!landmark.id) {
                    landmark.id = `landmark-${role}-${index}`;
                }
                
                const listItem = document.createElement('li');
                const link = document.createElement('a');
                link.href = `#${landmark.id}`;
                link.textContent = label;
                
                listItem.appendChild(link);
                list.appendChild(listItem);
            });
            
            landmarkNav.appendChild(list);
            document.body.insertBefore(landmarkNav, document.body.firstChild);
        }
    }

    getLandmarkLabel(role) {
        const labels = {
            'banner': 'Header',
            'navigation': 'Navigation',
            'main': 'Main content',
            'contentinfo': 'Footer',
            'complementary': 'Sidebar'
        };
        return labels[role] || role;
    }

    // ===== FORM ACCESSIBILITY =====
    setupFormAccessibility() {
        // Add proper labels and descriptions
        document.querySelectorAll('input, select, textarea').forEach(input => {
            this.enhanceFormField(input);
        });

        // Form validation announcements
        document.addEventListener('invalid', (e) => {
            this.announceValidationError(e.target);
        }, true);

        // Real-time validation feedback
        document.addEventListener('input', (e) => {
            if (e.target.matches('input, select, textarea')) {
                this.updateValidationState(e.target);
            }
        });
    }

    enhanceFormField(field) {
        // Ensure proper labeling
        if (!field.getAttribute('aria-label') && !field.getAttribute('aria-labelledby')) {
            const label = document.querySelector(`label[for="${field.id}"]`);
            if (!label && field.id) {
                // Create implicit label relationship
                const parentLabel = field.closest('label');
                if (parentLabel) {
                    field.setAttribute('aria-label', parentLabel.textContent.trim());
                }
            }
        }

        // Add required indicator
        if (field.required) {
            field.setAttribute('aria-required', 'true');
            
            // Add visual required indicator if not present
            const label = document.querySelector(`label[for="${field.id}"]`) || field.closest('label');
            if (label && !label.querySelector('.required-indicator')) {
                const indicator = document.createElement('span');
                indicator.className = 'required-indicator';
                indicator.textContent = ' *';
                indicator.setAttribute('aria-label', 'required');
                label.appendChild(indicator);
            }
        }

        // Add error container
        if (!field.getAttribute('aria-describedby')) {
            const errorId = `${field.id}-error`;
            let errorContainer = document.getElementById(errorId);
            
            if (!errorContainer) {
                errorContainer = document.createElement('div');
                errorContainer.id = errorId;
                errorContainer.className = 'error-message';
                errorContainer.setAttribute('aria-live', 'polite');
                field.parentNode.insertBefore(errorContainer, field.nextSibling);
            }
            
            field.setAttribute('aria-describedby', errorId);
        }
    }

    announceValidationError(field) {
        const errorMessage = field.validationMessage;
        if (errorMessage) {
            this.announce(`Error in ${this.getFieldLabel(field)}: ${errorMessage}`, 'assertive');
        }
    }

    updateValidationState(field) {
        const errorContainer = document.getElementById(field.getAttribute('aria-describedby'));
        
        if (field.validity.valid) {
            field.setAttribute('aria-invalid', 'false');
            if (errorContainer) {
                errorContainer.textContent = '';
            }
        } else {
            field.setAttribute('aria-invalid', 'true');
            if (errorContainer) {
                errorContainer.textContent = field.validationMessage;
            }
        }
    }

    getFieldLabel(field) {
        const label = document.querySelector(`label[for="${field.id}"]`) || field.closest('label');
        return label ? label.textContent.trim() : field.name || field.id || 'field';
    }

    // ===== MODAL ACCESSIBILITY =====
    setupModalAccessibility() {
        // Modal show event
        document.addEventListener('show.bs.modal', (e) => {
            this.setupModalA11y(e.target);
        });

        // Modal hide event
        document.addEventListener('hide.bs.modal', (e) => {
            this.restoreFocus();
        });
    }

    setupModalA11y(modal) {
        // Set proper ARIA attributes
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-modal', 'true');
        
        // Find and set aria-labelledby
        const title = modal.querySelector('.modal-title');
        if (title) {
            if (!title.id) {
                title.id = `modal-title-${Date.now()}`;
            }
            modal.setAttribute('aria-labelledby', title.id);
        }

        // Set initial focus
        setTimeout(() => {
            const firstFocusable = modal.querySelector(this.focusableElements);
            if (firstFocusable) {
                firstFocusable.focus();
            }
        }, 100);

        // Announce modal opening
        this.announce(`Dialog opened: ${title ? title.textContent : 'Modal dialog'}`);
    }

    // ===== TOOLTIP ACCESSIBILITY =====
    setupTooltipAccessibility() {
        document.querySelectorAll('[data-tooltip], [title]').forEach(element => {
            this.enhanceTooltip(element);
        });
    }

    enhanceTooltip(element) {
        const tooltipText = element.getAttribute('data-tooltip') || element.getAttribute('title');
        
        if (tooltipText) {
            // Remove title to prevent browser tooltip
            element.removeAttribute('title');
            
            // Create tooltip element
            const tooltipId = `tooltip-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
            const tooltip = document.createElement('div');
            tooltip.id = tooltipId;
            tooltip.className = 'tooltip-content';
            tooltip.textContent = tooltipText;
            tooltip.setAttribute('role', 'tooltip');
            
            // Set ARIA relationship
            element.setAttribute('aria-describedby', tooltipId);
            
            // Add to DOM (initially hidden)
            document.body.appendChild(tooltip);
            
            // Show/hide events
            element.addEventListener('mouseenter', () => this.showTooltip(tooltip));
            element.addEventListener('mouseleave', () => this.hideTooltip(tooltip));
            element.addEventListener('focus', () => this.showTooltip(tooltip));
            element.addEventListener('blur', () => this.hideTooltip(tooltip));
        }
    }

    showTooltip(tooltip) {
        tooltip.style.display = 'block';
        // Position tooltip (simplified)
        tooltip.style.position = 'absolute';
        tooltip.style.zIndex = '9999';
    }

    hideTooltip(tooltip) {
        tooltip.style.display = 'none';
    }

    // ===== TABLE ACCESSIBILITY =====
    setupTableAccessibility() {
        document.querySelectorAll('table').forEach(table => {
            this.enhanceTable(table);
        });
    }

    enhanceTable(table) {
        // Add table role if not present
        if (!table.getAttribute('role')) {
            table.setAttribute('role', 'table');
        }

        // Add caption if not present
        if (!table.querySelector('caption')) {
            const caption = document.createElement('caption');
            caption.textContent = table.getAttribute('aria-label') || 'Data table';
            table.insertBefore(caption, table.firstChild);
        }

        // Enhance headers
        table.querySelectorAll('th').forEach(th => {
            if (!th.getAttribute('scope')) {
                // Determine scope based on position
                const row = th.closest('tr');
                const isFirstRow = row === table.querySelector('tr');
                th.setAttribute('scope', isFirstRow ? 'col' : 'row');
            }
        });

        // Add row/column headers for complex tables
        if (table.querySelectorAll('th').length > table.querySelectorAll('thead th').length) {
            table.querySelectorAll('tbody tr').forEach((row, rowIndex) => {
                row.querySelectorAll('td').forEach((cell, cellIndex) => {
                    const columnHeader = table.querySelector(`thead th:nth-child(${cellIndex + 1})`);
                    const rowHeader = row.querySelector('th');
                    
                    const headers = [];
                    if (columnHeader && columnHeader.id) headers.push(columnHeader.id);
                    if (rowHeader && rowHeader.id) headers.push(rowHeader.id);
                    
                    if (headers.length > 0) {
                        cell.setAttribute('headers', headers.join(' '));
                    }
                });
            });
        }
    }

    // ===== IMAGE ACCESSIBILITY =====
    setupImageAccessibility() {
        document.querySelectorAll('img').forEach(img => {
            this.enhanceImage(img);
        });
    }

    enhanceImage(img) {
        // Check for missing alt text
        if (!img.hasAttribute('alt')) {
            // Decorative images should have empty alt
            if (img.closest('.decoration, .background')) {
                img.setAttribute('alt', '');
            } else {
                // Try to infer alt text from context
                const figcaption = img.closest('figure')?.querySelector('figcaption');
                const title = img.getAttribute('title');
                
                if (figcaption) {
                    img.setAttribute('alt', figcaption.textContent.trim());
                } else if (title) {
                    img.setAttribute('alt', title);
                } else {
                    // Flag for manual review
                    img.setAttribute('alt', 'Image (alt text needed)');
                    console.warn('Image missing alt text:', img.src);
                }
            }
        }

        // Handle loading states
        if (img.loading === 'lazy') {
            img.addEventListener('load', () => {
                this.announce(`Image loaded: ${img.alt}`);
            });
        }
    }

    // ===== COLOR CONTRAST =====
    setupColorContrastToggle() {
        const contrastToggle = document.createElement('button');
        contrastToggle.className = 'contrast-toggle';
        contrastToggle.textContent = 'Toggle High Contrast';
        contrastToggle.setAttribute('aria-label', 'Toggle high contrast mode');
        
        contrastToggle.addEventListener('click', () => {
            this.toggleHighContrast();
        });
        
        // Add to accessibility toolbar
        this.getAccessibilityToolbar().appendChild(contrastToggle);
    }

    toggleHighContrast() {
        this.settings.highContrast = !this.settings.highContrast;
        document.body.classList.toggle('high-contrast', this.settings.highContrast);
        
        this.announce(
            this.settings.highContrast ? 'High contrast enabled' : 'High contrast disabled'
        );
        
        this.saveUserPreferences();
    }

    // ===== FONT SIZE CONTROLS =====
    setupFontSizeControls() {
        const fontControls = document.createElement('div');
        fontControls.className = 'font-size-controls';
        fontControls.innerHTML = `
            <button class="font-decrease" aria-label="Decrease font size">A-</button>
            <button class="font-reset" aria-label="Reset font size">A</button>
            <button class="font-increase" aria-label="Increase font size">A+</button>
        `;
        
        fontControls.querySelector('.font-decrease').addEventListener('click', () => {
            this.decreaseFontSize();
        });
        
        fontControls.querySelector('.font-reset').addEventListener('click', () => {
            this.resetFontSize();
        });
        
        fontControls.querySelector('.font-increase').addEventListener('click', () => {
            this.increaseFontSize();
        });
        
        this.getAccessibilityToolbar().appendChild(fontControls);
    }

    increaseFontSize() {
        const sizes = ['normal', 'large', 'larger', 'largest'];
        const currentIndex = sizes.indexOf(this.settings.fontSize);
        
        if (currentIndex < sizes.length - 1) {
            this.settings.fontSize = sizes[currentIndex + 1];
            this.applyFontSize();
            this.announce(`Font size increased to ${this.settings.fontSize}`);
        }
    }

    decreaseFontSize() {
        const sizes = ['normal', 'large', 'larger', 'largest'];
        const currentIndex = sizes.indexOf(this.settings.fontSize);
        
        if (currentIndex > 0) {
            this.settings.fontSize = sizes[currentIndex - 1];
            this.applyFontSize();
            this.announce(`Font size decreased to ${this.settings.fontSize}`);
        }
    }

    resetFontSize() {
        this.settings.fontSize = 'normal';
        this.applyFontSize();
        this.announce('Font size reset to normal');
    }

    applyFontSize() {
        document.body.className = document.body.className.replace(/font-size-\w+/g, '');
        document.body.classList.add(`font-size-${this.settings.fontSize}`);
        this.saveUserPreferences();
    }

    // ===== SCREEN READER SUPPORT =====
    setupScreenReaderSupport() {
        // Detect screen reader usage
        this.detectScreenReader();
        
        // Enhanced announcements for screen readers
        this.setupScreenReaderAnnouncements();
    }

    detectScreenReader() {
        // Simple heuristic for screen reader detection
        const hasScreenReader = (
            navigator.userAgent.includes('NVDA') ||
            navigator.userAgent.includes('JAWS') ||
            navigator.userAgent.includes('VoiceOver') ||
            window.speechSynthesis
        );
        
        if (hasScreenReader) {
            this.settings.screenReaderMode = true;
            document.body.classList.add('screen-reader-mode');
        }
    }

    setupScreenReaderAnnouncements() {
        // Announce page changes
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === 1) { // Element node
                            this.announceNewContent(node);
                        }
                    });
                }
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    announceNewContent(element) {
        // Announce important new content
        if (element.matches('.alert, .notification, .toast')) {
            const text = element.textContent.trim();
            if (text) {
                this.announce(text, 'assertive');
            }
        }
        
        // Announce new blocks
        if (element.matches('.block')) {
            const title = element.querySelector('.block-title')?.textContent || 'New block';
            this.announce(`${title} added`);
        }
    }

    // ===== UTILITY METHODS =====
    getAccessibilityToolbar() {
        let toolbar = document.querySelector('.accessibility-toolbar');
        
        if (!toolbar) {
            toolbar = document.createElement('div');
            toolbar.className = 'accessibility-toolbar';
            toolbar.setAttribute('role', 'toolbar');
            toolbar.setAttribute('aria-label', 'Accessibility options');
            
            // Style the toolbar
            toolbar.style.cssText = `
                position: fixed;
                top: 0;
                right: 0;
                background: #000;
                color: #fff;
                padding: 10px;
                z-index: 9999;
                display: flex;
                gap: 10px;
                transform: translateY(-100%);
                transition: transform 0.3s ease;
            `;
            
            // Show on focus
            toolbar.addEventListener('focusin', () => {
                toolbar.style.transform = 'translateY(0)';
            });
            
            toolbar.addEventListener('focusout', (e) => {
                if (!toolbar.contains(e.relatedTarget)) {
                    toolbar.style.transform = 'translateY(-100%)';
                }
            });
            
            document.body.appendChild(toolbar);
        }
        
        return toolbar;
    }

    handleEscape() {
        // Close modals
        const modal = document.querySelector('.modal.show');
        if (modal) {
            const closeBtn = modal.querySelector('[data-bs-dismiss="modal"]');
            if (closeBtn) {
                closeBtn.click();
            }
        }
        
        // Close dropdowns
        const dropdown = document.querySelector('.dropdown.show');
        if (dropdown) {
            dropdown.classList.remove('show');
        }
        
        // Clear search
        const searchInput = document.querySelector('input[type="search"]:focus');
        if (searchInput && searchInput.value) {
            searchInput.value = '';
            searchInput.dispatchEvent(new Event('input'));
        }
    }

    // ===== PREFERENCES =====
    saveUserPreferences() {
        localStorage.setItem('accessibility-preferences', JSON.stringify(this.settings));
    }

    loadUserPreferences() {
        const saved = localStorage.getItem('accessibility-preferences');
        if (saved) {
            try {
                const preferences = JSON.parse(saved);
                Object.assign(this.settings, preferences);
                
                // Apply saved preferences
                if (this.settings.highContrast) {
                    document.body.classList.add('high-contrast');
                }
                
                this.applyFontSize();
                
            } catch (e) {
                console.error('Error loading accessibility preferences:', e);
            }
        }
    }

    // ===== EVENT BINDING =====
    bindEvents() {
        // Handle reduced motion preference changes
        const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
        mediaQuery.addListener((e) => {
            this.settings.reducedMotion = e.matches;
            document.body.classList.toggle('reduce-motion', e.matches);
        });
        
        // Handle color scheme changes
        const colorSchemeQuery = window.matchMedia('(prefers-color-scheme: dark)');
        colorSchemeQuery.addListener((e) => {
            this.announce(e.matches ? 'Dark mode detected' : 'Light mode detected');
        });
    }

    // ===== PUBLIC API =====
    
    // Get accessibility report
    getAccessibilityReport() {
        const issues = [];
        
        // Check for missing alt text
        document.querySelectorAll('img:not([alt])').forEach(img => {
            issues.push({
                type: 'missing-alt',
                element: img,
                message: 'Image missing alt text'
            });
        });
        
        // Check for missing form labels
        document.querySelectorAll('input:not([aria-label]):not([aria-labelledby])').forEach(input => {
            if (!document.querySelector(`label[for="${input.id}"]`) && !input.closest('label')) {
                issues.push({
                    type: 'missing-label',
                    element: input,
                    message: 'Form field missing label'
                });
            }
        });
        
        // Check for missing headings
        const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
        if (headings.length === 0) {
            issues.push({
                type: 'missing-headings',
                message: 'Page has no heading structure'
            });
        }
        
        return {
            issues,
            score: Math.max(0, 100 - (issues.length * 10)),
            announcements: this.announcements.slice(-10)
        };
    }
    
    // Manual announcement
    announceMessage(message, priority = 'polite') {
        this.announce(message, priority);
    }
    
    // Focus management
    focusElement(selector) {
        const element = document.querySelector(selector);
        if (element) {
            element.focus();
            element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
    
    // Cleanup
    destroy() {
        // Remove created elements
        document.querySelectorAll('.accessibility-toolbar, .skip-links, .landmark-navigation').forEach(el => {
            el.remove();
        });
        
        // Remove event listeners would go here
        // (In a real implementation, you'd track and remove all listeners)
    }
}

// CSS for accessibility features
const accessibilityCSS = `
/* High contrast mode */
.high-contrast {
    filter: contrast(150%) brightness(120%);
}

.high-contrast * {
    background-color: #000 !important;
    color: #fff !important;
    border-color: #fff !important;
}

.high-contrast a {
    color: #ffff00 !important;
}

.high-contrast button {
    background-color: #fff !important;
    color: #000 !important;
}

/* Font size variations */
.font-size-large {
    font-size: 1.125em;
}

.font-size-larger {
    font-size: 1.25em;
}

.font-size-largest {
    font-size: 1.5em;
}

/* Focus indicators */
.focus-visible {
    outline: 3px solid #005fcc !important;
    outline-offset: 2px !important;
}

.using-mouse .focus-visible {
    outline: none !important;
}

/* Screen reader only content */
.sr-only {
    position: absolute !important;
    width: 1px !important;
    height: 1px !important;
    padding: 0 !important;
    margin: -1px !important;
    overflow: hidden !important;
    clip: rect(0, 0, 0, 0) !important;
    white-space: nowrap !important;
    border: 0 !important;
}

/* Reduced motion */
.reduce-motion *,
.reduce-motion *::before,
.reduce-motion *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
}

/* Error messages */
.error-message {
    color: #d32f2f;
    font-size: 0.875em;
    margin-top: 0.25rem;
}

.error-message:empty {
    display: none;
}

/* Required indicators */
.required-indicator {
    color: #d32f2f;
    font-weight: bold;
}

/* Tooltip styling */
.tooltip-content {
    background: #333;
    color: #fff;
    padding: 0.5rem;
    border-radius: 4px;
    font-size: 0.875rem;
    max-width: 200px;
    z-index: 9999;
    display: none;
}
`;

// Add CSS to document
if (!document.querySelector('#accessibility-css')) {
    const style = document.createElement('style');
    style.id = 'accessibility-css';
    style.textContent = accessibilityCSS;
    document.head.appendChild(style);
}

// Initialize accessibility system when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.accessibilitySystem = new AccessibilitySystem();
    });
} else {
    window.accessibilitySystem = new AccessibilitySystem();
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AccessibilitySystem;
}