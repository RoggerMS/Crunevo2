/**
 * Personal Space - Enhanced JavaScript Module
 * Optimized for performance, accessibility, and user experience
 */

class PersonalSpaceManager {
  constructor() {
    this.blocks = new Map();
    this.sortableInstance = null;
    this.currentEditingBlock = null;
    this.autoSaveTimer = null;
    this.pendingChanges = new Set();
    this.isInitialized = false;
    
    // Configuration
    this.config = {
      autoSaveInterval: 30000,
      debounceDelay: 500,
      maxRetries: 3,
      apiTimeout: 10000
    };
    
    // State management
    this.state = {
      isDarkMode: this.getStoredTheme() === 'dark',
      isFocusMode: localStorage.getItem('focus_mode') === 'on',
      isLoading: false,
      hasUnsavedChanges: false
    };
    
    // Bind methods
    this.handleBlockInteraction = this.handleBlockInteraction.bind(this);
    this.handleKeyboardNavigation = this.handleKeyboardNavigation.bind(this);
    this.autoSave = this.autoSave.bind(this);
  }
  
  /**
   * Initialize the Personal Space system
   */
  async init() {
    if (this.isInitialized) return;
    
    try {
      this.showLoadingState();
      
      // Initialize core components
      await this.initializeComponents();
      
      // Load initial data
      await this.loadBlocks();
      
      // Setup event listeners
      this.setupEventListeners();
      
      // Initialize UI features
      this.initializeUI();
      
      // Setup auto-save
      this.setupAutoSave();
      
      this.isInitialized = true;
      this.hideLoadingState();
      
      this.showNotification('Personal Space cargado correctamente', 'success');
    } catch (error) {
      this.handleError('Error al inicializar Personal Space', error);
    }
  }
  
  /**
   * Initialize core components
   */
  async initializeComponents() {
    // Initialize theme
    this.applyTheme();
    
    // Initialize focus mode
    if (this.state.isFocusMode) {
      this.applyFocusMode(true);
    }
    
    // Initialize sortable if grid exists
    const grid = document.getElementById('blocksGrid');
    if (grid && window.Sortable) {
      this.initializeSortable(grid);
    }
    
    // Setup accessibility features
    this.setupAccessibility();
  }
  
  /**
   * Setup event listeners with proper delegation
   */
  setupEventListeners() {
    // Block interactions
    const grid = document.getElementById('blocksGrid');
    if (grid) {
      grid.addEventListener('click', this.handleBlockInteraction);
      grid.addEventListener('keydown', this.handleKeyboardNavigation);
    }
    
    // Control buttons
    this.bindButton('addBlockBtn', () => this.showAddBlockModal());
    this.bindButton('darkModeToggle', () => this.toggleDarkMode());
    this.bindButton('focusModeBtn', () => this.toggleFocusMode());
    this.bindButton('saveBlockBtn', () => this.saveCurrentBlock());
    
    // Form validation
    document.addEventListener('input', this.debounce(this.validateForm.bind(this), 300));
    
    // Auto-save on content change
    document.addEventListener('input', this.debounce(this.markAsChanged.bind(this), this.config.debounceDelay));
    
    // Prevent data loss
    window.addEventListener('beforeunload', this.handleBeforeUnload.bind(this));
    
    // Handle visibility change for auto-save
    document.addEventListener('visibilitychange', this.handleVisibilityChange.bind(this));
  }
  
  /**
   * Load blocks from API with error handling and retry logic
   */
  async loadBlocks(retryCount = 0) {
    try {
      const response = await this.apiCall('/espacio-personal/api/blocks', {
        method: 'GET',
        timeout: this.config.apiTimeout
      });
      
      if (response.success) {
        this.blocks.clear();
        response.blocks.forEach(block => {
          this.blocks.set(block.id, this.processBlock(block));
        });
        
        this.renderBlocks();
        this.updateDashboardMetrics();
      } else {
        throw new Error(response.error || 'Error al cargar bloques');
      }
    } catch (error) {
      if (retryCount < this.config.maxRetries) {
        await this.delay(1000 * (retryCount + 1));
        return this.loadBlocks(retryCount + 1);
      }
      this.handleError('Error al cargar los bloques', error);
    }
  }
  
  /**
   * Process and enhance block data
   */
  processBlock(block) {
    const metadata = block.metadata || {};
    
    return {
      ...block,
      color: metadata.color || this.getDefaultColor(block.type),
      icon: metadata.icon || this.getDefaultIcon(block.type),
      progress: this.calculateProgress(block),
      lastModified: new Date(block.updated_at),
      isValid: this.validateBlockData(block)
    };
  }
  
  /**
   * Render blocks with performance optimization
   */
  renderBlocks() {
    const grid = document.getElementById('blocksGrid');
    if (!grid) return;
    
    // Use document fragment for better performance
    const fragment = document.createDocumentFragment();
    
    // Clear existing blocks
    grid.innerHTML = '';
    
    if (this.blocks.size === 0) {
      this.renderEmptyState(grid);
      return;
    }
    
    // Sort blocks by order or last modified
    const sortedBlocks = Array.from(this.blocks.values())
      .sort((a, b) => (a.order_index || 0) - (b.order_index || 0));
    
    // Render blocks in batches to avoid blocking UI
    this.renderBlocksBatch(sortedBlocks, fragment, 0, () => {
      grid.appendChild(fragment);
      this.setupBlockAccessibility();
    });
  }
  
  /**
   * Render blocks in batches for better performance
   */
  renderBlocksBatch(blocks, fragment, startIndex, callback, batchSize = 10) {
    const endIndex = Math.min(startIndex + batchSize, blocks.length);
    
    for (let i = startIndex; i < endIndex; i++) {
      const blockElement = this.createBlockElement(blocks[i]);
      fragment.appendChild(blockElement);
    }
    
    if (endIndex < blocks.length) {
      // Continue with next batch
      requestAnimationFrame(() => {
        this.renderBlocksBatch(blocks, fragment, endIndex, callback, batchSize);
      });
    } else {
      callback();
    }
  }
  
  /**
   * Create block element with proper structure and accessibility
   */
  createBlockElement(block) {
    const element = document.createElement('div');
    element.className = `base-block block-type-${block.type} fade-in`;
    element.dataset.blockId = block.id;
    element.setAttribute('role', 'button');
    element.setAttribute('tabindex', '0');
    element.setAttribute('aria-label', `${block.title || 'Bloque sin título'} - ${block.type}`);
    
    element.innerHTML = this.getBlockTemplate(block);
    
    return element;
  }
  
  /**
   * Get block template based on type
   */
  getBlockTemplate(block) {
    const progress = block.progress || 0;
    const hasProgress = progress > 0;
    
    return `
      <div class="drag-handle" aria-hidden="true">
        <i class="bi bi-grip-vertical"></i>
      </div>
      
      <div class="block-header">
        <div class="d-flex align-items-center justify-content-between">
          <div class="d-flex align-items-center gap-3">
            <div class="block-icon ${block.color}">
              <i class="${block.icon}"></i>
            </div>
            <div>
              <h6 class="block-title mb-1">${this.escapeHtml(block.title || 'Sin título')}</h6>
              <span class="block-type-label">${this.getTypeLabel(block.type)}</span>
            </div>
          </div>
          <div class="block-actions">
            <button class="btn btn-ghost btn-sm" data-action="edit" aria-label="Editar bloque">
              <i class="bi bi-pencil"></i>
            </button>
            <button class="btn btn-ghost btn-sm" data-action="delete" aria-label="Eliminar bloque">
              <i class="bi bi-trash"></i>
            </button>
          </div>
        </div>
      </div>
      
      <div class="block-content">
        ${this.getBlockContentTemplate(block)}
      </div>
      
      ${hasProgress ? `
        <div class="block-footer">
          <div class="progress-indicator">
            <div class="progress-bar" style="width: ${progress}%" role="progressbar" aria-valuenow="${progress}" aria-valuemin="0" aria-valuemax="100"></div>
          </div>
          <small class="text-muted">${progress}% completado</small>
        </div>
      ` : ''}
    `;
  }
  
  /**
   * Handle block interactions with proper event delegation
   */
  handleBlockInteraction(event) {
    const blockElement = event.target.closest('.base-block');
    if (!blockElement) return;
    
    const blockId = blockElement.dataset.blockId;
    const action = event.target.closest('[data-action]')?.dataset.action;
    
    event.preventDefault();
    
    switch (action) {
      case 'edit':
        this.editBlock(blockId);
        break;
      case 'delete':
        this.confirmDeleteBlock(blockId);
        break;
      default:
        if (event.type === 'dblclick') {
          this.editBlock(blockId);
        }
        break;
    }
  }
  
  /**
   * Handle keyboard navigation for accessibility
   */
  handleKeyboardNavigation(event) {
    const blockElement = event.target.closest('.base-block');
    if (!blockElement) return;
    
    const blockId = blockElement.dataset.blockId;
    
    switch (event.key) {
      case 'Enter':
      case ' ':
        event.preventDefault();
        this.editBlock(blockId);
        break;
      case 'Delete':
        event.preventDefault();
        this.confirmDeleteBlock(blockId);
        break;
      case 'ArrowRight':
      case 'ArrowDown':
        event.preventDefault();
        this.focusNextBlock(blockElement);
        break;
      case 'ArrowLeft':
      case 'ArrowUp':
        event.preventDefault();
        this.focusPreviousBlock(blockElement);
        break;
    }
  }
  
  /**
   * Validate form data with comprehensive checks
   */
  validateForm(event) {
    const form = event.target.closest('form');
    if (!form) return;
    
    const errors = [];
    const formData = new FormData(form);
    
    // Title validation
    const title = formData.get('title')?.trim();
    if (!title || title.length < 2) {
      errors.push('El título debe tener al menos 2 caracteres');
    } else if (title.length > 255) {
      errors.push('El título no puede exceder 255 caracteres');
    }
    
    // Content validation
    const content = formData.get('content')?.trim();
    if (content && content.length > 10000) {
      errors.push('El contenido no puede exceder 10,000 caracteres');
    }
    
    // Type-specific validation
    const blockType = formData.get('type');
    if (blockType) {
      const typeErrors = this.validateBlockType(blockType, formData);
      errors.push(...typeErrors);
    }
    
    this.displayValidationErrors(form, errors);
    return errors.length === 0;
  }
  
  /**
   * Enhanced error handling with user-friendly messages
   */
  handleError(message, error = null) {
    console.error(message, error);
    
    // Log error for debugging
    if (error) {
      this.logError({
        message,
        error: error.message,
        stack: error.stack,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href
      });
    }
    
    // Show user-friendly message
    const userMessage = this.getUserFriendlyErrorMessage(error);
    this.showNotification(userMessage, 'error');
  }
  
  /**
   * Auto-save functionality with conflict resolution
   */
  async autoSave() {
    if (this.pendingChanges.size === 0) return;
    
    const changedBlocks = Array.from(this.pendingChanges);
    this.pendingChanges.clear();
    
    for (const blockId of changedBlocks) {
      try {
        await this.saveBlock(blockId, { silent: true });
      } catch (error) {
        // Re-add to pending changes if save failed
        this.pendingChanges.add(blockId);
        console.warn(`Auto-save failed for block ${blockId}:`, error);
      }
    }
    
    if (this.pendingChanges.size === 0) {
      this.state.hasUnsavedChanges = false;
      this.updateSaveIndicator();
    }
  }
  
  /**
   * API call wrapper with timeout and retry logic
   */
  async apiCall(url, options = {}) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), options.timeout || this.config.apiTimeout);
    
    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
          ...options.headers
        }
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  }
  
  /**
   * Utility functions
   */
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }
  
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
  
  getStoredTheme() {
    return localStorage.getItem('theme') || 
           document.documentElement.dataset.bsTheme || 
           (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  }
  
  showNotification(message, type = 'info') {
    // Implementation depends on notification system
    console.log(`[${type.toUpperCase()}] ${message}`);
  }
  
  // Additional methods would be implemented here...
  // (toggleDarkMode, toggleFocusMode, saveBlock, etc.)
}

// Initialize Personal Space when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.personalSpace = new PersonalSpaceManager();
    window.personalSpace.init();
  });
} else {
  window.personalSpace = new PersonalSpaceManager();
  window.personalSpace.init();
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = PersonalSpaceManager;
}