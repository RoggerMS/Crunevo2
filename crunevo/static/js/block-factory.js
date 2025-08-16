/**
 * BlockFactory - Sistema de creación de bloques para Personal Space
 * Soluciona el error: Cannot read properties of undefined (reading 'selectBlockType')
 */

window.BlockFactory = {
    currentStep: 1,
    selectedType: null,
    blockData: {},
    maxSteps: 3,
    
    /**
     * Inicializar el BlockFactory
     */
    init() {
        console.log('BlockFactory initialized');
        this.currentStep = 1;
        this.selectedType = null;
        this.blockData = {};
        this.updateStepIndicator();
        this.setupEventListeners();
    },
    
    /**
     * Seleccionar tipo de bloque y avanzar al siguiente paso
     * @param {string} type - Tipo de bloque seleccionado
     */
    selectBlockType(type) {
        console.log('Selecting block type:', type);
        this.selectedType = type;
        this.blockData.block_type = type;
        
        // Remover selección anterior
        document.querySelectorAll('.block-type-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        // Marcar como seleccionado
        const selectedCard = document.querySelector(`[data-type="${type}"]`);
        if (selectedCard) {
            selectedCard.classList.add('selected');
        }
        
        // Habilitar botón siguiente
        const nextBtn = document.querySelector('#factory-next-btn');
        if (nextBtn) {
            nextBtn.disabled = false;
            nextBtn.classList.remove('disabled');
        }
        
        // Auto-avanzar después de un breve delay
        setTimeout(() => {
            this.nextStep();
        }, 500);
    },
    
    /**
     * Avanzar al siguiente paso
     */
    nextStep() {
        if (!this.validateCurrentStep()) {
            return;
        }
        
        if (this.currentStep < this.maxSteps) {
            this.currentStep++;
            this.showStep(this.currentStep);
            this.updateStepIndicator();
        }
    },
    
    /**
     * Retroceder al paso anterior
     */
    previousStep() {
        if (this.currentStep > 1) {
            this.currentStep--;
            this.showStep(this.currentStep);
            this.updateStepIndicator();
        }
    },
    
    /**
     * Mostrar paso específico
     * @param {number} stepNumber - Número del paso a mostrar
     */
    showStep(stepNumber) {
        // Ocultar todos los pasos
        document.querySelectorAll('.factory-step').forEach(step => {
            step.style.display = 'none';
            step.classList.remove('active');
        });
        
        // Mostrar paso actual
        const currentStepEl = document.querySelector(`#factory-step-${stepNumber}`);
        if (currentStepEl) {
            currentStepEl.style.display = 'block';
            currentStepEl.classList.add('active');
        }
        
        // Actualizar botones de navegación
        this.updateNavigationButtons();
    },
    
    /**
     * Actualizar indicador visual de pasos
     */
    updateStepIndicator() {
        const indicators = document.querySelectorAll('.step-indicator');
        indicators.forEach((indicator, index) => {
            const stepNum = index + 1;
            indicator.classList.remove('active', 'completed');
            
            if (stepNum < this.currentStep) {
                indicator.classList.add('completed');
            } else if (stepNum === this.currentStep) {
                indicator.classList.add('active');
            }
        });
    },
    
    /**
     * Actualizar estado de botones de navegación
     */
    updateNavigationButtons() {
        const prevBtn = document.querySelector('#factory-prev-btn');
        const nextBtn = document.querySelector('#factory-next-btn');
        const createBtn = document.querySelector('#factory-create-btn');
        
        if (prevBtn) {
            prevBtn.style.display = this.currentStep > 1 ? 'inline-block' : 'none';
        }
        
        if (nextBtn) {
            nextBtn.style.display = this.currentStep < this.maxSteps ? 'inline-block' : 'none';
            nextBtn.disabled = !this.validateCurrentStep();
        }
        
        if (createBtn) {
            createBtn.style.display = this.currentStep === this.maxSteps ? 'inline-block' : 'none';
        }
    },
    
    /**
     * Validar datos del paso actual
     * @returns {boolean} - True si el paso es válido
     */
    validateCurrentStep() {
        switch (this.currentStep) {
            case 1:
                return this.selectedType !== null;
            case 2:
                const title = document.querySelector('#block-title')?.value;
                return title && title.trim().length > 0;
            case 3:
                return true; // Paso de personalización siempre válido
            default:
                return false;
        }
    },
    
    /**
     * Recopilar datos del formulario
     */
    collectFormData() {
        // Datos básicos
        const title = document.querySelector('#block-title')?.value || '';
        const description = document.querySelector('#block-description')?.value || '';
        const color = document.querySelector('#block-color')?.value || '#3b82f6';
        const size = document.querySelector('input[name="block-size"]:checked')?.value || 'medium';
        const isPublic = document.querySelector('#block-public')?.checked || false;
        
        this.blockData = {
            ...this.blockData,
            title: title.trim(),
            description: description.trim(),
            color: color,
            size: size,
            is_public: isPublic,
            metadata: this.getTypeSpecificMetadata()
        };
    },
    
    /**
     * Obtener metadatos específicos del tipo de bloque
     * @returns {object} - Metadatos específicos
     */
    getTypeSpecificMetadata() {
        const metadata = {};
        
        switch (this.selectedType) {
            case 'kanban':
                metadata.columns = ['Por hacer', 'En progreso', 'Completado'];
                break;
            case 'calendar':
                metadata.view_type = 'month';
                metadata.show_weekends = true;
                break;
            case 'chart':
                metadata.chart_type = 'line';
                metadata.data_source = 'manual';
                break;
            case 'objectives':
                metadata.target_date = null;
                metadata.priority = 'medium';
                break;
            default:
                break;
        }
        
        return metadata;
    },
    
    /**
     * Crear bloque final
     */
    async createBlock() {
        try {
            // Recopilar datos del formulario
            this.collectFormData();
            
            // Validar datos
            if (!this.blockData.title || !this.blockData.block_type) {
                throw new Error('Título y tipo de bloque son requeridos');
            }
            
            // Mostrar loading
            this.showLoading(true);
            
            // Enviar petición al backend
            const response = await fetch('/api/personal-space/blocks', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(this.blockData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Éxito - cerrar modal y actualizar UI
                this.showSuccess('Bloque creado exitosamente');
                this.closeModal();
                this.refreshWorkspace();
            } else {
                throw new Error(result.error || 'Error al crear el bloque');
            }
            
        } catch (error) {
            console.error('Error creating block:', error);
            this.showError(error.message);
        } finally {
            this.showLoading(false);
        }
    },
    
    /**
     * Configurar event listeners
     */
    setupEventListeners() {
        // Botones de navegación
        const prevBtn = document.querySelector('#factory-prev-btn');
        const nextBtn = document.querySelector('#factory-next-btn');
        const createBtn = document.querySelector('#factory-create-btn');
        
        if (prevBtn) {
            prevBtn.addEventListener('click', () => this.previousStep());
        }
        
        if (nextBtn) {
            nextBtn.addEventListener('click', () => this.nextStep());
        }
        
        if (createBtn) {
            createBtn.addEventListener('click', () => this.createBlock());
        }
        
        // Campos del formulario
        const titleInput = document.querySelector('#block-title');
        if (titleInput) {
            titleInput.addEventListener('input', () => this.updateNavigationButtons());
        }
    },
    
    /**
     * Obtener CSRF token
     * @returns {string} - CSRF token
     */
    getCSRFToken() {
        const token = document.querySelector('meta[name=csrf-token]')?.getAttribute('content');
        return token || '';
    },
    
    /**
     * Mostrar/ocultar loading
     * @param {boolean} show - Mostrar loading
     */
    showLoading(show) {
        const createBtn = document.querySelector('#factory-create-btn');
        if (createBtn) {
            createBtn.disabled = show;
            createBtn.innerHTML = show ? 
                '<i class="fas fa-spinner fa-spin"></i> Creando...' : 
                '<i class="fas fa-plus"></i> Crear Bloque';
        }
    },
    
    /**
     * Mostrar mensaje de éxito
     * @param {string} message - Mensaje de éxito
     */
    showSuccess(message) {
        // Implementar notificación de éxito
        console.log('Success:', message);
        if (window.showNotification) {
            window.showNotification(message, 'success');
        }
    },
    
    /**
     * Mostrar mensaje de error
     * @param {string} message - Mensaje de error
     */
    showError(message) {
        // Implementar notificación de error
        console.error('Error:', message);
        if (window.showNotification) {
            window.showNotification(message, 'error');
        } else {
            alert('Error: ' + message);
        }
    },
    
    /**
     * Cerrar modal
     */
    closeModal() {
        const modal = document.querySelector('#block-factory-modal');
        if (modal) {
            modal.style.display = 'none';
            modal.classList.remove('show');
        }
        
        // Reset factory state
        this.currentStep = 1;
        this.selectedType = null;
        this.blockData = {};
    },
    
    /**
     * Actualizar workspace después de crear bloque
     */
    refreshWorkspace() {
        // Recargar bloques en el workspace
        if (window.PersonalSpaceManager && window.PersonalSpaceManager.loadBlocks) {
            window.PersonalSpaceManager.loadBlocks();
        } else if (window.loadBlocks) {
            window.loadBlocks();
        } else {
            // Fallback: recargar página
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        }
    }
};

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Esperar un poco para asegurar que otros scripts se hayan cargado
    setTimeout(() => {
        if (window.BlockFactory) {
            window.BlockFactory.init();
        }
    }, 100);
});

// Exportar para uso global
if (typeof module !== 'undefined' && module.exports) {
    module.exports = window.BlockFactory;
}