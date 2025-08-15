/**
 * BlockFactory - Modal for creating any type of block
 * Handles block creation workflow, templates, and configuration
 * Rewritten without global onclick handlers, using event delegation
 */

window.BlockFactory = {
    // Wizard state
    wizard: {
        selectedType: null,
        config: {},
        step: 1
    },
    
    // Additional state
    totalSteps: 3,
    selectedTemplate: null,
    templates: [],

    // Initialize the factory
    init: function() {
        // Reset wizard state
        this.wizard = {
            selectedType: null,
            config: {},
            step: 1
        };
        this.selectedTemplate = null;
        
        // Show first step
        this.showStep(1);
        this.updateStepIndicator();
        this.updateButtons();
        
        // Load templates for template mode
        this.loadTemplates();
        
        // Setup event listeners
        this.setupEventListeners();
    },

    // Setup event listeners with delegation
    setupEventListeners: function() {
        const modal = document.getElementById('block-factory-modal');
        if (!modal) return;
        
        // Remove existing listeners to avoid duplicates
        modal.removeEventListener('click', this.handleModalClick);
        modal.removeEventListener('input', this.handleModalInput);
        modal.removeEventListener('change', this.handleModalChange);
        
        // Event delegation for all modal interactions
        this.handleModalClick = this.handleModalClick.bind(this);
        this.handleModalInput = this.handleModalInput.bind(this);
        this.handleModalChange = this.handleModalChange.bind(this);
        
        modal.addEventListener('click', this.handleModalClick);
        modal.addEventListener('input', this.handleModalInput);
        modal.addEventListener('change', this.handleModalChange);
        
        // Creation mode tabs
        this.setupCreationModeTabs();
    },
    
    // Handle all click events in modal
    handleModalClick: function(e) {
        const target = e.target.closest('[data-action], [data-block-type], [data-template-id], [data-color], .block-type-card, .template-card, .color-option');
        if (!target) return;
        
        // Block type selection
        if (target.hasAttribute('data-block-type') || target.classList.contains('block-type-card')) {
            const blockType = target.getAttribute('data-block-type');
            if (blockType) {
                this.selectBlockType(blockType);
            }
            return;
        }
        
        // Template selection
        if (target.hasAttribute('data-template-id') || target.classList.contains('template-card')) {
            const templateId = target.getAttribute('data-template-id');
            if (templateId) {
                this.selectTemplate(templateId);
            }
            return;
        }
        
        // Color selection
        if (target.hasAttribute('data-color') || target.classList.contains('color-option')) {
            const color = target.getAttribute('data-color');
            if (color) {
                this.selectColor(color);
            }
            return;
        }
        
        // Template selection
        if (target.classList.contains('template-card') || target.closest('.template-card')) {
            const templateCard = target.classList.contains('template-card') ? target : target.closest('.template-card');
            const templateId = templateCard.getAttribute('data-template-id');
            if (templateId) {
                this.selectTemplate(templateId);
            }
            return;
        }
        
        // Action buttons
        const action = target.getAttribute('data-action') || target.id;
        switch (action) {
            case 'next-step':
            case 'next-step-btn':
                this.nextStep();
                break;
            case 'prev-step':
            case 'prev-step-btn':
                this.previousStep();
                break;
            case 'create-block':
            case 'create-block-btn':
                this.createBlock();
                break;
            case 'select-template':
                const templateId = target.getAttribute('data-template-id');
                if (templateId) {
                    this.selectTemplate(templateId);
                }
                break;
        }
    },
    
    // Handle input events
    handleModalInput: function(e) {
        const target = e.target;
        
        // Template search
        if (target.id === 'template-search') {
            this.searchTemplates(target.value);
            return;
        }
        
        // Title input for preview
        if (target.name === 'title') {
            this.updatePreview();
            return;
        }
    },
    
    // Handle change events
    handleModalChange: function(e) {
        const target = e.target;
        
        // Preview updates
        if (target.id === 'show_border' || target.id === 'show_shadow') {
            this.updatePreview();
            return;
        }
    },

    // Setup creation mode tabs
    setupCreationModeTabs: function() {
        const individualTab = document.getElementById('individual-tab');
        const templateTab = document.getElementById('template-tab');
        
        if (individualTab) {
            individualTab.addEventListener('click', () => {
                // Switch to individual mode
                document.querySelectorAll('.creation-mode-tab').forEach(tab => {
                    tab.classList.remove('active');
                });
                individualTab.classList.add('active');
                
                // Show/hide content
                const individualMode = document.getElementById('individual-mode');
                const templateMode = document.getElementById('template-mode');
                if (individualMode && templateMode) {
                    individualMode.classList.remove('d-none');
                    templateMode.classList.add('d-none');
                }
                
                // Update buttons
                this.updateButtons();
            });
        }
        
        if (templateTab) {
            templateTab.addEventListener('click', () => {
                // Switch to template mode
                document.querySelectorAll('.creation-mode-tab').forEach(tab => {
                    tab.classList.remove('active');
                });
                templateTab.classList.add('active');
                
                // Show/hide content
                const individualMode = document.getElementById('individual-mode');
                const templateMode = document.getElementById('template-mode');
                if (individualMode && templateMode) {
                    individualMode.classList.add('d-none');
                    templateMode.classList.remove('d-none');
                }
                
                // Load templates when switching to template mode
                this.loadTemplates();
                
                // Update buttons
                this.updateButtons();
            });
        }
    },

    // Select block type
    selectBlockType: function(type) {
        // Remove previous selection
        document.querySelectorAll('.block-type-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        // Select new type
        const selectedCard = document.querySelector(`[data-block-type="${type}"]`);
        if (selectedCard) {
            selectedCard.classList.add('selected');
        }
        
        // Update wizard state
        this.wizard.selectedType = type;
        
        // Load type-specific configuration
        this.loadTypeConfiguration(type);
        
        // Enable next button
        this.updateButtons();
    },

    // Load type-specific configuration
    loadTypeConfiguration: function(type) {
        const configContent = document.getElementById('type-config-content');
        if (!configContent) return;
        
        // This would load type-specific form fields
        // For now, we'll use a basic implementation
        const configs = {
            'task': this.getTaskConfig(),
            'note': this.getNoteConfig(),
            'kanban': this.getKanbanConfig(),
            'objective': this.getObjectiveConfig(),
            'calendar': this.getCalendarConfig(),
            'habit': this.getHabitConfig()
        };
        
        configContent.innerHTML = configs[type] || '';
        
        // Initialize wizard config for this type
        this.wizard.config = {};
    },

    // Get task-specific configuration
    getTaskConfig: function() {
        return `
            <div class="row">
                <div class="col-md-6">
                    <div class="form-group">
                        <label for="due_date">Fecha límite</label>
                        <input type="date" class="form-control" name="due_date" id="due_date">
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="form-group">
                        <label for="priority">Prioridad</label>
                        <select class="form-control" name="priority" id="priority">
                            <option value="low">Baja</option>
                            <option value="medium" selected>Media</option>
                            <option value="high">Alta</option>
                        </select>
                    </div>
                </div>
            </div>
            <div class="form-group">
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" name="show_progress" id="show_progress">
                    <label class="form-check-label" for="show_progress">
                        Mostrar progreso
                    </label>
                </div>
            </div>
        `;
    },

    // Get note-specific configuration
    getNoteConfig: function() {
        return `
            <div class="form-group">
                <label for="note_type">Tipo de nota</label>
                <select class="form-control" name="note_type" id="note_type">
                    <option value="text">Texto</option>
                    <option value="markdown">Markdown</option>
                    <option value="rich">Texto enriquecido</option>
                </select>
            </div>
            <div class="form-group">
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" name="auto_save" id="auto_save" checked>
                    <label class="form-check-label" for="auto_save">
                        Guardado automático
                    </label>
                </div>
            </div>
        `;
    },

    // Get kanban-specific configuration
    getKanbanConfig: function() {
        return `
            <div class="form-group">
                <label for="columns">Columnas iniciales (separadas por coma)</label>
                <input type="text" class="form-control" name="columns" id="columns" 
                       value="Por hacer, En progreso, Completado" placeholder="Por hacer, En progreso, Completado">
            </div>
            <div class="form-group">
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" name="allow_drag" id="allow_drag" checked>
                    <label class="form-check-label" for="allow_drag">
                        Permitir arrastrar tarjetas
                    </label>
                </div>
            </div>
        `;
    },

    // Get objective-specific configuration
    getObjectiveConfig: function() {
        return `
            <div class="row">
                <div class="col-md-6">
                    <div class="form-group">
                        <label for="target_date">Fecha objetivo</label>
                        <input type="date" class="form-control" name="target_date" id="target_date">
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="form-group">
                        <label for="progress_type">Tipo de progreso</label>
                        <select class="form-control" name="progress_type" id="progress_type">
                            <option value="percentage">Porcentaje</option>
                            <option value="tasks">Tareas</option>
                            <option value="milestones">Hitos</option>
                        </select>
                    </div>
                </div>
            </div>
        `;
    },

    // Get calendar-specific configuration
    getCalendarConfig: function() {
        return `
            <div class="form-group">
                <label for="view_type">Vista predeterminada</label>
                <select class="form-control" name="view_type" id="view_type">
                    <option value="month">Mes</option>
                    <option value="week">Semana</option>
                    <option value="day">Día</option>
                </select>
            </div>
            <div class="form-group">
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" name="show_weekends" id="show_weekends" checked>
                    <label class="form-check-label" for="show_weekends">
                        Mostrar fines de semana
                    </label>
                </div>
            </div>
        `;
    },

    // Get habit-specific configuration
    getHabitConfig: function() {
        return `
            <div class="row">
                <div class="col-md-6">
                    <div class="form-group">
                        <label for="frequency">Frecuencia</label>
                        <select class="form-control" name="frequency" id="frequency">
                            <option value="daily">Diario</option>
                            <option value="weekly">Semanal</option>
                            <option value="monthly">Mensual</option>
                        </select>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="form-group">
                        <label for="target_count">Meta (veces)</label>
                        <input type="number" class="form-control" name="target_count" id="target_count" value="1" min="1">
                    </div>
                </div>
            </div>
            <div class="form-group">
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" name="daily_reminders" id="daily_reminders">
                    <label class="form-check-label" for="daily_reminders">
                        Recordatorios diarios
                    </label>
                </div>
            </div>
        `;
    },

    // Navigate to next step
    nextStep: function() {
        if (this.wizard.step < this.totalSteps && this.canProceedToNextStep()) {
            this.wizard.step++;
            this.showStep(this.wizard.step);
            this.updateStepIndicator();
            this.updateButtons();
            
            // Update preview when moving to customization step
            if (this.wizard.step === 3) {
                this.updatePreview();
            }
        }
    },

    // Navigate to previous step
    previousStep: function() {
        if (this.wizard.step > 1) {
            this.wizard.step--;
            this.showStep(this.wizard.step);
            this.updateStepIndicator();
            this.updateButtons();
        }
    },

    // Show specific step
    showStep: function(step) {
        // Hide all steps
        document.querySelectorAll('.factory-step').forEach(stepEl => {
            stepEl.classList.add('d-none');
        });
        
        // Show current step
        const currentStepEl = document.getElementById(`step-${step}`);
        if (currentStepEl) {
            currentStepEl.classList.remove('d-none');
        }
    },

    // Update step indicator
    updateStepIndicator: function() {
        document.querySelectorAll('.step-indicator .step').forEach((step, index) => {
            const stepNumber = index + 1;
            if (stepNumber < this.wizard.step) {
                step.classList.add('completed');
                step.classList.remove('active');
            } else if (stepNumber === this.wizard.step) {
                step.classList.add('active');
                step.classList.remove('completed');
            } else {
                step.classList.remove('active', 'completed');
            }
        });
    },

    // Update navigation buttons
    updateButtons: function() {
        const prevBtn = document.getElementById('prev-step-btn');
        const nextBtn = document.getElementById('next-step-btn');
        const createBtn = document.getElementById('create-block-btn');
        
        // Previous button
        if (prevBtn) {
            prevBtn.style.display = this.wizard.step > 1 ? 'inline-block' : 'none';
        }
        
        // Next/Create buttons
        if (this.wizard.step < this.totalSteps) {
            if (nextBtn) {
                nextBtn.style.display = 'inline-block';
                nextBtn.disabled = !this.canProceedToNextStep();
            }
            if (createBtn) {
                createBtn.style.display = 'none';
            }
        } else {
            if (nextBtn) {
                nextBtn.style.display = 'none';
            }
            if (createBtn) {
                createBtn.style.display = 'inline-block';
                createBtn.disabled = !this.validateCurrentStep();
            }
        }
    },

    // Check if can proceed to next step
    canProceedToNextStep: function() {
        switch (this.wizard.step) {
            case 1:
                if (this.isTemplateMode()) {
                    return this.selectedTemplate !== null;
                } else {
                    return this.wizard.selectedType !== null;
                }
            case 2:
                return this.validateConfigurationForm();
            case 3:
                return true; // Customization is optional
            default:
                return false;
        }
    },

    // Validate current step
    validateCurrentStep: function() {
        if (this.wizard.step === 1 && this.isTemplateMode()) {
            return this.selectedTemplate !== null;
        }
        
        if (this.wizard.step === 2) {
            return this.validateConfigurationForm();
        }
        
        return true;
    },

    // Validate configuration form
    validateConfigurationForm: function() {
        const titleInput = document.querySelector('input[name="title"]');
        return titleInput && titleInput.value.trim() !== '';
    },

    // Select color
    selectColor: function(color) {
        // Remove previous selection
        document.querySelectorAll('.color-option').forEach(option => {
            option.classList.remove('selected');
        });
        
        // Select new color
        const selectedOption = document.querySelector(`[data-color="${color}"]`);
        if (selectedOption) {
            selectedOption.classList.add('selected');
        }
        
        // Update hidden input
        const hiddenInput = document.getElementById('theme_color');
        if (hiddenInput) {
            hiddenInput.value = color;
        }
        
        this.updatePreview();
    },

    // Update preview
    updatePreview: function() {
        const previewBlock = document.getElementById('preview-block');
        if (!previewBlock) return;
        
        // Get form data
        const title = document.querySelector('input[name="title"]')?.value || 'Título del bloque';
        const themeColor = document.getElementById('theme_color')?.value || 'purple';
        const showBorder = document.getElementById('show_border')?.checked;
        const showShadow = document.getElementById('show_shadow')?.checked;
        
        // Update preview
        const previewTitle = previewBlock.querySelector('.preview-title');
        if (previewTitle) {
            previewTitle.textContent = title;
        }
        
        // Apply theme color
        const colorMap = {
            blue: '#3182ce',
            green: '#38a169',
            purple: '#9f7aea',
            orange: '#d69e2e',
            red: '#e53e3e',
            teal: '#319795',
            pink: '#d53f8c',
            gray: '#718096'
        };
        
        const color = colorMap[themeColor] || colorMap.purple;
        previewBlock.style.borderColor = color;
        
        // Apply border and shadow
        previewBlock.style.border = showBorder ? `2px solid ${color}` : 'none';
        previewBlock.style.boxShadow = showShadow ? '0 4px 12px rgba(0, 0, 0, 0.15)' : 'none';
    },

    // Create block or apply template
    createBlock: async function() {
        // If in template mode, apply template instead
        if (this.isTemplateMode()) {
            await this.applyTemplate();
            return;
        }
        
        try {
            // Collect all form data
            const blockData = this.collectBlockData();
            
            // Show loading state
            const createBtn = document.getElementById('create-block-btn');
            if (createBtn) {
                createBtn.disabled = true;
                createBtn.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Creando...';
            }
            
            // Send to server
            const response = await fetch('/api/personal-space/blocks', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(blockData)
            });
            
            if (response.ok) {
                const result = await response.json();
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('block-factory-modal'));
                if (modal) {
                    modal.hide();
                }
                
                // Refresh workspace
                if (window.WorkspaceLayout && window.WorkspaceLayout.refreshBlocks) {
                    window.WorkspaceLayout.refreshBlocks();
                } else if (window.loadBlocks) {
                    window.loadBlocks();
                }
                
                // Show success message
                this.showSuccessMessage('Bloque creado exitosamente');
                
                // Reset factory
                this.reset();
            } else {
                throw new Error('Error al crear el bloque');
            }
        } catch (error) {
            console.error('Error creating block:', error);
            this.showErrorMessage('Error al crear el bloque. Inténtalo de nuevo.');
        } finally {
            // Reset button
            const createBtn = document.getElementById('create-block-btn');
            if (createBtn) {
                createBtn.disabled = false;
                createBtn.innerHTML = '<i class="bi bi-plus-circle me-2"></i>Crear Bloque';
            }
        }
    },

    // Collect all block data
    collectBlockData: function() {
        const data = {
            type: this.wizard.selectedType,
            title: document.querySelector('input[name="title"]')?.value || '',
            content: document.querySelector('textarea[name="description"]')?.value || '',
            metadata: {
                category: document.querySelector('select[name="category"]')?.value || 'personal',
                priority: document.querySelector('select[name="priority"]')?.value || 'medium',
                size: document.querySelector('select[name="size"]')?.value || 'medium',
                position_x: parseInt(document.querySelector('input[name="position_x"]')?.value) || 0,
                position_y: parseInt(document.querySelector('input[name="position_y"]')?.value) || 0,
                theme_color: document.getElementById('theme_color')?.value || 'purple',
                header_style: document.querySelector('select[name="header_style"]')?.value || 'default',
                show_border: document.getElementById('show_border')?.checked || false,
                show_shadow: document.getElementById('show_shadow')?.checked || false,
                auto_save: document.getElementById('auto_save')?.checked || false,
                notifications: document.getElementById('notifications')?.checked || false,
                collaborative: document.getElementById('collaborative')?.checked || false,
                public_view: document.getElementById('public_view')?.checked || false,
                ...this.collectTypeSpecificConfig()
            }
        };
        
        return data;
    },

    // Collect type-specific configuration
    collectTypeSpecificConfig: function() {
        const config = {};
        const container = document.getElementById('type-config-content');
        if (!container) return config;
        
        // Collect all form inputs in type-specific section
        const inputs = container.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            if (input.type === 'checkbox') {
                config[input.name] = input.checked;
            } else {
                config[input.name] = input.value;
            }
        });
        
        // Store in wizard config
        this.wizard.config = { ...this.wizard.config, ...config };
        
        return config;
    },

    // Get CSRF token
    getCSRFToken: function() {
        const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        return token || '';
    },

    // Show success message
    showSuccessMessage: function(message) {
        // Integration with notification system
        if (window.showNotification) {
            window.showNotification(message, 'success');
        }
    },

    // Show error message
    showErrorMessage: function(message) {
        // Integration with notification system
        if (window.showNotification) {
            window.showNotification(message, 'error');
        } else {
            console.error('Error:', message);
        }
    },

    // Reset factory to initial state
    reset: function() {
        this.wizard = {
            selectedType: null,
            config: {},
            step: 1
        };
        this.selectedTemplate = null;
        
        // Reset forms
        document.getElementById('block-config-form')?.reset();
        document.getElementById('block-customization-form')?.reset();
        
        // Reset creation mode to individual
        const individualTab = document.getElementById('individual-tab');
        const templateTab = document.getElementById('template-tab');
        if (individualTab && templateTab) {
            individualTab.classList.add('active');
            templateTab.classList.remove('active');
            
            const individualMode = document.getElementById('individual-mode');
            const templateMode = document.getElementById('template-mode');
            if (individualMode && templateMode) {
                individualMode.classList.add('show', 'active');
                templateMode.classList.remove('show', 'active');
            }
        }
        
        // Reset UI
        document.querySelectorAll('.block-type-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        document.querySelectorAll('.color-option').forEach(option => {
            option.classList.remove('selected');
        });
        
        // Show first step
        this.showStep(1);
        this.updateStepIndicator();
        this.updateButtons();
    },

    // Template-related functions
    // Load templates
    loadTemplates: async function() {
        try {
            const response = await fetch('/api/personal-space/templates?public=true');
            if (response.ok) {
                this.templates = await response.json();
                this.renderTemplates();
            } else {
                throw new Error('Error loading templates');
            }
        } catch (error) {
            console.error('Error loading templates:', error);
            this.showTemplateError('Error al cargar las plantillas');
        }
    },

    // Render templates in grid
    renderTemplates: function(filteredTemplates = null) {
        const templatesGrid = document.getElementById('templates-grid');
        if (!templatesGrid) return;
        
        const templates = filteredTemplates || this.templates;
        
        if (templates.length === 0) {
            templatesGrid.innerHTML = `
                <div class="text-center py-4">
                    <i class="bi bi-collection text-muted" style="font-size: 2rem;"></i>
                    <p class="mt-2 text-muted">No hay plantillas disponibles</p>
                </div>
            `;
            return;
        }
        
        templatesGrid.innerHTML = templates.map(template => `
            <div class="template-card" data-template-id="${template.id}" onclick="window.BlockFactory.selectTemplate('${template.id}')">
                <div class="template-title">${template.name}</div>
                <div class="template-description">${template.description || 'Sin descripción'}</div>
                <div class="template-blocks-count">${template.blocks_count || 0} bloques</div>
            </div>
        `).join('');
    },

    // Select template
    selectTemplate: function(templateId) {
        // Remove previous selection
        document.querySelectorAll('.template-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        // Select new template
        const selectedCard = document.querySelector(`[data-template-id="${templateId}"]`);
        if (selectedCard) {
            selectedCard.classList.add('selected');
        }
        
        this.selectedTemplate = templateId;
        
        // Enable next button
        this.updateButtons();
    },

    // Filter templates by category
    filterTemplates: function(category) {
        // Update active category button
        document.querySelectorAll('.template-categories .btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        const activeBtn = document.querySelector(`[data-category="${category}"]`);
        if (activeBtn) {
            activeBtn.classList.add('active');
        }
        
        // Filter templates
        let filteredTemplates = this.templates;
        if (category !== 'all') {
            filteredTemplates = this.templates.filter(template => 
                template.category === category
            );
        }
        
        this.renderTemplates(filteredTemplates);
    },

    // Search templates
    searchTemplates: function(query) {
        const filteredTemplates = this.templates.filter(template =>
            template.name.toLowerCase().includes(query.toLowerCase()) ||
            (template.description && template.description.toLowerCase().includes(query.toLowerCase()))
        );
        
        this.renderTemplates(filteredTemplates);
    },

    // Apply selected template
    applyTemplate: async function() {
        if (!this.selectedTemplate) return;
        
        try {
            const response = await fetch(`/api/personal-space/templates/${this.selectedTemplate}/apply`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            if (response.ok) {
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('block-factory-modal'));
                if (modal) {
                    modal.hide();
                }
                
                // Refresh workspace
                if (window.WorkspaceLayout && window.WorkspaceLayout.refreshBlocks) {
                    window.WorkspaceLayout.refreshBlocks();
                } else if (window.loadBlocks) {
                    window.loadBlocks();
                }
                
                this.showSuccessMessage('Plantilla aplicada exitosamente');
                this.reset();
            } else {
                throw new Error('Error applying template');
            }
        } catch (error) {
            console.error('Error applying template:', error);
            this.showErrorMessage('Error al aplicar la plantilla. Inténtalo de nuevo.');
        }
    },

    // Show template error
    showTemplateError: function(message) {
        const templatesGrid = document.getElementById('templates-grid');
        if (templatesGrid) {
            templatesGrid.innerHTML = `
                <div class="text-center py-4 text-danger">
                    <i class="bi bi-exclamation-triangle" style="font-size: 2rem;"></i>
                    <p class="mt-2">${message}</p>
                </div>
            `;
        }
    },

    // Check if template mode is active
    isTemplateMode: function() {
        const templateTab = document.getElementById('template-tab');
        return templateTab && templateTab.classList.contains('active');
    }
};

// Global functions removed - now using event delegation

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('block-factory-modal');
    if (modal) {
        modal.addEventListener('shown.bs.modal', function() {
            window.BlockFactory.init();
        });
        
        modal.addEventListener('hidden.bs.modal', function() {
            window.BlockFactory.reset();
        });
    }
});