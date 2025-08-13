/**
 * Comprehensive Frontend Validation System
 * Provides robust client-side validation with real-time feedback
 */

class ValidationSystem {
    constructor() {
        this.validators = new Map();
        this.errorMessages = new Map();
        this.validationRules = new Map();
        this.debounceTimers = new Map();
        this.initializeDefaultValidators();
        this.initializeErrorMessages();
        this.initializeBlockValidationRules();
    }

    /**
     * Initialize default validation functions
     */
    initializeDefaultValidators() {
        // Required field validator
        this.validators.set('required', (value, options = {}) => {
            if (value === null || value === undefined || value === '') {
                return { valid: false, message: options.message || 'Este campo es obligatorio' };
            }
            return { valid: true };
        });

        // String length validator
        this.validators.set('length', (value, options = {}) => {
            if (typeof value !== 'string') {
                value = String(value || '');
            }
            
            const length = value.length;
            
            if (options.min && length < options.min) {
                return { 
                    valid: false, 
                    message: `Debe tener al menos ${options.min} caracteres` 
                };
            }
            
            if (options.max && length > options.max) {
                return { 
                    valid: false, 
                    message: `No puede exceder ${options.max} caracteres` 
                };
            }
            
            return { valid: true };
        });

        // Email validator
        this.validators.set('email', (value, options = {}) => {
            if (!value) return { valid: true }; // Allow empty if not required
            
            const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
            if (!emailRegex.test(value)) {
                return { 
                    valid: false, 
                    message: options.message || 'Ingrese un email válido' 
                };
            }
            
            return { valid: true };
        });

        // Number range validator
        this.validators.set('range', (value, options = {}) => {
            const num = parseFloat(value);
            
            if (isNaN(num)) {
                return { 
                    valid: false, 
                    message: 'Debe ser un número válido' 
                };
            }
            
            if (options.min !== undefined && num < options.min) {
                return { 
                    valid: false, 
                    message: `El valor mínimo es ${options.min}` 
                };
            }
            
            if (options.max !== undefined && num > options.max) {
                return { 
                    valid: false, 
                    message: `El valor máximo es ${options.max}` 
                };
            }
            
            return { valid: true };
        });

        // Date validator
        this.validators.set('date', (value, options = {}) => {
            if (!value) return { valid: true };
            
            const date = new Date(value);
            if (isNaN(date.getTime())) {
                return { 
                    valid: false, 
                    message: 'Ingrese una fecha válida' 
                };
            }
            
            if (options.min) {
                const minDate = new Date(options.min);
                if (date < minDate) {
                    return { 
                        valid: false, 
                        message: `La fecha debe ser posterior a ${minDate.toLocaleDateString()}` 
                    };
                }
            }
            
            if (options.max) {
                const maxDate = new Date(options.max);
                if (date > maxDate) {
                    return { 
                        valid: false, 
                        message: `La fecha debe ser anterior a ${maxDate.toLocaleDateString()}` 
                    };
                }
            }
            
            return { valid: true };
        });

        // Choice validator
        this.validators.set('choice', (value, options = {}) => {
            if (!options.choices || !Array.isArray(options.choices)) {
                return { valid: true };
            }
            
            if (!options.choices.includes(value)) {
                return { 
                    valid: false, 
                    message: `Debe seleccionar una opción válida: ${options.choices.join(', ')}` 
                };
            }
            
            return { valid: true };
        });

        // Custom pattern validator
        this.validators.set('pattern', (value, options = {}) => {
            if (!value || !options.pattern) return { valid: true };
            
            const regex = new RegExp(options.pattern);
            if (!regex.test(value)) {
                return { 
                    valid: false, 
                    message: options.message || 'El formato no es válido' 
                };
            }
            
            return { valid: true };
        });

        // Safe HTML validator
        this.validators.set('safeHtml', (value, options = {}) => {
            if (!value) return { valid: true };
            
            // Check for potentially dangerous content
            const dangerousPatterns = [
                /<script[^>]*>.*?<\/script>/gi,
                /javascript:/gi,
                /on\w+\s*=/gi,
                /<iframe[^>]*>/gi
            ];
            
            for (const pattern of dangerousPatterns) {
                if (pattern.test(value)) {
                    return { 
                        valid: false, 
                        message: 'El contenido contiene elementos no permitidos' 
                    };
                }
            }
            
            return { valid: true };
        });
    }

    /**
     * Initialize error message templates
     */
    initializeErrorMessages() {
        this.errorMessages.set('REQUIRED_FIELD', 'Este campo es obligatorio');
        this.errorMessages.set('INVALID_EMAIL', 'Ingrese un email válido');
        this.errorMessages.set('INVALID_DATE', 'Ingrese una fecha válida');
        this.errorMessages.set('MIN_LENGTH', 'Muy corto');
        this.errorMessages.set('MAX_LENGTH', 'Muy largo');
        this.errorMessages.set('INVALID_CHOICE', 'Selección no válida');
        this.errorMessages.set('INVALID_NUMBER', 'Debe ser un número');
        this.errorMessages.set('UNSAFE_CONTENT', 'Contenido no permitido');
    }

    /**
     * Initialize block-specific validation rules
     */
    initializeBlockValidationRules() {
        // Task block validation
        this.validationRules.set('tarea', {
            title: [
                { validator: 'required' },
                { validator: 'length', options: { min: 1, max: 255 } },
                { validator: 'safeHtml' }
            ],
            content: [
                { validator: 'length', options: { max: 5000 } },
                { validator: 'safeHtml' }
            ],
            priority: [
                { validator: 'choice', options: { choices: ['low', 'medium', 'high', 'urgent'] } }
            ],
            due_date: [
                { validator: 'date', options: { min: new Date().toISOString().split('T')[0] } }
            ]
        });

        // Objective block validation
        this.validationRules.set('objetivo', {
            title: [
                { validator: 'required' },
                { validator: 'length', options: { min: 1, max: 255 } },
                { validator: 'safeHtml' }
            ],
            content: [
                { validator: 'length', options: { max: 10000 } },
                { validator: 'safeHtml' }
            ],
            progress: [
                { validator: 'range', options: { min: 0, max: 100 } }
            ],
            status: [
                { validator: 'choice', options: { choices: ['no_iniciada', 'en_progreso', 'cumplida', 'pausada'] } }
            ]
        });

        // Note block validation
        this.validationRules.set('nota', {
            title: [
                { validator: 'required' },
                { validator: 'length', options: { min: 1, max: 255 } },
                { validator: 'safeHtml' }
            ],
            content: [
                { validator: 'length', options: { max: 50000 } },
                { validator: 'safeHtml' }
            ]
        });

        // List block validation
        this.validationRules.set('lista', {
            title: [
                { validator: 'required' },
                { validator: 'length', options: { min: 1, max: 255 } },
                { validator: 'safeHtml' }
            ],
            content: [
                { validator: 'length', options: { max: 10000 } },
                { validator: 'safeHtml' }
            ]
        });

        // Kanban block validation
        this.validationRules.set('kanban', {
            title: [
                { validator: 'required' },
                { validator: 'length', options: { min: 1, max: 255 } },
                { validator: 'safeHtml' }
            ],
            content: [
                { validator: 'length', options: { max: 20000 } },
                { validator: 'safeHtml' }
            ]
        });

        // Reminder block validation
        this.validationRules.set('recordatorio', {
            title: [
                { validator: 'required' },
                { validator: 'length', options: { min: 1, max: 255 } },
                { validator: 'safeHtml' }
            ],
            content: [
                { validator: 'length', options: { max: 2000 } },
                { validator: 'safeHtml' }
            ],
            due_date: [
                { validator: 'required' },
                { validator: 'date', options: { min: new Date().toISOString().split('T')[0] } }
            ],
            priority: [
                { validator: 'choice', options: { choices: ['low', 'medium', 'high', 'urgent'] } }
            ]
        });
    }

    /**
     * Validate a single field
     */
    validateField(fieldName, value, blockType = null, customRules = null) {
        const rules = customRules || this.getFieldRules(fieldName, blockType);
        const results = [];
        
        if (!rules || rules.length === 0) {
            return { valid: true, errors: [], warnings: [] };
        }

        for (const rule of rules) {
            const validator = this.validators.get(rule.validator);
            if (!validator) {
                console.warn(`Unknown validator: ${rule.validator}`);
                continue;
            }

            const result = validator(value, rule.options || {});
            if (!result.valid) {
                results.push({
                    field: fieldName,
                    message: result.message,
                    code: rule.validator.toUpperCase(),
                    severity: rule.severity || 'error'
                });
            }
        }

        const errors = results.filter(r => r.severity === 'error');
        const warnings = results.filter(r => r.severity === 'warning');

        return {
            valid: errors.length === 0,
            errors,
            warnings
        };
    }

    /**
     * Validate an entire form or block data
     */
    validateBlock(blockData, blockType) {
        const allErrors = [];
        const allWarnings = [];
        const fieldResults = {};

        // Get validation rules for this block type
        const blockRules = this.validationRules.get(blockType);
        if (!blockRules) {
            return {
                valid: true,
                errors: [],
                warnings: [],
                fieldResults: {}
            };
        }

        // Validate each field
        for (const [fieldName, rules] of Object.entries(blockRules)) {
            const fieldValue = blockData[fieldName];
            const result = this.validateField(fieldName, fieldValue, blockType, rules);
            
            fieldResults[fieldName] = result;
            allErrors.push(...result.errors);
            allWarnings.push(...result.warnings);
        }

        // Cross-field validation
        const crossValidationResults = this.performCrossValidation(blockData, blockType);
        allErrors.push(...crossValidationResults.errors);
        allWarnings.push(...crossValidationResults.warnings);

        return {
            valid: allErrors.length === 0,
            errors: allErrors,
            warnings: allWarnings,
            fieldResults
        };
    }

    /**
     * Perform cross-field validation
     */
    performCrossValidation(blockData, blockType) {
        const errors = [];
        const warnings = [];

        // Date consistency validation
        if (blockData.due_date && blockData.target_date) {
            const dueDate = new Date(blockData.due_date);
            const targetDate = new Date(blockData.target_date);
            
            if (dueDate > targetDate) {
                errors.push({
                    field: 'due_date',
                    message: 'La fecha de vencimiento no puede ser posterior a la fecha objetivo',
                    code: 'DATE_INCONSISTENCY'
                });
            }
        }

        // Progress and status consistency for objectives
        if (blockType === 'objetivo') {
            const progress = parseInt(blockData.progress || 0);
            const status = blockData.status;

            if (progress === 100 && status !== 'cumplida') {
                warnings.push({
                    field: 'status',
                    message: 'El estado debería ser "cumplida" cuando el progreso es 100%',
                    code: 'PROGRESS_STATUS_MISMATCH'
                });
            } else if (progress === 0 && status === 'cumplida') {
                errors.push({
                    field: 'progress',
                    message: 'El progreso debe ser mayor a 0% cuando el estado es "cumplida"',
                    code: 'PROGRESS_STATUS_MISMATCH'
                });
            }
        }

        return { errors, warnings };
    }

    /**
     * Get validation rules for a specific field
     */
    getFieldRules(fieldName, blockType) {
        if (!blockType) return [];
        
        const blockRules = this.validationRules.get(blockType);
        return blockRules ? blockRules[fieldName] || [] : [];
    }

    /**
     * Setup real-time validation for a form
     */
    setupFormValidation(formElement, blockType, options = {}) {
        if (!formElement) return;

        const config = {
            validateOnInput: true,
            validateOnBlur: true,
            debounceMs: 300,
            showWarnings: true,
            ...options
        };

        // Find all form fields
        const fields = formElement.querySelectorAll('input, textarea, select');
        
        fields.forEach(field => {
            const fieldName = field.name || field.dataset.field;
            if (!fieldName) return;

            // Setup input validation
            if (config.validateOnInput) {
                field.addEventListener('input', (e) => {
                    this.debounceValidation(fieldName, () => {
                        this.validateFormField(field, blockType, config);
                    }, config.debounceMs);
                });
            }

            // Setup blur validation
            if (config.validateOnBlur) {
                field.addEventListener('blur', () => {
                    this.validateFormField(field, blockType, config);
                });
            }
        });

        // Setup form submission validation
        formElement.addEventListener('submit', (e) => {
            const isValid = this.validateForm(formElement, blockType, config);
            if (!isValid) {
                e.preventDefault();
                e.stopPropagation();
            }
        });
    }

    /**
     * Validate a single form field and show feedback
     */
    validateFormField(fieldElement, blockType, config) {
        const fieldName = fieldElement.name || fieldElement.dataset.field;
        const fieldValue = fieldElement.value;
        
        const result = this.validateField(fieldName, fieldValue, blockType);
        this.showFieldValidationFeedback(fieldElement, result, config);
        
        return result.valid;
    }

    /**
     * Validate entire form
     */
    validateForm(formElement, blockType, config) {
        const formData = new FormData(formElement);
        const blockData = Object.fromEntries(formData.entries());
        
        // Add any additional data from data attributes or other sources
        const additionalFields = formElement.querySelectorAll('[data-field]');
        additionalFields.forEach(field => {
            const fieldName = field.dataset.field;
            if (fieldName && !blockData[fieldName]) {
                blockData[fieldName] = field.value || field.textContent || field.dataset.value;
            }
        });

        const result = this.validateBlock(blockData, blockType);
        
        // Show validation feedback for all fields
        Object.entries(result.fieldResults).forEach(([fieldName, fieldResult]) => {
            const fieldElement = formElement.querySelector(`[name="${fieldName}"], [data-field="${fieldName}"]`);
            if (fieldElement) {
                this.showFieldValidationFeedback(fieldElement, fieldResult, config);
            }
        });

        // Show general form errors
        this.showFormValidationSummary(formElement, result, config);
        
        return result.valid;
    }

    /**
     * Show validation feedback for a field
     */
    showFieldValidationFeedback(fieldElement, result, config) {
        // Remove existing feedback
        this.clearFieldValidationFeedback(fieldElement);

        // Add validation state classes
        fieldElement.classList.remove('is-valid', 'is-invalid', 'has-warning');
        
        if (result.valid) {
            fieldElement.classList.add('is-valid');
        } else {
            fieldElement.classList.add('is-invalid');
        }

        if (result.warnings.length > 0 && config.showWarnings) {
            fieldElement.classList.add('has-warning');
        }

        // Create and show error messages
        if (result.errors.length > 0 || (result.warnings.length > 0 && config.showWarnings)) {
            const feedbackContainer = this.createFieldFeedbackContainer(fieldElement);
            
            result.errors.forEach(error => {
                const errorElement = this.createFeedbackElement(error.message, 'error');
                feedbackContainer.appendChild(errorElement);
            });

            if (config.showWarnings) {
                result.warnings.forEach(warning => {
                    const warningElement = this.createFeedbackElement(warning.message, 'warning');
                    feedbackContainer.appendChild(warningElement);
                });
            }
        }
    }

    /**
     * Clear validation feedback for a field
     */
    clearFieldValidationFeedback(fieldElement) {
        const existingFeedback = fieldElement.parentNode.querySelector('.validation-feedback');
        if (existingFeedback) {
            existingFeedback.remove();
        }
    }

    /**
     * Create feedback container for a field
     */
    createFieldFeedbackContainer(fieldElement) {
        let container = fieldElement.parentNode.querySelector('.validation-feedback');
        
        if (!container) {
            container = document.createElement('div');
            container.className = 'validation-feedback';
            fieldElement.parentNode.appendChild(container);
        }
        
        return container;
    }

    /**
     * Create a feedback element
     */
    createFeedbackElement(message, type) {
        const element = document.createElement('div');
        element.className = `validation-message validation-${type}`;
        element.textContent = message;
        return element;
    }

    /**
     * Show form validation summary
     */
    showFormValidationSummary(formElement, result, config) {
        // Remove existing summary
        const existingSummary = formElement.querySelector('.validation-summary');
        if (existingSummary) {
            existingSummary.remove();
        }

        if (result.errors.length > 0) {
            const summary = document.createElement('div');
            summary.className = 'validation-summary alert alert-danger';
            summary.innerHTML = `
                <h6>Por favor, corrija los siguientes errores:</h6>
                <ul>
                    ${result.errors.map(error => `<li>${error.message}</li>`).join('')}
                </ul>
            `;
            
            formElement.insertBefore(summary, formElement.firstChild);
        }
    }

    /**
     * Debounce validation to avoid excessive calls
     */
    debounceValidation(key, callback, delay) {
        if (this.debounceTimers.has(key)) {
            clearTimeout(this.debounceTimers.get(key));
        }
        
        const timer = setTimeout(callback, delay);
        this.debounceTimers.set(key, timer);
    }

    /**
     * Add custom validator
     */
    addValidator(name, validatorFunction) {
        this.validators.set(name, validatorFunction);
    }

    /**
     * Add validation rules for a block type
     */
    addBlockValidationRules(blockType, rules) {
        this.validationRules.set(blockType, rules);
    }

    /**
     * Get validation summary for display
     */
    getValidationSummary(result) {
        return {
            isValid: result.valid,
            errorCount: result.errors.length,
            warningCount: result.warnings.length,
            errors: result.errors.map(e => e.message),
            warnings: result.warnings.map(w => w.message)
        };
    }
}

// Global validation system instance
window.ValidationSystem = ValidationSystem;
window.validationSystem = new ValidationSystem();

// Auto-initialize validation for forms with data-validate attribute
document.addEventListener('DOMContentLoaded', () => {
    const formsToValidate = document.querySelectorAll('form[data-validate]');
    
    formsToValidate.forEach(form => {
        const blockType = form.dataset.blockType || form.dataset.validate;
        if (blockType) {
            window.validationSystem.setupFormValidation(form, blockType);
        }
    });
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ValidationSystem;
}