// Personal Space JavaScript - Optimized Version
function initPersonalSpace() {
    console.log('Initializing Personal Space...');
    initializePersonalSpace();
    updateDashboardMetrics();
    initializeKanbanBoards();
    setupAutoSave();
    setupErrorHandling();
    setupModalBackdropCleanup();
}

let sortableInstance = null;
let currentEditingBlock = null;
let isDarkMode = (localStorage.getItem('theme') || document.documentElement.dataset.bsTheme) === 'dark';
let isFocusMode = localStorage.getItem('focus_mode') === 'on';
let isInitialized = false;

const DEFAULT_ICONS = {
    'nota': 'bi-journal-text',
    'nota_enriquecida': 'bi-file-richtext',
    'bitacora': 'bi-journal-text',
    'lista': 'bi-check2-square',
    'meta': 'bi-target',
    'recordatorio': 'bi-alarm',
    'frase': 'bi-quote',
    'enlace': 'bi-link-45deg',
    'tarea': 'bi-clipboard-check',
    'kanban': 'bi-kanban',
    'objetivo': 'bi-trophy',
    'bloque': 'bi-grid-3x3'
};

function initializePersonalSpace() {
    if (isInitialized) {
        console.log('Personal Space already initialized');
        return;
    }
    
    try {
        console.log('Starting Personal Space initialization...');
        
        // Initialize UI components
        initializeDarkMode();
        initializeFocusMode();
        initializeSortable();
        initializeEventListeners();
        initializeAutoSave();
        
        // Initialize BlockFactory if available
        if (typeof window.BlockFactory !== 'undefined' && window.BlockFactory.init) {
            window.BlockFactory.init();
            console.log('BlockFactory initialized');
        }

        // Ensure modals are not constrained by parent containers
        const editModal = document.getElementById('editBlockModal');
        if (editModal && editModal.parentNode !== document.body) {
            document.body.appendChild(editModal);
        }

        // Restore dismissed suggestions
        hideDismissedSuggestions();

        // Load initial data
        loadBlocks();

        // Set up periodic auto-save
        setInterval(autoSaveChanges, 30000); // Auto-save every 30 seconds
        
        isInitialized = true;
        console.log('Personal Space initialized successfully');
    } catch (error) {
        console.error('Error initializing Personal Space:', error);
        showNotification('Error al inicializar el espacio personal', 'error');
    }
}

function initializeDarkMode() {
    const html = document.documentElement;
    const body = document.body;
    
    // Prevent transitions during initialization
    body.classList.add('preload');
    
    // Apply theme classes
    if (isDarkMode) {
        html.classList.add('dark-mode');
        body.classList.add('dark-theme');
        body.classList.remove('light-theme');
    } else {
        html.classList.remove('dark-mode');
        body.classList.add('light-theme');
        body.classList.remove('dark-theme');
    }
    
    html.dataset.bsTheme = isDarkMode ? 'dark' : 'light';
    updateDarkModeButton();
    updateThemeColor();
    
    // Re-enable transitions after initialization
    setTimeout(() => {
        body.classList.remove('preload');
    }, 100);
    
    // Listen for system theme changes if no manual preference is set
    const savedTheme = localStorage.getItem('theme');
    if (!savedTheme) {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        mediaQuery.addEventListener('change', (e) => {
            isDarkMode = e.matches;
            initializeDarkMode();
        });
    }
}

function initializeFocusMode() {
    if (isFocusMode) {
        applyFocusMode(true);
    }
}

function initializeSortable() {
    const grid = document.getElementById('blocksGrid');
    if (!grid) return;

    sortableInstance = Sortable.create(grid, {
        animation: 150,
        ghostClass: 'sortable-ghost',
        chosenClass: 'sortable-chosen',
        dragClass: 'sortable-drag',
        onEnd: function(evt) {
            updateBlockOrder();
        }
    });
}

function initializeEventListeners() {
    try {
        console.log('Initializing event listeners...');
        
        // Add block buttons with improved error handling - Using specific IDs and selectors
        const addBlockSelectors = ['#addBlockBtn', '#new-block-btn', '#create-first-block-btn', '[data-bs-target="#block-factory-modal"]:not(.dropdown-toggle)'];
        addBlockSelectors.forEach(selector => {
            const buttons = document.querySelectorAll(selector);
            buttons.forEach(btn => {
                if (btn && !btn.dataset.listenerAdded) {
                    btn.addEventListener('click', (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        console.log('Add block button clicked');
                        showAddBlockModal();
                    });
                    btn.dataset.listenerAdded = 'true';
                }
            });
        });
        
        // Create first block button
        const createFirstBlock = document.getElementById('createFirstBlock');
        if (createFirstBlock && !createFirstBlock.dataset.listenerAdded) {
            createFirstBlock.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('Create first block clicked');
                startPersonalSpace();
            });
            createFirstBlock.dataset.listenerAdded = 'true';
        }

        // Control buttons with error handling
        const darkModeToggle = document.getElementById('darkModeToggle');
        const focusModeBtn = document.getElementById('focusModeBtn');
        const exitFocusBtn = document.getElementById('exitFocusBtn');
        
        if (darkModeToggle) {
            darkModeToggle.addEventListener('click', (e) => {
                e.preventDefault();
                toggleDarkMode();
            });
        }
        
        if (focusModeBtn) {
            focusModeBtn.addEventListener('click', (e) => {
                e.preventDefault();
                toggleFocusMode();
            });
        }
        
        if (exitFocusBtn) {
            exitFocusBtn.addEventListener('click', (e) => {
                e.preventDefault();
                if (isFocusMode) toggleFocusMode();
            });
        }

        // Modal events
        document.addEventListener('click', handleModalEvents);
        const saveBlockBtn = document.getElementById('saveBlockBtn');
        if (saveBlockBtn) {
            saveBlockBtn.addEventListener('click', (e) => {
                e.preventDefault();
                saveCurrentBlock();
            });
        }

        // Suggestion events
        document.querySelectorAll('.apply-suggestion-btn').forEach(btn => {
            btn.addEventListener('click', handleSuggestionClick);
        });

        // Centralized block interaction delegation with improved handling
        const grid = document.getElementById('blocksGrid');
        if (grid && !grid.dataset.bound) {
            grid.addEventListener('click', handleBlockInteractions);
            grid.addEventListener('dblclick', handleBlockInteractions);
            grid.dataset.bound = '1';
        }

        // Auto-save on content change
        document.addEventListener('input', debounce(handleContentChange, 500));
        
        console.log('Event listeners initialized successfully');
    } catch (error) {
        console.error('Error initializing event listeners:', error);
    }
}

function initializeAutoSave() {
    // Save draft content periodically
    setInterval(() => {
        const editingElements = document.querySelectorAll('[contenteditable="true"], .auto-save-input');
        editingElements.forEach(element => {
            if (element.dataset.blockId && element.dataset.hasChanges === 'true') {
                autoSaveBlock(element.dataset.blockId);
            }
        });
    }, 10000);
}

// Block Management Functions
function loadBlocks() {
    console.log('Loading blocks...');
    
    // Show loading state
    const grid = document.getElementById('blocksGrid');
    if (grid) {
        grid.innerHTML = '<div class="text-center p-4"><div class="spinner-border" role="status"><span class="visually-hidden">Cargando...</span></div></div>';
    }
    
    csrfFetch('/api/personal-space/blocks')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Blocks loaded:', data);
            if (data.success) {
                renderBlocks(data.blocks || []);
            } else {
                throw new Error(data.error || 'Error desconocido al cargar bloques');
            }
        })
        .catch(error => {
            console.error('Error loading blocks:', error);
            showNotification('Error al cargar los bloques: ' + error.message, 'error');
            
            // Show error state
            if (grid) {
                grid.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">
                            <i class="bi bi-exclamation-triangle"></i>
                        </div>
                        <h3>Error al cargar bloques</h3>
                        <p>No se pudieron cargar los bloques. Intenta recargar la página.</p>
                        <button class="modern-btn modern-btn-primary" onclick="loadBlocks()">Reintentar</button>
                    </div>
                `;
            }
        });
}

function renderBlocks(blocks) {
    console.log('Rendering blocks:', blocks.length);
    const grid = document.getElementById('blocksGrid');
    if (!grid) {
        console.error('Blocks grid not found');
        return;
    }

    // Clear existing content
    grid.innerHTML = '';

    if (!blocks || blocks.length === 0) {
        renderEmptyState(grid);
        return;
    }

    try {
        blocks.forEach((b, index) => {
            try {
                const block = convertBlock(b);
                const blockElement = createBlockElement(block);
                if (blockElement) {
                    blockElement.classList.add('fade-in');
                    grid.appendChild(blockElement);
                }
            } catch (error) {
                console.error(`Error rendering block ${index}:`, error, b);
            }
        });

        // Setup accessibility
        setupBlockAccessibility();
        
        updateDashboardMetrics();
        initializeKanbanBoards();
        
        console.log('Blocks rendered successfully');
    } catch (error) {
        console.error('Error in renderBlocks:', error);
        showNotification('Error al mostrar los bloques', 'error');
    }
}

function convertBlock(block) {
    if (!block) {
        console.error('Block is null or undefined');
        return null;
    }
    
    // Ensure metadata exists
    if (!block.metadata) {
        block.metadata = {};
    }
    
    // Set default values
    block.color = block.metadata.color || 'indigo';
    block.icon = block.metadata.icon || DEFAULT_ICONS[block.type] || 'bi-card-text';
    block.progress = computeProgress(block);
    
    // Ensure required fields
    block.title = block.title || 'Sin título';
    block.content = block.content || '';
    block.type = block.type || 'nota';
    
    return block;
}

function computeProgress(block) {
    const meta = block.metadata || {};
    switch (block.type) {
        case 'lista':
            const tasks = meta.tasks || [];
            if (!tasks.length) return 0;
            const done = tasks.filter(t => t.completed).length;
            return Math.round((done / tasks.length) * 100);
        case 'objetivo':
        case 'meta':
            return meta.progress || 0;
        case 'kanban':
            const cols = meta.columns || {};
            let total = 0, completed = 0;
            Object.entries(cols).forEach(([name, tasks]) => {
                total += tasks.length;
                if (['hecho','completado','finalizado'].includes(name.toLowerCase())) {
                    completed += tasks.length;
                }
            });
            return total ? Math.round((completed/total)*100) : 0;
        default:
            return 0;
    }
}

function createBlockElement(block) {
    const blockElement = document.createElement('div');
    blockElement.className = `block-card ${block.color}-block ${block.is_featured ? 'featured' : ''}`;
    blockElement.dataset.blockId = block.id;
    blockElement.dataset.blockType = block.type;

    blockElement.setAttribute('role', 'button');
    blockElement.tabIndex = 0;
    blockElement.setAttribute('aria-label', block.title || 'Bloque');

    blockElement.innerHTML = generateBlockHTML(block);

    return blockElement;
}

function generateBlockHTML(block) {
    const typeLabels = {
        'nota': 'Nota Rápida',
        'nota_enriquecida': 'Bitácora Inteligente',
        'lista': 'Lista de Tareas',
        'meta': 'Meta',
        'recordatorio': 'Recordatorio',
        'frase': 'Frase Motivacional',
        'enlace': 'Enlace Educativo'
    };

    return `
        <div class="block-header">
            <div class="block-icon">
                <i class="${block.icon}"></i>
            </div>
            <div class="block-meta">
                <h6 class="block-title line-clamp-2">${block.title || 'Sin título'}</h6>
                <small class="block-type-label">${typeLabels[block.type] || 'Bloque'}</small>
            </div>
            <div class="block-actions">
                ${block.is_featured ? '<i class="bi bi-star-fill featured-star" title="Destacado"></i>' : ''}
                <div class="dropdown">
                    <button class="btn btn-sm btn-ghost" data-bs-toggle="dropdown">
                        <i class="bi bi-three-dots-vertical"></i>
                    </button>
                    <ul class="dropdown-menu">
                        <li><a class="dropdown-item edit-block" href="#"><i class="bi bi-pencil"></i> Editar</a></li>
                        <li><a class="dropdown-item toggle-featured" href="#"><i class="bi bi-star"></i> ${block.is_featured ? 'Quitar destacado' : 'Destacar'}</a></li>
                        <li><hr class="dropdown-divider"></li>
                        <li><a class="dropdown-item text-danger delete-block" href="#"><i class="bi bi-trash"></i> Eliminar</a></li>
                    </ul>
                </div>
            </div>
        </div>
        <div class="block-content">
            ${generateBlockContent(block)}
        </div>
        <div class="block-footer">
            <small class="text-muted">
                Actualizado ${formatDate(block.updated_at)}
            </small>
            <div class="d-flex align-items-center">
                ${block.progress > 0 ? `<span class="progress-badge me-2">${block.progress}%</span>` : ''}
                <a class="btn btn-link btn-sm btn-enter" href="/personal-space/bloque/${block.id}" data-id="${block.id}" aria-label="Entrar al bloque">Entrar</a>
                </div>
        </div>
    `;
}

function generateBlockContent(block) {
    switch (block.type) {
        case 'nota':
        case 'nota_enriquecida':
        case 'nota_enriquecida':
        case 'nota_enriquecida':
            return `
                <div class="note-content">
                    ${block.content ?
                        `<p class="line-clamp-2">${block.content.substring(0, 200)}${block.content.length > 200 ? '...' : ''}</p>` :
                        '<p class="text-muted">Haz clic para escribir...</p>'
                    }
                </div>
            `;

        case 'lista':
            const tasks = block.metadata.tasks || [];
            return `
                <div class="task-list-content">
                    ${tasks.length > 0 ? `
                        <div class="progress-indicator mb-2">
                            <div class="progress">
                                <div class="progress-bar" style="width: ${block.progress}%"></div>
                            </div>
                            <small>${block.progress}% completado</small>
                        </div>
                        <div class="task-preview">
                            ${tasks.slice(0, 3).map(task => `
                                <div class="task-item">
                                    <i class="bi ${task.completed ? 'bi-check-square' : 'bi-square'}"></i>
                                    <span class="${task.completed ? 'completed' : ''}">${task.text}</span>
                                </div>
                            `).join('')}
                            ${tasks.length > 3 ? `<small class="text-muted">y ${tasks.length - 3} más...</small>` : ''}
                        </div>
                    ` : '<p class="text-muted">No hay tareas aún</p>'}
                </div>
            `;

        case 'meta':
            return `
                <div class="goal-content">
                    <div class="goal-progress mb-2">
                        <div class="progress">
                            <div class="progress-bar bg-success" style="width: ${block.metadata.progress || 0}%"></div>
                        </div>
                        <small>${block.metadata.progress || 0}% completado</small>
                    </div>
                    ${block.metadata.target_date ? `
                        <div class="goal-date">
                            <i class="bi bi-calendar"></i>
                            <small>Meta: ${formatDate(block.metadata.target_date)}</small>
                        </div>
                    ` : ''}
                    ${block.content ? `<p class="goal-description line-clamp-2">${block.content.substring(0, 100)}${block.content.length > 100 ? '...' : ''}</p>` : ''}
                </div>
            `;

        case 'recordatorio':
            return `
                <div class="reminder-content">
                    ${block.is_overdue ? `
                        <div class="alert alert-danger alert-sm">
                            <i class="bi bi-exclamation-triangle"></i> ¡Vencido!
                        </div>
                    ` : ''}
                    ${block.metadata.due_date ? `
                        <div class="reminder-date">
                            <i class="bi bi-calendar-event"></i>
                            <small>${formatDate(block.metadata.due_date)}</small>
                        </div>
                    ` : ''}
                    ${block.content ? `<p class="line-clamp-2">${block.content.substring(0, 150)}${block.content.length > 150 ? '...' : ''}</p>` : ''}
                </div>
            `;

        case 'frase':
            return `
                <div class="quote-content text-center">
                    ${block.content ? `
                        <blockquote class="blockquote">
                            <p class="line-clamp-2">"${block.content}"</p>
                        </blockquote>
                        ${block.metadata.author ? `
                            <footer class="blockquote-footer">${block.metadata.author}</footer>
                        ` : ''}
                    ` : '<p class="text-muted">Añade una frase inspiradora</p>'}
                </div>
            `;

        case 'enlace':
            return `
                <div class="link-content">
                    ${block.metadata.url ? `
                        <div class="link-preview">
                            <div class="link-icon">
                                <i class="bi bi-link-45deg"></i>
                            </div>
                            <div class="link-info">
                                <h6>${block.title || 'Enlace'}</h6>
                                ${block.metadata.description ? `
                                    <p class="text-muted line-clamp-2">${block.metadata.description.substring(0, 100)}</p>
                                ` : ''}
                                <small class="text-primary">${block.metadata.url.substring(0, 50)}...</small>
                            </div>
                        </div>
                    ` : '<p class="text-muted">Añade un enlace educativo</p>'}
                </div>
            `;

        default:
            return '<p class="text-muted">Contenido no disponible</p>';
    }
}

// Modal Functions
function showAddBlockModal() {
    // Try multiple modal IDs for compatibility
    const modalIds = ['block-factory-modal', 'addBlockModal', 'blockFactoryModal'];
    let modal = null;
    
    for (const id of modalIds) {
        modal = document.getElementById(id);
        if (modal) break;
    }
    
    if (modal) {
        try {
            // Remove any existing backdrops first
            const existingBackdrops = document.querySelectorAll('.modal-backdrop');
            existingBackdrops.forEach(backdrop => backdrop.remove());
            
            // Close any other open modals
            const openModals = document.querySelectorAll('.modal.show');
            openModals.forEach(openModal => {
                const instance = bootstrap.Modal.getInstance(openModal);
                if (instance) instance.hide();
            });
            
            // Wait a bit for cleanup, then show the modal
            setTimeout(() => {
                const bsModal = new bootstrap.Modal(modal, {
                    backdrop: true,
                    keyboard: true,
                    focus: true
                });
                bsModal.show();
            }, 100);
        } catch (error) {
            console.error('Error showing modal:', error);
            showNotification('Error al abrir el modal de creación', 'error');
        }
    } else {
        console.error('Block factory modal not found. Available modals:', 
            Array.from(document.querySelectorAll('[id*="modal"]')).map(m => m.id));
        showNotification('Modal de creación no encontrado', 'error');
    }
}

function handleModalEvents(e) {
    try {
        // Handle block type selection
        const blockTypeCard = e.target.closest('.block-type-card');
        if (blockTypeCard && blockTypeCard.dataset.type) {
            e.preventDefault();
            e.stopPropagation();
            const blockType = blockTypeCard.dataset.type;
            console.log('Creating new block of type:', blockType);
            createNewBlock(blockType);
            return;
        }
        
        // Only handle quick action buttons that specifically target block-factory-modal
        const quickActionBtn = e.target.closest('[data-bs-toggle="modal"]');
        if (quickActionBtn) {
            const targetModal = quickActionBtn.getAttribute('data-bs-target');
            // Only intercept if it's specifically targeting the block factory modal
            if (targetModal === '#block-factory-modal') {
                e.preventDefault();
                e.stopPropagation();
                const modal = document.querySelector(targetModal);
                if (modal) {
                    const bsModal = new bootstrap.Modal(modal);
                    bsModal.show();
                }
            }
            // Let other modals (like template gallery) handle themselves normally
        }
    } catch (error) {
        console.error('Error in handleModalEvents:', error);
    }
}

function apiCreateBlock(blockData) {
    return csrfFetch('/api/personal-space/blocks', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(blockData)
    }).then(response => response.json());
}

function createNewBlock(type) {
    if (!type) {
        console.error('Block type is required');
        showNotification('Tipo de bloque requerido', 'error');
        return;
    }
    
    const blockData = {
        type: type,
        title: getDefaultTitle(type),
        content: '',
        metadata: Object.assign({
            color: 'indigo',
            icon: DEFAULT_ICONS[type] || 'bi-card-text'
        }, getDefaultMetadata(type))
    };

    console.log('Creating block with data:', blockData);
    
    apiCreateBlock(blockData)
        .then(data => {
            console.log('Block creation response:', data);
            if (data.success && data.block) {
                // Close any open modals
                const openModals = document.querySelectorAll('.modal.show');
                openModals.forEach(modal => {
                    const bsModal = bootstrap.Modal.getInstance(modal);
                    if (bsModal) bsModal.hide();
                });

                const blockElement = createBlockElement(data.block);
                if (blockElement) {
                    blockElement.classList.add('new-block');

                    const grid = document.getElementById('blocksGrid');
                    if (grid) {
                        const emptyState = grid.querySelector('.empty-state');
                        if (emptyState) {
                            emptyState.remove();
                        }
                        grid.appendChild(blockElement);
                    }

                    // Auto-open edit modal after a short delay
                    setTimeout(() => {
                        showEditBlockModal(data.block.id);
                    }, 300);

                    showNotification('Bloque creado exitosamente', 'success');
                } else {
                    console.error('Failed to create block element');
                    showNotification('Error al mostrar el bloque creado', 'error');
                }
            } else {
                console.error('Block creation failed:', data);
                showNotification(data.message || 'Error al crear el bloque', 'error');
            }
        })
        .catch(error => {
            console.error('Error creating block:', error);
            showNotification('Error de conexión al crear el bloque', 'error');
        });
}

function getDefaultTitle(type) {
    const titles = {
        'nota': 'Nueva nota',
        'nota_enriquecida': 'Nueva nota',
        'lista': 'Lista de tareas',
        'meta': 'Nueva meta',
        'recordatorio': 'Recordatorio',
        'frase': 'Frase motivacional',
        'enlace': 'Enlace útil'
    };
    return titles[type] || 'Nuevo bloque';
}

function getDefaultMetadata(type) {
    switch (type) {
        case 'lista':
            return { tasks: [] };
        case 'meta':
            return { progress: 0, target_date: '' };
        case 'recordatorio':
            return { due_date: '', priority: 'medium' };
        case 'frase':
            return { author: '', category: 'motivacional' };
        case 'enlace':
            return { url: '', description: '' };
        case 'nota_enriquecida':
            return { blocks: [], template_type: '', tags: [] };
        case 'bitacora':
            return { entries: [], streak: 0, mood_tracking: true };
        default:
            return {};
    }
}

function startPersonalSpace() {
    const requests = ['nota_enriquecida', 'kanban', 'objetivo'].map(type =>
        csrfFetch('/api/personal-space/blocks', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                type,
                title: getDefaultTitle(type),
                content: '',
                metadata: Object.assign({
                    color: 'indigo',
                    icon: DEFAULT_ICONS[type]
                }, getDefaultMetadata(type))
            })
        })
    );
    Promise.all(requests).then(() => {
        showNotification('Espacio inicial creado', 'success');
        setTimeout(() => window.location.reload(), 500);
    });
}

// Block Editing Functions
const debouncedShowEdit = debounce((id) => showEditBlockModal(id), 200);

function handleBlockInteractions(e) {
    const blockCard = e.target.closest('.block-card');
    if (!blockCard) return;

    const blockId = blockCard.dataset.blockId;

    if (e.target.closest('.edit-block')) {
        e.preventDefault();
        debouncedShowEdit.cancel?.();
        showEditBlockModal(blockId);
        return;
    }
    if (e.target.closest('.delete-block')) {
        e.preventDefault();
        deleteBlock(blockId);
        return;
    }
    if (e.target.closest('.toggle-featured')) {
        e.preventDefault();
        toggleBlockFeatured(blockId);
        return;
    }
    if (e.target.closest('.dropdown, .btn-enter')) {
        return;
    }

    if (e.type === 'dblclick') {
        debouncedShowEdit.cancel?.();
        openBlock(blockId);
    } else {
        debouncedShowEdit(blockId);
    }
}

function showEditBlockModal(blockId) {
    const blockCard = document.querySelector(`[data-block-id="${blockId}"]`);
    if (!blockCard) return;

    const blockType = blockCard.dataset.blockType;
    currentEditingBlock = blockId;

    // Clean any orphaned backdrops before showing modal
    document.querySelectorAll('.modal-backdrop').forEach(b => b.remove());

    // Prefer fetching only this block if endpoint exists
    csrfFetch(`/api/personal-space/blocks/${blockId}`)
        .then(response => {
            if (!response.ok) throw new Error('single-endpoint-missing');
            return response.json();
        })
        .then(data => {
            const block = data.block || data;
            renderEditForm(block);
            const modalEl = document.getElementById('editBlockModal');
            const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
            modal.show();
        })
        .catch(() => {
            // Fallback to full list fetch
            csrfFetch(`/api/personal-space/blocks`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const block = data.blocks.find(b => b.id == blockId);
                        if (block) {
                            renderEditForm(block);
                            const modalEl = document.getElementById('editBlockModal');
                            const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
                            modal.show();
                        } else {
                            showNotification('Bloque no encontrado', 'error');
                        }
                    } else {
                        showNotification('Error al cargar los bloques', 'error');
                    }
                })
                .catch(error => {
                    console.error('Error loading block data:', error);
                    showNotification('Error al cargar los datos del bloque', 'error');
                });
        });
}

function renderEditForm(block) {
    const content = document.getElementById('editBlockContent');
    if (!content) {
        console.warn('[PS] editBlockContent no existe, reintentando...');
        setTimeout(() => renderEditForm(block), 50);
        return;
    }
    const form = generateEditForm(block);
    content.innerHTML = form;

    // Initialize form interactions
    initializeEditFormInteractions(block);
}

function generateEditForm(block) {
    const baseForm = `
        <div class="row mb-3">
            <div class="col-md-8">
                <label for="blockTitle" class="form-label">Título</label>
                <input type="text" class="form-control" id="blockTitle" value="${block.title || ''}" maxlength="200">
            </div>
            <div class="col-md-4">
                <label for="blockColor" class="form-label">Color</label>
                <select class="form-select" id="blockColor">
                    <option value="indigo" ${block.color === 'indigo' ? 'selected' : ''}>Índigo</option>
                    <option value="purple" ${block.color === 'purple' ? 'selected' : ''}>Púrpura</option>
                    <option value="emerald" ${block.color === 'emerald' ? 'selected' : ''}>Esmeralda</option>
                    <option value="amber" ${block.color === 'amber' ? 'selected' : ''}>Ámbar</option>
                    <option value="rose" ${block.color === 'rose' ? 'selected' : ''}>Rosa</option>
                    <option value="blue" ${block.color === 'blue' ? 'selected' : ''}>Azul</option>
                </select>
            </div>
        </div>
    `;

    let specificForm = '';

    switch (block.type) {
        case 'nota':
            specificForm = `
                <div class="mb-3">
                    <label for="noteContent" class="form-label">Contenido</label>
                    <textarea class="form-control" id="noteContent" rows="8" placeholder="Escribe tu nota aquí...">${block.content || ''}</textarea>
                </div>
            `;
            break;

        case 'lista':
            const tasks = block.metadata.tasks || [];
            specificForm = `
                <div class="mb-3">
                    <label class="form-label">Tareas</label>
                    <div id="tasksList">
                        ${tasks.map((task, index) => `
                            <div class="task-item-edit mb-2" data-task-index="${index}">
                                <div class="input-group">
                                    <div class="input-group-text">
                                        <input type="checkbox" ${task.completed ? 'checked' : ''} class="task-checkbox">
                                    </div>
                                    <input type="text" class="form-control task-text" value="${task.text || ''}" placeholder="Descripción de la tarea">
                                    <button class="btn btn-outline-danger btn-sm remove-task" type="button">
                                        <i class="bi bi-trash"></i>
                                    </button>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                    <button type="button" class="btn btn-outline-primary btn-sm" id="addTaskBtn">
                        <i class="bi bi-plus"></i> Añadir tarea
                    </button>
                </div>
            `;
            break;

        case 'meta':
            specificForm = `
                <div class="mb-3">
                    <label for="goalContent" class="form-label">Descripción de la meta</label>
                    <textarea class="form-control" id="goalContent" rows="4" placeholder="Describe tu meta...">${block.content || ''}</textarea>
                </div>
                <div class="row">
                    <div class="col-md-6">
                        <label for="goalProgress" class="form-label">Progreso (%)</label>
                        <input type="range" class="form-range" id="goalProgress" min="0" max="100" value="${block.metadata.progress || 0}">
                        <div class="text-center"><span id="progressValue">${block.metadata.progress || 0}</span>%</div>
                    </div>
                    <div class="col-md-6">
                        <label for="targetDate" class="form-label">Fecha objetivo</label>
                        <input type="date" class="form-control" id="targetDate" value="${block.metadata.target_date || ''}">
                    </div>
                </div>
            `;
            break;

        case 'recordatorio':
            specificForm = `
                <div class="mb-3">
                    <label for="reminderContent" class="form-label">Descripción</label>
                    <textarea class="form-control" id="reminderContent" rows="4" placeholder="¿Qué necesitas recordar?">${block.content || ''}</textarea>
                </div>
                <div class="row">
                    <div class="col-md-6">
                        <label for="dueDate" class="form-label">Fecha y hora límite</label>
                        <input type="datetime-local" class="form-control" id="dueDate" value="${formatDateForInput(block.metadata.due_date)}">
                    </div>
                    <div class="col-md-6">
                        <label for="priority" class="form-label">Prioridad</label>
                        <select class="form-select" id="priority">
                            <option value="low" ${block.metadata.priority === 'low' ? 'selected' : ''}>Baja</option>
                            <option value="medium" ${block.metadata.priority === 'medium' ? 'selected' : ''}>Media</option>
                            <option value="high" ${block.metadata.priority === 'high' ? 'selected' : ''}>Alta</option>
                        </select>
                    </div>
                </div>
            `;
            break;

        case 'frase':
            specificForm = `
                <div class="mb-3">
                    <label for="quoteContent" class="form-label">Frase</label>
                    <textarea class="form-control" id="quoteContent" rows="4" placeholder="Escribe una frase inspiradora...">${block.content || ''}</textarea>
                </div>
                <div class="mb-3">
                    <label for="quoteAuthor" class="form-label">Autor (opcional)</label>
                    <input type="text" class="form-control" id="quoteAuthor" value="${block.metadata.author || ''}" placeholder="Nombre del autor">
                </div>
            `;
            break;

        case 'enlace':
            specificForm = `
                <div class="mb-3">
                    <label for="linkUrl" class="form-label">URL</label>
                    <input type="url" class="form-control" id="linkUrl" value="${block.metadata.url || ''}" placeholder="https://...">
                </div>
                <div class="mb-3">
                    <label for="linkDescription" class="form-label">Descripción</label>
                    <textarea class="form-control" id="linkDescription" rows="3" placeholder="Breve descripción del enlace...">${block.metadata.description || ''}</textarea>
                </div>
            `;
            break;
    }

    return baseForm + specificForm;
}

function initializeEditFormInteractions(block) {
    // Progress slider for goals
    const progressSlider = document.getElementById('goalProgress');
    const progressValue = document.getElementById('progressValue');
    if (progressSlider && progressValue) {
        progressSlider.addEventListener('input', function() {
            progressValue.textContent = this.value;
        });
    }

    // Task management for lists
    if (block.type === 'lista') {
        document.getElementById('addTaskBtn')?.addEventListener('click', addNewTask);
        document.addEventListener('click', function(e) {
            if (e.target.closest('.remove-task')) {
                e.target.closest('.task-item-edit').remove();
            }
        });
    }
}

function addNewTask() {
    const tasksList = document.getElementById('tasksList');
    const newIndex = tasksList.children.length;

    const taskHTML = `
        <div class="task-item-edit mb-2" data-task-index="${newIndex}">
            <div class="input-group">
                <div class="input-group-text">
                    <input type="checkbox" class="task-checkbox">
                </div>
                <input type="text" class="form-control task-text" placeholder="Descripción de la tarea">
                <button class="btn btn-outline-danger btn-sm remove-task" type="button">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        </div>
    `;

    tasksList.insertAdjacentHTML('beforeend', taskHTML);
}

function saveCurrentBlock() {
    if (!currentEditingBlock) return;

    const blockCard = document.querySelector(`[data-block-id="${currentEditingBlock}"]`);
    const blockType = blockCard.dataset.blockType;

    const updateData = {
        title: document.getElementById('blockTitle')?.value || '',
        color: document.getElementById('blockColor')?.value || 'indigo',
        metadata: {}
    };

    // Collect specific data based on block type
    switch (blockType) {
        case 'nota':
            updateData.content = document.getElementById('noteContent')?.value || '';
            break;

        case 'lista':
            const tasks = [];
            document.querySelectorAll('.task-item-edit').forEach(item => {
                const text = item.querySelector('.task-text').value.trim();
                const completed = item.querySelector('.task-checkbox').checked;
                if (text) {
                    tasks.push({ text, completed });
                }
            });
            updateData.metadata.tasks = tasks;
            break;

        case 'meta':
            updateData.content = document.getElementById('goalContent')?.value || '';
            updateData.metadata.progress = parseInt(document.getElementById('goalProgress')?.value || 0);
            updateData.metadata.target_date = document.getElementById('targetDate')?.value || '';
            break;

        case 'recordatorio':
            updateData.content = document.getElementById('reminderContent')?.value || '';
            updateData.metadata.due_date = document.getElementById('dueDate')?.value || '';
            updateData.metadata.priority = document.getElementById('priority')?.value || 'medium';
            break;

        case 'frase':
            updateData.content = document.getElementById('quoteContent')?.value || '';
            updateData.metadata.author = document.getElementById('quoteAuthor')?.value || '';
            break;

        case 'enlace':
            updateData.metadata.url = document.getElementById('linkUrl')?.value || '';
            updateData.metadata.description = document.getElementById('linkDescription')?.value || '';
            break;
    }

    // Save to server
    csrfFetch(`/api/personal-space/blocks/${currentEditingBlock}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(updateData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Close modal
            bootstrap.Modal.getInstance(document.getElementById('editBlockModal')).hide();

            // Update block in UI
            updateBlockInUI(data.block);

            showNotification('Bloque actualizado correctamente', 'success');
        } else {
            showNotification(data.message || 'Error al actualizar el bloque', 'error');
        }
    })
    .catch(error => {
        console.error('Error updating block:', error);
        showNotification('Error de conexión', 'error');
    });
}

function updateBlockInUI(blockData) {
    const blockCard = document.querySelector(`[data-block-id="${blockData.id}"]`);
    if (blockCard) {
        const block = convertBlock(blockData);
        blockCard.outerHTML = createBlockElement(block).outerHTML;
    }
}

function addBlockToUI(blockData) {
    const grid = document.getElementById('blocksGrid');
    if (!grid) return;
    const block = convertBlock(blockData);
    const element = createBlockElement(block);
    const emptyState = grid.querySelector('.empty-state');
    if (emptyState) emptyState.remove();
    const metrics = document.getElementById('dashboardMetrics');
    metrics?.classList.remove('d-none');
    grid.appendChild(element);
    updateDashboardMetrics();
    if (block.type === 'kanban') {
        initializeKanbanBoards();
    }
}

// Block Actions
function deleteBlock(blockId) {
    if (!confirm('¿Estás seguro de que quieres eliminar este bloque?')) {
        return;
    }

    csrfFetch(`/api/personal-space/blocks/${blockId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const blockCard = document.querySelector(`[data-block-id="${blockId}"]`);
            if (blockCard) {
                blockCard.style.transition = 'all 0.3s ease';
                blockCard.style.transform = 'scale(0)';
                blockCard.style.opacity = '0';

                setTimeout(() => {
                    blockCard.remove();

                    // Show empty state if no blocks left
                    const grid = document.getElementById('blocksGrid');
                    if (grid.children.length === 0) {
                        grid.innerHTML = `
                            <div class="empty-state">
                                <div class="empty-icon">
                                    <i class="bi bi-plus-circle"></i>
                                </div>
                                <h3>¡Bienvenido a tu Espacio Personal!</h3>
                                <p>Comienza creando tu primer bloque para organizar tu vida académica</p>
                                <button class="btn btn-primary btn-lg" id="createFirstBlock">
                                    <i class="bi bi-plus-lg"></i>
                                    Crear mi primer bloque
                                </button>
                            </div>
                        `;
                    }
                }, 300);
            }

            showNotification('Bloque eliminado', 'success');
        } else {
            showNotification(data.message || 'Error al eliminar el bloque', 'error');
        }
    })
    .catch(error => {
        console.error('Error deleting block:', error);
        showNotification('Error de conexión', 'error');
    });
}

function toggleBlockFeatured(blockId) {
    const blockCard = document.querySelector(`[data-block-id="${blockId}"]`);
    const isFeatured = blockCard.classList.contains('featured');

    csrfFetch(`/api/personal-space/blocks/${blockId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            is_featured: !isFeatured
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            blockCard.classList.toggle('featured', data.block.is_featured);

            const starIcon = blockCard.querySelector('.featured-star');
            const toggleButton = blockCard.querySelector('.toggle-featured');

            if (data.block.is_featured) {
                if (!starIcon) {
                    const actionsDiv = blockCard.querySelector('.block-actions');
                    actionsDiv.insertAdjacentHTML('afterbegin', '<i class="bi bi-star-fill featured-star" title="Destacado"></i>');
                }
                if (toggleButton) {
                    toggleButton.innerHTML = '<i class="bi bi-star"></i> Quitar destacado';
                }
            } else {
                if (starIcon) {
                    starIcon.remove();
                }
                if (toggleButton) {
                    toggleButton.innerHTML = '<i class="bi bi-star"></i> Destacar';
                }
            }

            showNotification(data.block.is_featured ? 'Bloque destacado' : 'Destacado removido', 'success');
        } else {
            showNotification(data.message || 'Error al actualizar el bloque', 'error');
        }
    })
    .catch(error => {
        console.error('Error toggling featured:', error);
        showNotification('Error de conexión', 'error');
    });
}

function updateBlockOrder() {
    const blocks = [];
    document.querySelectorAll('.block-card').forEach((card, index) => {
        if (card.dataset.blockId) {
            blocks.push({
                id: parseInt(card.dataset.blockId),
                position: index
            });
        }
    });

    csrfFetch('/api/personal-space/blocks/reorder', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ blocks })
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            console.error('Error updating order:', data.message);
        }
    })
    .catch(error => {
        console.error('Error updating order:', error);
    });
}

// UI Controls
function toggleDarkMode() {
    try {
        isDarkMode = !isDarkMode;
        const html = document.documentElement;
        const body = document.body;
        
        // Update classes for better theme support
        html.classList.toggle('dark-mode', isDarkMode);
        html.dataset.bsTheme = isDarkMode ? 'dark' : 'light';
        
        if (isDarkMode) {
            body.classList.add('dark-theme');
            body.classList.remove('light-theme');
        } else {
            body.classList.add('light-theme');
            body.classList.remove('dark-theme');
        }
        
        // Save preference
        localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
        
        // Update button state and theme color
        updateDarkModeButton();
        updateThemeColor();
        
        // Trigger custom event for theme change
        window.dispatchEvent(new CustomEvent('themeChanged', {
            detail: { isDark: isDarkMode, theme: isDarkMode ? 'dark' : 'light' }
        }));
        
        console.log('Dark mode toggled:', isDarkMode);
    } catch (error) {
        console.error('Error toggling dark mode:', error);
    }
}

function updateDarkModeButton() {
    const button = document.getElementById('darkModeToggle');
    if (button) {
        const icon = button.querySelector('i');
        const text = button.querySelector('span') || button.lastChild;

        if (isDarkMode) {
            icon.className = 'bi bi-sun';
            if (text.nodeType === Node.TEXT_NODE) {
                text.textContent = ' Modo Claro';
            }
        } else {
            icon.className = 'bi bi-moon';
            if (text.nodeType === Node.TEXT_NODE) {
                text.textContent = ' Modo Oscuro';
            }
        }
    }
}

function updateThemeColor() {
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) {
        meta.setAttribute('content', isDarkMode ? '#0f172a' : '#ffffff');
    }
}

function applyFocusMode(state) {
    isFocusMode = state;
    document.querySelector('.personal-space-container').classList.toggle('focus-mode', state);

    document.querySelectorAll('.navbar, .sidebar-left, .sidebar-right, .mobile-bottom-nav').forEach(el => {
        if (!el) return;
        el.classList.toggle('tw-hidden', state);
    });

    const exitBtn = document.getElementById('exitFocusBtn');
    if (exitBtn) {
        exitBtn.classList.toggle('d-none', !state);
    }

    const button = document.getElementById('focusModeBtn');
    if (button) {
        const icon = button.querySelector('i');
        const text = button.querySelector('span') || button.lastChild;

        if (state) {
            icon.className = 'bi bi-eye';
            if (text.nodeType === Node.TEXT_NODE) {
                text.textContent = ' Modo Normal';
            }
            button.classList.remove('btn-outline-primary');
            button.classList.add('btn-primary');
        } else {
            icon.className = 'bi bi-eye-slash';
            if (text.nodeType === Node.TEXT_NODE) {
                text.textContent = ' Modo Enfoque';
            }
            button.classList.remove('btn-primary');
            button.classList.add('btn-outline-primary');
        }
    }
}

function toggleFocusMode() {
    const newState = !isFocusMode;
    applyFocusMode(newState);
    localStorage.setItem('focus_mode', newState ? 'on' : 'off');
}

// Suggestion Handling
function handleSuggestionClick(e) {
    const suggestionCard = e.currentTarget.closest('.suggestion-card');
    if (suggestionCard) {
        const action = suggestionCard.dataset.action;

        switch (action) {
            case 'create_objetivo_block':
                if (!blockTypeExists('objetivo')) {
                    fetch('/api/personal-space/create-block', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCsrfToken()
                        },
                        body: JSON.stringify({
                            type: 'objetivo',
                            metadata: { progress: 0, color: 'indigo', icon: DEFAULT_ICONS['objetivo'] }
                        })
                    })
                    .then(res => res.json())
                    .then(data => {
                        if (data.success && data.block) {
                            addBlockToUI(data.block);
                        } else {
                            window.location.reload();
                        }
                    });
                }
                break;
            case 'create_nota_block':
                if (!blockTypeExists('nota_enriquecida')) {
                    csrfFetch('/api/personal-space/blocks', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            type: 'nota_enriquecida',
                            metadata: Object.assign({ color: 'indigo', icon: DEFAULT_ICONS['nota_enriquecida'] }, getDefaultMetadata('nota_enriquecida'))
                        })
                    })
                    .then(res => res.json())
                    .then(data => {
                        if (data.success && data.block) {
                            addBlockToUI(data.block);
                        } else {
                            window.location.reload();
                        }
                    });
                }
                break;
            case 'create_kanban_block':
                if (!blockTypeExists('kanban')) {
                    csrfFetch('/api/personal-space/blocks', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            type: 'kanban',
                            metadata: { columns: { "Por hacer": [], "En curso": [], "Hecho": [] }, color: 'indigo', icon: DEFAULT_ICONS['kanban'] }
                        })
                    })
                    .then(res => res.json())
                    .then(data => {
                        if (data.success && data.block) {
                            addBlockToUI(data.block);
                        } else {
                            window.location.reload();
                        }
                    });
                }
                break;
            case 'create_bloque_block':
                if (!blockTypeExists('bloque')) {
                    createNewBlock('bloque');
                }
                break;
            case 'show_overdue_items':
                showOverdueReminders();
                break;
        }

        // Hide the suggestion
        suggestionCard.style.transition = 'all 0.3s ease';
        suggestionCard.style.transform = 'translateX(100%)';
        suggestionCard.style.opacity = '0';

        setTimeout(() => {
            suggestionCard.remove();

            // Hide suggestions container if empty
            const suggestionsContainer = document.getElementById('smartSuggestions');
            if (suggestionsContainer && suggestionsContainer.querySelectorAll('.suggestion-card').length === 0) {
                suggestionsContainer.style.display = 'none';
            }
        }, 300);

        saveDismissedSuggestion(action);
    }
}

function loadDismissedSuggestions() {
    try {
        return JSON.parse(localStorage.getItem('ps_hidden_suggestions') || '[]');
    } catch (e) {
        return [];
    }
}

function saveDismissedSuggestion(action) {
    const list = loadDismissedSuggestions();
    if (!list.includes(action)) {
        list.push(action);
        localStorage.setItem('ps_hidden_suggestions', JSON.stringify(list));
    }
}

function hideDismissedSuggestions() {
    const hidden = loadDismissedSuggestions();
    if (hidden.length === 0) return;
    const container = document.getElementById('smartSuggestions');
    if (!container) return;
    container.querySelectorAll('.suggestion-card').forEach(card => {
        if (hidden.includes(card.dataset.action)) {
            card.remove();
        }
    });
    if (container.querySelectorAll('.suggestion-card').length === 0) {
        container.style.display = 'none';
    }
}

function blockTypeExists(type) {
    return document.querySelector(`.block-card[data-block-type="${type}"]`) !== null;
}

function showOverdueReminders() {
    const overdueBlocks = document.querySelectorAll('.block-card[data-block-type="recordatorio"]');
    overdueBlocks.forEach(block => {
        if (block.querySelector('.alert-danger')) {
            block.scrollIntoView({ behavior: 'smooth', block: 'center' });
            block.style.animation = 'pulse 2s infinite';

            setTimeout(() => {
                block.style.animation = '';
            }, 4000);
        }
    });
}

// Auto-save Functions
function handleContentChange(e) {
    if (e.target.closest('.block-card')) {
        e.target.dataset.hasChanges = 'true';
    }
}

function autoSaveBlock(blockId) {
    // Implement auto-save logic here if needed
}

function autoSaveChanges() {
    // Implement periodic auto-save logic here if needed
}

// Utility Functions
function formatDate(dateString) {
    if (!dateString) return '';

    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('es-ES', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    } catch (e) {
        return dateString.substring(0, 10);
    }
}

function formatDateForInput(dateString) {
    if (!dateString) return '';

    try {
        const date = new Date(dateString);
        return date.toISOString().slice(0, 16);
    } catch (e) {
        return '';
    }
}

function getCsrfToken() {
    return document.querySelector('meta[name=csrf-token]')?.getAttribute('content') || '';
}

function showNotification(message, type = 'info') {
    // Use existing CRUNEVO notification system if available
    if (window.CRUNEVO_UI && window.CRUNEVO_UI.showSuccessToast) {
        if (type === 'success') {
            window.CRUNEVO_UI.showSuccessToast(message);
        } else if (type === 'error') {
            window.CRUNEVO_UI.showErrorToast(message);
        }
        return;
    }

    // Fallback notification
    const toast = document.createElement('div');
    toast.className = `toast-notification ${type}`;
    toast.innerHTML = `
        <div class="toast-body d-flex align-items-center">
            <i class="bi bi-${getToastIcon(type)} me-2"></i>
            <span class="flex-grow-1">${message}</span>
            <button type="button" class="btn-close btn-sm ms-2" onclick="this.parentElement.parentElement.remove()"></button>
        </div>
    `;

    const container = document.querySelector('.toast-container') || createToastContainer();
    container.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 5000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '1060';
    document.body.appendChild(container);
    return container;
}

function getToastIcon(type) {
    switch (type) {
        case 'success': return 'check-circle';
        case 'error': return 'exclamation-triangle';
        case 'warning': return 'exclamation-triangle';
        default: return 'info-circle';
    }
}

function debounce(func, wait) {
    if (window.CRUNEVO && typeof window.CRUNEVO.debounce === 'function') {
        return window.CRUNEVO.debounce(func, wait);
    }
    let timeout;
    const debounced = function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func(...args), wait);
    };
    debounced.cancel = () => clearTimeout(timeout);
    return debounced;
}

window.initPersonalSpace = initPersonalSpace;

// CSS for animations
const style = document.createElement('style');
style.textContent = `
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }
        100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
    }
`;
document.head.appendChild(style);

// Enhanced Personal Space JavaScript
// Legacy enhanced initialization replaced by initPersonalSpace()

function updateDashboardMetrics() {
    const blocks = document.querySelectorAll('.block-card');
    const metrics = {
        notas: 0,
        tareas: 0,
        objetivos: 0,
        totalProgress: 0,
        progressCount: 0
    };

    blocks.forEach(block => {
        const type = block.dataset.blockType;

        switch(type) {
            case 'nota':
            case 'nota_enriquecida':
                metrics.notas++;
                break;
            case 'tarea':
            case 'lista':
            case 'kanban':
                metrics.tareas++;
                break;
            case 'objetivo':
            case 'meta':
                metrics.objetivos++;
                break;
        }

        // Calculate average progress
        const progressBar = block.querySelector('.progress-bar');
        if (progressBar) {
            const progress = parseInt(progressBar.style.width) || 0;
            metrics.totalProgress += progress;
            metrics.progressCount++;
        }
    });

    // Update DOM
    const notasElement = document.getElementById('notasCount');
    const tareasElement = document.getElementById('tareasCount');
    const objetivosElement = document.getElementById('objetivosCount');
    const progressElement = document.getElementById('progressAvg');

    if (notasElement) notasElement.textContent = metrics.notas;
    if (tareasElement) tareasElement.textContent = metrics.tareas;
    if (objetivosElement) objetivosElement.textContent = metrics.objetivos;

    if (progressElement) {
        const avgProgress = metrics.progressCount > 0 ? 
            Math.round(metrics.totalProgress / metrics.progressCount) : 0;
        progressElement.textContent = `${avgProgress}%`;
    }
}

function initializeKanbanBoards() {
    document.querySelectorAll('.kanban-columns').forEach(kanban => {
        const kanbanId = kanban.dataset.kanbanId;

        kanban.querySelectorAll('.column-tasks').forEach(column => {
            new Sortable(column, {
                group: `kanban-${kanbanId}`,
                animation: 150,
                ghostClass: 'sortable-ghost',
                onEnd: function(evt) {
                    saveKanbanState(kanbanId);
                }
            });
        });
    });
}

function saveKanbanState(kanbanId) {
    const kanban = document.querySelector(`[data-kanban-id="${kanbanId}"]`);
    const columns = {};

    kanban.querySelectorAll('.column-tasks').forEach(column => {
        const columnName = column.dataset.columnTasks;
        const tasks = [];

        column.querySelectorAll('.kanban-task').forEach(task => {
            tasks.push({
                title: task.querySelector('h6').textContent,
                description: task.querySelector('p')?.textContent || '',
                priority: task.querySelector('.task-priority')?.classList.contains('priority-high') ? 'high' : 
                         task.querySelector('.task-priority')?.classList.contains('priority-medium') ? 'medium' : 'low'
            });
        });

        columns[columnName] = tasks;
    });

    // Save to backend
    csrfFetch(`/api/personal-space/blocks/${kanbanId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            metadata: { columns: columns }
        })
    }).catch(error => console.error('Error saving kanban:', error));
}

function toggleTask(blockId) {
    const checkbox = event.target;
    const completed = checkbox.checked;

    csrfFetch(`/api/personal-space/blocks/${blockId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            metadata: { completed: completed }
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateDashboardMetrics();
            // Update visual state
            const card = checkbox.closest('.block-card');
            const title = card.querySelector('.block-title');
            if (completed) {
                title.classList.add('completed');
            } else {
                title.classList.remove('completed');
            }
        }
    })
    .catch(error => console.error('Error updating task:', error));
}

function openKanban(blockId) {
    // Open kanban management modal
    window.location.href = `/personal-space/kanban/${blockId}`;
}

function openBlock(blockId) {
    window.location.href = `/personal-space/bloque/${blockId}`;
}

function editBlock(blockId) {
    // Function to edit a block - calls the modal
    showEditBlockModal(blockId);
}

function manageBloque(blockId) {
    // Open block management interface
    editBlock(blockId);
}

function toggleBloque(blockId) {
    const card = document.querySelector(`[data-block-id="${blockId}"]`);
    const content = card.querySelector('.bloque-content');
    const chevron = card.querySelector('.bi-chevron-down');

    if (content.style.display === 'none') {
        content.style.display = 'block';
        chevron.style.transform = 'rotate(0deg)';
    } else {
        content.style.display = 'none';
        chevron.style.transform = 'rotate(-90deg)';
    }
}

function setupAutoSave() {
    // Auto-save functionality for content changes
    document.addEventListener('input', debounce(function(e) {
        if (e.target.matches('[data-autosave]')) {
            const blockId = e.target.closest('.block-card').dataset.blockId;
            autoSaveBlock(blockId, e.target);
        }
    }, 1000));
}

function autoSaveBlock(blockId, element) {
    const data = {};

    if (element.classList.contains('block-title-edit')) {
        data.title = element.textContent;
    } else if (element.classList.contains('block-content-edit')) {
        data.content = element.textContent;
    }

    csrfFetch(`/api/personal-space/blocks/${blockId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    }).catch(error => console.error('Auto-save error:', error));
}

// Render empty state
function renderEmptyState(container) {
    const emptyState = document.createElement('div');
    emptyState.className = 'empty-state text-center py-5';
    emptyState.innerHTML = `
        <div class="empty-state-icon mb-3">
            <i class="bi bi-journal-plus" style="font-size: 3rem; color: var(--bs-secondary);"></i>
        </div>
        <h4 class="empty-state-title mb-2">No hay bloques creados</h4>
        <p class="empty-state-text text-muted mb-4">Comienza creando tu primer bloque de estudio</p>
        <button class="btn btn-primary" onclick="showCreateBlockModal()">
            <i class="bi bi-plus-circle me-2"></i>Crear primer bloque
        </button>
    `;
    container.appendChild(emptyState);
}

// Setup accessibility features
function setupBlockAccessibility() {
    const blocks = document.querySelectorAll('.block-card');
    blocks.forEach((block, index) => {
        block.setAttribute('tabindex', '0');
        block.setAttribute('role', 'button');
        block.setAttribute('aria-label', `Bloque ${index + 1}`);
        
        // Add keyboard navigation
        block.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                block.click();
            }
        });
    });
}

// Show notification
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existing = document.querySelector('.notification-toast');
    if (existing) {
        existing.remove();
    }
    
    const notification = document.createElement('div');
    notification.className = `notification-toast alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    
    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="bi bi-${type === 'error' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
            <span>${message}</span>
            <button type="button" class="btn-close ms-auto" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Show create block modal
function showCreateBlockModal() {
    const modal = document.getElementById('block-factory-modal');
    if (modal) {
        // Remove any existing backdrops first
        const existingBackdrops = document.querySelectorAll('.modal-backdrop');
        existingBackdrops.forEach(backdrop => backdrop.remove());
        
        // Close any other open modals
        const openModals = document.querySelectorAll('.modal.show');
        openModals.forEach(openModal => {
            const instance = bootstrap.Modal.getInstance(openModal);
            if (instance) instance.hide();
        });
        
        // Wait a bit for cleanup, then show the modal
        setTimeout(() => {
            const bsModal = new bootstrap.Modal(modal, {
                backdrop: true,
                keyboard: true,
                focus: true
            });
            bsModal.show();
        }, 100);
    } else {
        console.error('Block factory modal not found');
        showNotification('Error al abrir el modal de creación', 'error');
    }
}

// Toggle Analytics Dashboard
function toggleAnalytics() {
    const analyticsSection = document.getElementById('analytics-dashboard');
    if (analyticsSection) {
        // Toggle visibility of analytics section using CSS class
        if (analyticsSection.classList.contains('show')) {
            analyticsSection.classList.remove('show');
            showNotification('Panel de Analytics ocultado', 'info');
        } else {
            analyticsSection.classList.add('show');
            analyticsSection.scrollIntoView({ behavior: 'smooth' });
            showNotification('Panel de Analytics activado', 'success');
        }
    } else {
        // If analytics section doesn't exist, redirect to analytics page
        window.location.href = '/personal-space/analytics';
    }
}

// Quick Notes functionality
function showQuickNotesModal() {
    // Create quick notes modal if it doesn't exist
    let modal = document.getElementById('quick-notes-modal');
    if (!modal) {
        modal = createQuickNotesModal();
        document.body.appendChild(modal);
    }
    
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

function createQuickNotesModal() {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = 'quick-notes-modal';
    modal.setAttribute('tabindex', '-1');
    modal.setAttribute('aria-labelledby', 'quickNotesModalLabel');
    modal.setAttribute('aria-hidden', 'true');
    
    modal.innerHTML = `
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="quickNotesModalLabel">
                        <i class="bi bi-lightning-charge me-2"></i>Nota Rápida
                    </h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div class="mb-3">
                        <label for="quickNoteTitle" class="form-label">Título (opcional)</label>
                        <input type="text" class="form-control" id="quickNoteTitle" placeholder="Título de la nota...">
                    </div>
                    <div class="mb-3">
                        <label for="quickNoteContent" class="form-label">Contenido</label>
                        <textarea class="form-control" id="quickNoteContent" rows="4" placeholder="Escribe tu nota rápida aquí..."></textarea>
                    </div>
                    <div class="mb-3">
                        <label for="quickNoteCategory" class="form-label">Categoría</label>
                        <select class="form-select" id="quickNoteCategory">
                            <option value="general">General</option>
                            <option value="ideas">Ideas</option>
                            <option value="recordatorios">Recordatorios</option>
                            <option value="tareas">Tareas</option>
                        </select>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                    <button type="button" class="btn btn-primary" onclick="saveQuickNote()">Guardar Nota</button>
                </div>
            </div>
        </div>
    `;
    
    return modal;
}

function saveQuickNote() {
    const title = document.getElementById('quickNoteTitle').value || 'Nota rápida';
    const content = document.getElementById('quickNoteContent').value;
    const category = document.getElementById('quickNoteCategory').value;
    
    if (!content.trim()) {
        showNotification('El contenido de la nota no puede estar vacío', 'error');
        return;
    }
    
    const blockData = {
        type: 'nota',
        title: title,
        content: content,
        metadata: {
            color: 'blue',
            icon: 'bi-lightning-charge',
            category: category,
            quick_note: true
        }
    };
    
    apiCreateBlock(blockData)
        .then(data => {
            if (data.success && data.block) {
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('quick-notes-modal'));
                if (modal) modal.hide();
                
                // Clear form
                document.getElementById('quickNoteTitle').value = '';
                document.getElementById('quickNoteContent').value = '';
                document.getElementById('quickNoteCategory').value = 'general';
                
                // Add to grid
                const blockElement = createBlockElement(data.block);
                if (blockElement) {
                    const grid = document.getElementById('blocksGrid');
                    if (grid) {
                        const emptyState = grid.querySelector('.empty-state');
                        if (emptyState) emptyState.remove();
                        grid.appendChild(blockElement);
                    }
                }
                
                showNotification('Nota rápida guardada exitosamente', 'success');
            } else {
                showNotification(data.message || 'Error al guardar la nota', 'error');
            }
        })
        .catch(error => {
            console.error('Error saving quick note:', error);
            showNotification('Error de conexión al guardar la nota', 'error');
        });
}

// Setup error handling
function setupErrorHandling() {
    window.addEventListener('error', (e) => {
        console.error('Global error:', e.error);
        showNotification('Ha ocurrido un error inesperado', 'error');
    });
    
    window.addEventListener('unhandledrejection', (e) => {
        console.error('Unhandled promise rejection:', e.reason);
        showNotification('Error en la comunicación con el servidor', 'error');
    });
}

// Setup modal backdrop cleanup
function setupModalBackdropCleanup() {
    // Clean up duplicate backdrops when any modal is shown
    document.addEventListener('shown.bs.modal', function(e) {
        setTimeout(() => {
            const backdrops = document.querySelectorAll('.modal-backdrop');
            if (backdrops.length > 1) {
                // Keep only the last backdrop
                for (let i = 0; i < backdrops.length - 1; i++) {
                    backdrops[i].remove();
                }
            }
        }, 50);
    });
    
    // Clean up all backdrops when any modal is hidden
    document.addEventListener('hidden.bs.modal', function(e) {
        setTimeout(() => {
            const backdrops = document.querySelectorAll('.modal-backdrop');
            const openModals = document.querySelectorAll('.modal.show');
            
            // If no modals are open, remove all backdrops and restore body scroll
            if (openModals.length === 0) {
                backdrops.forEach(backdrop => backdrop.remove());
                // Restore body scroll when all modals are closed
                document.body.style.overflow = '';
                document.body.classList.remove('modal-open');
            }
        }, 100);
    });
}
