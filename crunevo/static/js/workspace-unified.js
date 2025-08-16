/**
 * Unified Workspace API
 * Combines functionality from PersonalSpaceWorkspace and WorkspaceLayout
 * into a single, coherent API for managing workspace state and interactions
 */

window.WorkspaceManager = {
    // Core properties
    grid: null,
    isEditMode: false,
    currentView: 'grid',
    currentWorkspaceId: null,
    
    // Grid configuration
    gridSize: 20,
    snapToGrid: true,
    gridVisible: false,
    
    // Drag and drop state
    draggedBlock: null,
    
    // Auto-save
    autoSaveTimeout: null,
    
    /**
     * Initialize the workspace manager
     */
    init: function() {
        this.initializeGrid();
        this.bindEvents();
        this.loadWorkspaceData();
        this.setupDragAndDrop();
        this.setupAutoSave();
        this.initializeUI();
    },
    
    /**
     * Initialize GridStack with unified configuration
     */
    initializeGrid: function() {
        // Check if grid container exists
        const gridContainer = document.querySelector('.grid-stack');
        if (!gridContainer) {
            console.warn('GridStack container not found. Skipping grid initialization.');
            return;
        }
        
        // Initialize GridStack
        try {
            this.grid = GridStack.init({
                cellHeight: 80,
                verticalMargin: 10,
                horizontalMargin: 10,
                minRow: 6,
                animate: true,
                float: false,
                removable: false,
                acceptWidgets: true,
                dragIn: '.block-item',
                dragInOptions: {
                    revert: 'invalid',
                    scroll: false,
                    appendTo: 'body',
                    helper: 'clone'
                }
            });
            
            // Only add event listeners if grid was successfully initialized
            if (this.grid) {
                // Handle grid changes
                this.grid.on('change', (event, items) => {
                    this.onGridChange(items);
                });
                
                // Handle new items dropped
                this.grid.on('dropped', (event, previousWidget, newWidget) => {
                    this.onBlockDropped(newWidget);
                });
            }
        } catch (error) {
            console.error('Failed to initialize GridStack:', error);
            this.grid = null;
        }
    },
    
    /**
     * Initialize UI elements and state
     */
    initializeUI: function() {
        // Set initial grid visibility
        this.updateGridVisibility();
        
        // Initialize edit mode state
        this.updateEditModeUI();
        
        // Initialize view state
        this.updateViewUI();
    },
    
    /**
     * Bind all event listeners
     */
    bindEvents: function() {
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'b') {
                e.preventDefault();
                this.toggleBlockSidebar();
            }
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                this.saveWorkspace();
            }
        });
        
        // Block actions (edit/delete)
        document.addEventListener('click', (e) => {
            const actionBtn = e.target.closest('[data-action]');
            if (actionBtn) {
                const action = actionBtn.dataset.action;
                const blockId = actionBtn.dataset.blockId;
                
                if (action === 'edit') {
                    this.editBlock(blockId);
                } else if (action === 'delete') {
                    this.deleteBlock(blockId);
                }
            }
        });
        
        // UI controls
        this.bindUIControls();
    },
    
    /**
     * Bind UI control event listeners
     */
    bindUIControls: function() {
        // Sidebar toggle
        const sidebarToggle = document.getElementById('toggle-sidebar-btn');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => this.toggleBlockSidebar());
        }
        
        // View toggle buttons
        const gridViewBtn = document.getElementById('grid-view-btn');
        const listViewBtn = document.getElementById('list-view-btn');
        
        if (gridViewBtn) {
            gridViewBtn.addEventListener('click', () => this.switchView('grid'));
        }
        if (listViewBtn) {
            listViewBtn.addEventListener('click', () => this.switchView('list'));
        }
        
        // Edit mode toggle
        const editModeBtn = document.getElementById('edit-mode-btn');
        if (editModeBtn) {
            editModeBtn.addEventListener('click', () => this.toggleEditMode());
        }
        
        // Workspace actions
        const saveBtn = document.getElementById('save-workspace-btn');
        const resetBtn = document.getElementById('reset-workspace-btn');
        const exportBtn = document.getElementById('export-workspace-btn');
        
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveWorkspace());
        }
        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.resetWorkspace());
        }
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportWorkspace());
        }
        
        // Grid controls
        const gridSizeSlider = document.getElementById('grid-size-slider');
        const snapToggle = document.getElementById('snap-to-grid-toggle');
        const gridVisibilityToggle = document.getElementById('grid-visibility-toggle');
        
        if (gridSizeSlider) {
            gridSizeSlider.addEventListener('input', (e) => this.changeGridSize(parseInt(e.target.value)));
        }
        if (snapToggle) {
            snapToggle.addEventListener('change', () => this.toggleSnapToGrid());
        }
        if (gridVisibilityToggle) {
            gridVisibilityToggle.addEventListener('change', () => this.toggleGridVisibility());
        }
    },
    
    /**
     * Setup drag and drop functionality
     */
    setupDragAndDrop: function() {
        const blockItems = document.querySelectorAll('.block-item');
        
        blockItems.forEach(item => {
            item.addEventListener('dragstart', (e) => {
                const blockType = item.dataset.blockType;
                this.draggedBlock = { type: blockType, element: item };
                e.dataTransfer.setData('text/plain', blockType);
                e.dataTransfer.effectAllowed = 'copy';
            });
            
            item.addEventListener('dragend', () => {
                this.draggedBlock = null;
            });
        });
    },
    
    /**
     * Handle grid changes
     */
    onGridChange: function(items) {
        if (items && items.length > 0) {
            this.markAsModified();
            this.scheduleAutoSave();
        }
    },
    
    /**
     * Handle block dropped on workspace
     */
    onBlockDropped: function(newWidget) {
        const blockType = newWidget.el.dataset.blockType || 'task';
        
        // Create new block via API
        this.createBlock({
            type: blockType,
            x: newWidget.x,
            y: newWidget.y,
            width: newWidget.w || 4,
            height: newWidget.h || 3
        }).then(block => {
            if (block) {
                // Update the widget with real block data
                this.updateBlockWidget(newWidget.el, block);
            }
        });
    },
    
    /**
     * Create new block via API
     */
    createBlock: async function(blockData) {
        try {
            const response = await fetch('/api/personal-space/blocks', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(blockData)
            });
            
            if (response.ok) {
                const block = await response.json();
                this.showSuccessMessage('Bloque creado exitosamente');
                return block;
            } else {
                throw new Error('Error creating block');
            }
        } catch (error) {
            console.error('Error creating block:', error);
            this.showErrorMessage('Error al crear el bloque');
            return null;
        }
    },
    
    /**
     * Edit block - redirect to edit page
     */
    editBlock: function(blockId) {
        window.location.href = `/personal-space/block/${blockId}`;
    },
    
    /**
     * Delete block via API
     */
    deleteBlock: async function(blockId) {
        if (!confirm('¿Estás seguro de que quieres eliminar este bloque?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/personal-space/blocks/${blockId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            if (response.ok) {
                // Remove block from grid
                const blockElement = document.querySelector(`[data-block-id="${blockId}"]`);
                if (blockElement) {
                    const gridItem = blockElement.closest('.grid-stack-item');
                    if (gridItem && this.grid) {
                        this.grid.removeWidget(gridItem);
                    }
                }
                
                // Save workspace state
                this.saveWorkspace();
                
                // Show success message
                this.showSuccessMessage('Bloque eliminado correctamente');
                
                // Refresh blocks
                this.refreshBlocks();
            } else {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Error al eliminar el bloque');
            }
        } catch (error) {
            console.error('Error deleting block:', error);
            this.showErrorMessage('Error al eliminar el bloque: ' + error.message);
        }
    },
    
    /**
     * Refresh blocks from API
     */
    refreshBlocks: async function() {
        try {
            const response = await fetch('/api/personal-space/blocks');
            if (response.ok) {
                const data = await response.json();
                this.renderWorkspaceBlocks(data.blocks);
            }
        } catch (error) {
            console.error('Error refreshing blocks:', error);
        }
    },
    
    /**
     * Load workspace data from API
     */
    loadWorkspaceData: async function() {
        try {
            const response = await fetch('/api/personal-space/blocks');
            if (response.ok) {
                const data = await response.json();
                this.renderWorkspaceBlocks(data.blocks);
            }
        } catch (error) {
            console.error('Error loading workspace data:', error);
        }
    },
    
    /**
     * Render workspace blocks in grid
     */
    renderWorkspaceBlocks: function(blocks) {
        if (!blocks || blocks.length === 0) return;
        if (!this.grid) {
            console.warn('Grid not initialized. Cannot render blocks.');
            return;
        }
        
        // Clear existing grid
        this.grid.removeAll();
        
        // Add blocks to grid
        blocks.forEach(block => {
            const widget = {
                x: block.position_x || 0,
                y: block.position_y || 0,
                w: block.width || 4,
                h: block.height || 3,
                content: this.renderBlockContent(block),
                id: block.id
            };
            
            this.grid.addWidget(widget);
        });
    },
    
    /**
     * Update block widget with new data
     */
    updateBlockWidget: function(element, block) {
        element.dataset.blockId = block.id;
        element.innerHTML = this.renderBlockContent(block);
    },
    
    /**
     * Render block content HTML
     */
    renderBlockContent: function(block) {
        return `
            <div class="grid-stack-item-content">
                <div class="block-header">
                    <h4 class="block-title">
                        <i class="bi bi-${this.getBlockIcon(block.type)}"></i>
                        ${block.title || this.getBlockTypeName(block.type)}
                    </h4>
                    <div class="block-actions">
                        <button type="button" class="block-action-btn" data-action="edit" data-block-id="${block.id}" aria-label="Editar bloque">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button type="button" class="block-action-btn" data-action="delete" data-block-id="${block.id}" aria-label="Eliminar bloque">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
                <div class="block-body">
                    ${this.renderBlockBody(block)}
                </div>
            </div>
        `;
    },
    
    /**
     * Get icon for block type
     */
    getBlockIcon: function(type) {
        const icons = {
            task: 'check-square',
            note: 'journal-text',
            kanban: 'kanban',
            objective: 'target',
            calendar: 'calendar3',
            habit: 'arrow-repeat'
        };
        return icons[type] || 'square';
    },
    
    /**
     * Get display name for block type
     */
    getBlockTypeName: function(type) {
        const names = {
            task: 'Tareas',
            note: 'Notas',
            kanban: 'Kanban',
            objective: 'Objetivos',
            calendar: 'Calendario',
            habit: 'Hábitos'
        };
        return names[type] || 'Bloque';
    },
    
    /**
     * Render block body content
     */
    renderBlockBody: function(block) {
        return `
            <div class="text-center py-4">
                <i class="bi bi-${this.getBlockIcon(block.type)} text-muted" style="font-size: 2rem;"></i>
                <p class="text-muted mt-2 mb-0">Contenido del bloque</p>
                <small class="text-muted">Haz clic para configurar</small>
            </div>
        `;
    },
    
    /**
     * Toggle edit mode
     */
    toggleEditMode: function() {
        this.isEditMode = !this.isEditMode;
        this.updateEditModeUI();
        
        if (this.grid) {
            if (this.isEditMode) {
                this.grid.enable();
            } else {
                this.grid.disable();
                this.saveWorkspace();
            }
        }
    },
    
    /**
     * Update edit mode UI
     */
    updateEditModeUI: function() {
        const container = document.getElementById('workspace-container');
        const btn = document.getElementById('edit-mode-btn');
        
        if (container) {
            container.classList.toggle('edit-mode', this.isEditMode);
        }
        
        if (btn) {
            if (this.isEditMode) {
                btn.innerHTML = '<i class="bi bi-check me-1"></i>Finalizar';
                btn.classList.remove('secondary');
            } else {
                btn.innerHTML = '<i class="bi bi-pencil me-1"></i>Editar';
                btn.classList.add('secondary');
            }
        }
    },
    
    /**
     * Switch between grid and list views
     */
    switchView: function(view) {
        if (this.currentView === view) return;
        
        this.currentView = view;
        this.updateViewUI();
        
        if (view === 'list') {
            this.switchToListView();
        } else {
            this.switchToGridView();
        }
    },
    
    /**
     * Update view toggle UI
     */
    updateViewUI: function() {
        document.querySelectorAll('.view-toggle-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.view === this.currentView);
        });
    },
    
    /**
     * Switch to grid view
     */
    switchToGridView: function() {
        const container = document.querySelector('.grid-container');
        if (container) {
            container.style.display = 'block';
        }
        if (this.grid) {
            this.grid.enable();
        }
    },
    
    /**
     * Switch to list view
     */
    switchToListView: function() {
        console.log('Switching to list view');
        // TODO: Implement list view functionality
    },
    
    /**
     * Toggle block sidebar
     */
    toggleBlockSidebar: function() {
        const sidebar = document.getElementById('workspace-sidebar');
        if (sidebar) {
            sidebar.classList.toggle('collapsed');
        }
    },
    
    /**
     * Change grid size
     */
    changeGridSize: function(size) {
        this.gridSize = size;
        this.updateGridDisplay();
    },
    
    /**
     * Toggle snap to grid
     */
    toggleSnapToGrid: function() {
        this.snapToGrid = !this.snapToGrid;
        // Update grid behavior based on snap setting
        if (this.grid) {
            // GridStack doesn't have a direct snap toggle, but we can adjust cellHeight
            // This is a simplified implementation
            console.log('Snap to grid:', this.snapToGrid);
        }
    },
    
    /**
     * Toggle grid visibility
     */
    toggleGridVisibility: function() {
        this.gridVisible = !this.gridVisible;
        this.updateGridVisibility();
    },
    
    /**
     * Update grid visibility
     */
    updateGridVisibility: function() {
        const container = document.getElementById('workspace-container');
        if (container) {
            container.classList.toggle('show-grid', this.gridVisible);
        }
    },
    
    /**
     * Update grid display
     */
    updateGridDisplay: function() {
        // Update CSS custom properties for grid size
        document.documentElement.style.setProperty('--grid-size', `${this.gridSize}px`);
    },
    
    /**
     * Save workspace state
     */
    saveWorkspace: async function() {
        const blocks = this.getWorkspaceState();
        
        this.setSaveStatus('saving');
        
        try {
            const response = await fetch('/api/personal-space/blocks/reorder', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ blocks })
            });
            
            if (response.ok) {
                this.setSaveStatus('saved');
                this.updateLastModified();
                this.showSuccessMessage('Workspace guardado');
            } else {
                throw new Error('Save failed');
            }
        } catch (error) {
            console.error('Error saving workspace:', error);
            this.setSaveStatus('error');
            this.showErrorMessage('Error al guardar');
        }
    },
    
    /**
     * Get current workspace state
     */
    getWorkspaceState: function() {
        if (!this.grid) {
            console.warn('Grid not initialized. Cannot get workspace state.');
            return [];
        }
        
        const items = this.grid.getGridItems();
        return items.map(item => {
            const node = item.gridstackNode;
            return {
                id: node.id,
                x: node.x,
                y: node.y,
                width: node.w,
                height: node.h
            };
        });
    },
    
    /**
     * Setup auto-save functionality
     */
    setupAutoSave: function() {
        this.autoSaveTimeout = null;
    },
    
    /**
     * Schedule auto-save
     */
    scheduleAutoSave: function() {
        clearTimeout(this.autoSaveTimeout);
        this.autoSaveTimeout = setTimeout(() => {
            this.saveWorkspace();
        }, 3000); // Auto-save after 3 seconds of inactivity
    },
    
    /**
     * Mark workspace as modified
     */
    markAsModified: function() {
        this.setSaveStatus('modified');
    },
    
    /**
     * Set save status indicator
     */
    setSaveStatus: function(status) {
        const indicator = document.getElementById('save-status');
        const text = document.getElementById('save-status-text');
        
        if (indicator) {
            indicator.className = `status-indicator ${status}`;
        }
        
        const statusTexts = {
            saved: 'Guardado',
            saving: 'Guardando...',
            modified: 'Modificado',
            error: 'Error'
        };
        
        if (text) {
            text.textContent = statusTexts[status] || 'Desconocido';
        }
    },
    
    /**
     * Update last modified timestamp
     */
    updateLastModified: function() {
        const element = document.getElementById('last-modified');
        if (element) {
            element.textContent = 'hace un momento';
        }
    },
    
    /**
     * Reset workspace
     */
    resetWorkspace: function() {
        if (confirm('¿Estás seguro de que quieres resetear el workspace? Esta acción no se puede deshacer.')) {
            if (this.grid) {
                this.grid.removeAll();
            }
            this.saveWorkspace();
        }
    },
    
    /**
     * Export workspace configuration
     */
    exportWorkspace: function() {
        const state = this.getWorkspaceState();
        const dataStr = JSON.stringify(state, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        
        const link = document.createElement('a');
        link.href = URL.createObjectURL(dataBlob);
        link.download = `workspace-${new Date().toISOString().split('T')[0]}.json`;
        link.click();
    },
    
    /**
     * Get CSRF token for API requests
     */
    getCSRFToken: function() {
        return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    },
    
    /**
     * Show success message
     */
    showSuccessMessage: function(message) {
        console.log('Success:', message);
        // TODO: Implement proper toast/notification system
    },
    
    /**
     * Show error message
     */
    showErrorMessage: function(message) {
        console.error('Error:', message);
        // TODO: Implement proper toast/notification system
    }
};

// Expose global functions for backward compatibility
window.refreshBlocks = function() {
    window.WorkspaceManager.refreshBlocks();
};

window.editBlock = function(blockId) {
    window.WorkspaceManager.editBlock(blockId);
};

window.deleteBlock = function(blockId) {
    window.WorkspaceManager.deleteBlock(blockId);
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Personal Space core functionality
    if (window.initPersonalSpace) {
        window.initPersonalSpace();
    }
    
    // Initialize Unified Workspace Manager
    window.WorkspaceManager.init();
});