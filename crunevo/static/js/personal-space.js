// Personal Space JavaScript
document.addEventListener('DOMContentLoaded', function() {
    initializePersonalSpace();
});

let sortableInstance = null;
let currentEditingBlock = null;
let isDarkMode = (localStorage.getItem('theme') || document.documentElement.dataset.bsTheme) === 'dark';
let isFocusMode = localStorage.getItem('focus_mode') === 'on';

function initializePersonalSpace() {
    // Initialize UI components
    initializeDarkMode();
    initializeFocusMode();
    initializeSortable();
    initializeEventListeners();
    initializeAutoSave();

    // Restore dismissed suggestions
    hideDismissedSuggestions();

    // Load initial data
    loadBlocks();

    // Set up periodic auto-save
    setInterval(autoSaveChanges, 30000); // Auto-save every 30 seconds
}

function initializeDarkMode() {
    const html = document.documentElement;
    if (isDarkMode) {
        html.classList.add('dark-mode');
    } else {
        html.classList.remove('dark-mode');
    }
    html.dataset.bsTheme = isDarkMode ? 'dark' : 'light';
    updateDarkModeButton();
    updateThemeColor();
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
    // Add block buttons
    document.getElementById('addBlockBtn')?.addEventListener('click', showAddBlockModal);
    document.getElementById('floatingAddBtn')?.addEventListener('click', showAddBlockModal);
    document.getElementById('createFirstBlock')?.addEventListener('click', startPersonalSpace);

    // Control buttons
    document.getElementById('darkModeToggle')?.addEventListener('click', toggleDarkMode);
    document.getElementById('focusModeBtn')?.addEventListener('click', toggleFocusMode);
    document.getElementById('exitFocusBtn')?.addEventListener('click', () => {
        if (isFocusMode) toggleFocusMode();
    });

    // Modal events
    document.addEventListener('click', handleModalEvents);
    document.getElementById('saveBlockBtn')?.addEventListener('click', saveCurrentBlock);

    // Suggestion events
    document.addEventListener('click', handleSuggestionClick);

    // Block interaction events
    document.addEventListener('click', handleBlockInteractions);

    // Auto-save on content change
    document.addEventListener('input', debounce(handleContentChange, 500));
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
    fetch('/espacio-personal/api/blocks')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderBlocks(data.blocks);
            }
        })
        .catch(error => {
            console.error('Error loading blocks:', error);
            showNotification('Error al cargar los bloques', 'error');
        });
}

function renderBlocks(blocks) {
    const grid = document.getElementById('blocksGrid');
    if (!grid) return;

    // Clear existing blocks except empty state
    const emptyState = grid.querySelector('.empty-state');
    grid.innerHTML = '';

    if (blocks.length === 0 && emptyState) {
        grid.appendChild(emptyState);
        return;
    }

    blocks.forEach(block => {
        const blockElement = createBlockElement(block);
        grid.appendChild(blockElement);
    });
}

function createBlockElement(block) {
    const div = document.createElement('div');
    div.className = `block-card ${block.color}-block ${block.is_featured ? 'featured' : ''}`;
    div.dataset.blockId = block.id;
    div.dataset.blockType = block.block_type;

    div.innerHTML = generateBlockHTML(block);

    return div;
}

function generateBlockHTML(block) {
    const typeLabels = {
        'nota': 'Nota Rápida',
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
                <h6 class="block-title">${block.title || 'Sin título'}</h6>
                <small class="block-type-label">${typeLabels[block.block_type] || 'Bloque'}</small>
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
            ${block.progress > 0 ? `<div class="progress-badge">${block.progress}%</div>` : ''}
        </div>
    `;
}

function generateBlockContent(block) {
    switch (block.block_type) {
        case 'nota':
            return `
                <div class="note-content">
                    ${block.content ? 
                        `<p>${block.content.substring(0, 200)}${block.content.length > 200 ? '...' : ''}</p>` :
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
                    ${block.content ? `<p class="goal-description">${block.content.substring(0, 100)}...</p>` : ''}
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
                    ${block.content ? `<p>${block.content.substring(0, 150)}...</p>` : ''}
                </div>
            `;

        case 'frase':
            return `
                <div class="quote-content text-center">
                    ${block.content ? `
                        <blockquote class="blockquote">
                            <p>"${block.content}"</p>
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
                                    <p class="text-muted">${block.metadata.description.substring(0, 100)}</p>
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
    const modal = new bootstrap.Modal(document.getElementById('addBlockModal'));
    modal.show();
}

function handleModalEvents(e) {
    if (e.target.closest('.block-type-card')) {
        const blockType = e.target.closest('.block-type-card').dataset.type;
        createNewBlock(blockType);
    }
}

function apiCreateBlock(blockData) {
    return fetch('/espacio-personal/api/blocks', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(blockData)
    }).then(response => response.json());
}

function createNewBlock(type) {
    const blockData = {
        block_type: type,
        title: getDefaultTitle(type),
        content: '',
        color: 'indigo',
        metadata: getDefaultMetadata(type)
    };

    apiCreateBlock(blockData)
        .then(data => {
            if (data.success) {
                bootstrap.Modal.getInstance(document.getElementById('addBlockModal'))?.hide();

                const blockElement = createBlockElement(data.block);
                blockElement.classList.add('new-block');

                const grid = document.getElementById('blocksGrid');
                const emptyState = grid.querySelector('.empty-state');
                if (emptyState) {
                    emptyState.remove();
                }

                grid.appendChild(blockElement);

                setTimeout(() => {
                    showEditBlockModal(data.block.id);
                }, 500);

                showNotification('Bloque creado exitosamente', 'success');
            } else {
                showNotification(data.message || 'Error al crear el bloque', 'error');
            }
        })
        .catch(error => {
            console.error('Error creating block:', error);
            showNotification('Error de conexión', 'error');
        });
}

function getDefaultTitle(type) {
    const titles = {
        'nota': 'Nueva nota',
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
        default:
            return {};
    }
}

function startPersonalSpace() {
    // Create initial blocks: note, kanban and goal
    ['nota', 'kanban', 'objetivo'].forEach(type => createNewBlock(type));
    showNotification('Espacio inicial creado', 'success');
}

// Block Editing Functions
function handleBlockInteractions(e) {
    const blockCard = e.target.closest('.block-card');
    if (!blockCard) return;

    const blockId = blockCard.dataset.blockId;

    if (e.target.closest('.edit-block')) {
        e.preventDefault();
        showEditBlockModal(blockId);
    } else if (e.target.closest('.delete-block')) {
        e.preventDefault();
        deleteBlock(blockId);
    } else if (e.target.closest('.toggle-featured')) {
        e.preventDefault();
        toggleBlockFeatured(blockId);
    } else if (e.target.closest('.block-content') && !e.target.closest('.dropdown')) {
        showEditBlockModal(blockId);
    }
}

function showEditBlockModal(blockId) {
    const blockCard = document.querySelector(`[data-block-id="${blockId}"]`);
    if (!blockCard) return;

    const blockType = blockCard.dataset.blockType;
    currentEditingBlock = blockId;

    // Get current block data
    fetch(`/espacio-personal/api/blocks`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const block = data.blocks.find(b => b.id == blockId);
                if (block) {
                    renderEditForm(block);
                    const modal = new bootstrap.Modal(document.getElementById('editBlockModal'));
                    modal.show();
                }
            }
        })
        .catch(error => {
            console.error('Error loading block data:', error);
            showNotification('Error al cargar los datos del bloque', 'error');
        });
}

function renderEditForm(block) {
    const content = document.getElementById('editBlockContent');
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

    switch (block.block_type) {
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
    if (block.block_type === 'lista') {
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
    fetch(`/espacio-personal/api/blocks/${currentEditingBlock}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
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
        blockCard.outerHTML = createBlockElement(blockData).outerHTML;
    }
}

// Block Actions
function deleteBlock(blockId) {
    if (!confirm('¿Estás seguro de que quieres eliminar este bloque?')) {
        return;
    }

    fetch(`/espacio-personal/api/blocks/${blockId}`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCsrfToken()
        }
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

    fetch(`/espacio-personal/api/blocks/${blockId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
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

    fetch('/espacio-personal/api/blocks/reorder', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
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
    isDarkMode = !isDarkMode;
    const html = document.documentElement;
    html.classList.toggle('dark-mode', isDarkMode);
    html.dataset.bsTheme = isDarkMode ? 'dark' : 'light';
    localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
    updateDarkModeButton();
    updateThemeColor();
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
    if (e.target.closest('.suggestion-btn')) {
        const suggestionCard = e.target.closest('.suggestion-card');
        const action = suggestionCard.dataset.action;

        switch (action) {
            case 'create_objetivo_block':
                if (!blockTypeExists('objetivo')) {
                    createNewBlock('objetivo');
                }
                break;
            case 'create_nota_block':
                if (!blockTypeExists('nota')) {
                    createNewBlock('nota');
                }
                break;
            case 'create_kanban_block':
                if (!blockTypeExists('kanban')) {
                    createNewBlock('kanban');
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
    console.log('Auto-saving block:', blockId);
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
document.addEventListener('DOMContentLoaded', function() {
    // Initialize features
    initializeSortable();
    initializeModals();
    initializeControls();
    loadSuggestions();
    updateDashboardMetrics();
    initializeKanbanBoards();
    setupAutoSave();
});

function loadSuggestions() {
    fetch('/espacio-personal/api/suggestions')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.suggestions.length > 0) {
                showSuggestions(data.suggestions);
            }
        })
        .catch(error => console.error('Error loading suggestions:', error));
}

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
        const type = block.dataset.type;

        switch(type) {
            case 'nota':
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
    fetch(`/espacio-personal/api/blocks/${kanbanId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            metadata: { columns: columns }
        })
    }).catch(error => console.error('Error saving kanban:', error));
}

function toggleTask(blockId) {
    const checkbox = event.target;
    const completed = checkbox.checked;

    fetch(`/espacio-personal/api/blocks/${blockId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
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
    window.location.href = `/espacio-personal/kanban/${blockId}`;
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

    fetch(`/espacio-personal/api/blocks/${blockId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(data)
    }).catch(error => console.error('Auto-save error:', error));
}

function debounce(func, wait) {
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
