document.addEventListener('DOMContentLoaded', () => {
  const main = document.querySelector('.objective-page');
  if (!main) return;

  const state = {
    objective: {
      id: Number(main.dataset.objectiveId),
      title: '',
      desc: '',
      due_at: '',
      status: '',
      priority: '',
      progress: 0,
      milestones: [],
      resources: [],
      timeline: [],
      stats: { total_milestones: 0, done_milestones: 0, days_left: 0, streak: 0, velocity_week: 0 }
    }
  };

  // Performance tracking
  let performanceData = {
    weeklyProgress: [],
    lastProgressUpdate: null,
    velocity: 0
  };

  function debounce(fn, delay = 500) {
    let t;
    return (...args) => {
      clearTimeout(t);
      t = setTimeout(() => fn(...args), delay);
    };
  }

  const saveField = debounce((field, value) => {
    console.log('Saving', field, value);
    addTimelineEvent(`Campo ${field} actualizado`, 'edit');
  });

  // Utility functions
  function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  function safeQuerySelector(selector) {
    return document.querySelector(selector);
  }

  function safeQuerySelectorAll(selector) {
    return document.querySelectorAll(selector);
  }

  // Timeline management
  function addTimelineEvent(title, type = 'info', data = null) {
    const event = {
      id: generateId(),
      title,
      type,
      timestamp: new Date().toISOString(),
      data
    };
    
    state.objective.timeline.unshift(event);
    
    // Keep only last 10 events
    if (state.objective.timeline.length > 10) {
      state.objective.timeline = state.objective.timeline.slice(0, 10);
    }
    
    renderTimeline();
  }

  function renderTimeline() {
    const timelineEl = safeQuerySelector('[data-timeline]');
    if (!timelineEl) return;
    
    timelineEl.innerHTML = '';
    state.objective.timeline.forEach(event => {
      const item = document.createElement('div');
      item.className = `timeline-item timeline-item--${event.type}`;
      item.innerHTML = `
        <div class="timeline-time">${new Date(event.timestamp).toLocaleString()}</div>
        <div class="timeline-title">${event.title}</div>
      `;
      timelineEl.appendChild(item);
    });
  }

  // Editable fields
  ['title', 'desc'].forEach(field => {
    const el = document.querySelector(`[data-field="${field}"]`);
    if (el) {
      el.addEventListener('input', () => {
        state.objective[field] = el.textContent.trim();
        saveField(field, state.objective[field]);
      });
    }
  });

  ['due_at', 'status', 'priority'].forEach(field => {
    const el = document.querySelector(`[data-field="${field}"]`);
    if (el) {
      el.addEventListener('change', () => {
        state.objective[field] = el.value;
        saveField(field, state.objective[field]);
      });
      state.objective[field] = el.value;
    }
  });

  // Milestones
  const milestoneList = document.querySelector('[data-milestone-list]');
  function updateMilestoneProgress(m) {
    if (m.subtasks && m.subtasks.length) {
      const done = m.subtasks.filter(s => s.done).length;
      m.progress = (done / m.subtasks.length) * 100;
      m.done = done === m.subtasks.length;
    } else {
      m.progress = m.done ? 100 : 0;
    }
    updateObjectiveProgress();
    addTimelineEvent(`Meta "${m.title}" actualizada`, 'milestone');
  }

  function renderSubtasks(milestone) {
    const subtaskList = document.createElement('ul');
    subtaskList.className = 'subtask-list';
    
    if (milestone.subtasks && milestone.subtasks.length) {
      milestone.subtasks.forEach((subtask, idx) => {
        const li = document.createElement('li');
        li.className = 'subtask-item';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = subtask.done;
        checkbox.addEventListener('change', () => {
          subtask.done = checkbox.checked;
          updateMilestoneProgress(milestone);
          saveField('milestones', state.objective.milestones);
        });
        
        const span = document.createElement('span');
        span.contentEditable = true;
        span.textContent = subtask.title;
        span.addEventListener('input', () => {
          subtask.title = span.textContent.trim();
          saveField('milestones', state.objective.milestones);
        });
        
        const deleteBtn = document.createElement('button');
        deleteBtn.textContent = '×';
        deleteBtn.className = 'btn-delete-subtask';
        deleteBtn.addEventListener('click', () => {
          milestone.subtasks.splice(idx, 1);
          updateMilestoneProgress(milestone);
          renderMilestones();
          saveField('milestones', state.objective.milestones);
        });
        
        li.append(checkbox, span, deleteBtn);
        subtaskList.appendChild(li);
      });
    }
    
    const addSubtaskBtn = document.createElement('button');
    addSubtaskBtn.textContent = '+ Agregar subtarea';
    addSubtaskBtn.className = 'btn-add-subtask';
    addSubtaskBtn.addEventListener('click', () => {
      if (!milestone.subtasks) milestone.subtasks = [];
      milestone.subtasks.push({
        id: generateId(),
        title: 'Nueva subtarea',
        done: false
      });
      renderMilestones();
      saveField('milestones', state.objective.milestones);
    });
    
    subtaskList.appendChild(addSubtaskBtn);
    return subtaskList;
  }

  function renderMilestones() {
    milestoneList.innerHTML = '';
    state.objective.milestones.forEach((m, idx) => {
      const li = document.createElement('li');
      li.className = 'milestone-item';
      li.draggable = true;
      li.dataset.id = m.id;

      const header = document.createElement('div');
      header.className = 'milestone-header';

      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.checked = m.done;
      checkbox.addEventListener('change', () => {
        m.done = checkbox.checked;
        updateMilestoneProgress(m);
        saveField('milestones', state.objective.milestones);
      });

      const span = document.createElement('span');
      span.contentEditable = true;
      span.textContent = m.title;
      span.addEventListener('input', () => {
        m.title = span.textContent.trim();
        saveField('milestones', state.objective.milestones);
      });

      const weightInput = document.createElement('input');
      weightInput.type = 'number';
      weightInput.min = '1';
      weightInput.max = '10';
      weightInput.value = m.weight || 1;
      weightInput.className = 'milestone-weight';
      weightInput.addEventListener('change', () => {
        m.weight = Number(weightInput.value) || 1;
        updateObjectiveProgress();
        saveField('milestones', state.objective.milestones);
      });

      const progressBar = document.createElement('div');
      progressBar.className = 'milestone-progress';
      progressBar.innerHTML = `<div class="milestone-progress-fill" style="width: ${m.progress || 0}%"></div>`;

      const deleteBtn = document.createElement('button');
      deleteBtn.textContent = '×';
      deleteBtn.className = 'btn-delete-milestone';
      deleteBtn.addEventListener('click', () => {
        state.objective.milestones.splice(idx, 1);
        renderMilestones();
        saveField('milestones', state.objective.milestones);
      });

      header.append(checkbox, span, weightInput, progressBar, deleteBtn);
      li.appendChild(header);
      
      // Add subtasks
      const subtaskContainer = renderSubtasks(m);
      li.appendChild(subtaskContainer);

      li.addEventListener('dragstart', e => {
        e.dataTransfer.setData('text/plain', idx);
      });
      li.addEventListener('dragover', e => e.preventDefault());
      li.addEventListener('drop', e => {
        e.preventDefault();
        const from = Number(e.dataTransfer.getData('text/plain'));
        const to = idx;
        const arr = state.objective.milestones;
        arr.splice(to, 0, arr.splice(from, 1)[0]);
        renderMilestones();
        saveField('milestones', arr);
      });

      milestoneList.appendChild(li);
    });
    updateObjectiveProgress();
  }

  document.querySelector('.add-milestone')?.addEventListener('click', () => {
    const id = generateId();
    state.objective.milestones.push({ 
      id, 
      title: 'Nueva Meta', 
      weight: 1, 
      progress: 0, 
      done: false, 
      subtasks: [],
      evidences: []
    });
    renderMilestones();
    addTimelineEvent('Nueva meta agregada', 'milestone');
    saveField('milestones', state.objective.milestones);
  });

  // Resources
  const resourceList = document.querySelector('[data-resource-list]');
  function renderResources() {
    resourceList.innerHTML = '';
    state.objective.resources.forEach((r, idx) => {
      const li = document.createElement('li');
      li.className = 'resource-item';
      
      const link = document.createElement('a');
      link.href = r.url;
      link.textContent = r.label;
      link.target = '_blank';
      
      const typeSpan = document.createElement('span');
      typeSpan.className = 'resource-type';
      typeSpan.textContent = r.type || 'link';
      
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.textContent = 'Abrir';
      btn.className = 'btn-open-resource';
      btn.addEventListener('click', () => window.open(r.url, '_blank'));
      
      const deleteBtn = document.createElement('button');
      deleteBtn.textContent = '×';
      deleteBtn.className = 'btn-delete-resource';
      deleteBtn.addEventListener('click', () => {
        state.objective.resources.splice(idx, 1);
        renderResources();
        saveField('resources', state.objective.resources);
      });
      
      li.append(typeSpan, link, btn, deleteBtn);
      resourceList.appendChild(li);
    });
  }

  document.querySelector('.add-resource')?.addEventListener('click', () => {
    const label = prompt('Etiqueta');
    const url = prompt('URL');
    const type = prompt('Tipo (link, document, video, etc.)', 'link');
    if (label && url) {
      state.objective.resources.push({ 
        id: generateId(), 
        type: type || 'link', 
        label, 
        url 
      });
      renderResources();
      addTimelineEvent(`Recurso "${label}" agregado`, 'resource');
      saveField('resources', state.objective.resources);
    }
  });

  // Stats
  const statsEl = document.querySelector('[data-stats]');
  function renderStats() {
    const s = state.objective.stats;
    s.total_milestones = state.objective.milestones.length;
    s.done_milestones = state.objective.milestones.filter(m => m.done).length;
    
    // Calculate total subtasks
    s.total_subtasks = state.objective.milestones.reduce((sum, m) => 
      sum + (m.subtasks ? m.subtasks.length : 0), 0);
    s.done_subtasks = state.objective.milestones.reduce((sum, m) => 
      sum + (m.subtasks ? m.subtasks.filter(st => st.done).length : 0), 0);
    
    if (state.objective.due_at) {
      const due = new Date(state.objective.due_at);
      s.days_left = Math.ceil((due - new Date()) / 86400000);
    }
    
    // Calculate velocity (progress per week)
    const now = new Date();
    if (performanceData.lastProgressUpdate) {
      const daysSinceUpdate = (now - performanceData.lastProgressUpdate) / (1000 * 60 * 60 * 24);
      if (daysSinceUpdate >= 7) {
        performanceData.weeklyProgress.push(state.objective.progress);
        performanceData.lastProgressUpdate = now;
        if (performanceData.weeklyProgress.length > 1) {
          const lastWeek = performanceData.weeklyProgress[performanceData.weeklyProgress.length - 2];
          s.velocity_week = state.objective.progress - lastWeek;
        }
      }
    } else {
      performanceData.lastProgressUpdate = now;
    }
    
    const el = statsEl;
    if (el) {
      el.innerHTML = `
        <div class="stat-item">
          <span class="stat-label">Metas:</span>
          <span class="stat-value">${s.done_milestones}/${s.total_milestones}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Subtareas:</span>
          <span class="stat-value">${s.done_subtasks}/${s.total_subtasks}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Días restantes:</span>
          <span class="stat-value">${s.days_left}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Velocidad semanal:</span>
          <span class="stat-value">${s.velocity_week.toFixed(1)}%</span>
        </div>
      `;
    }
  }

  function updateObjectiveProgress() {
    const arr = state.objective.milestones;
    const totalWeight = arr.reduce((sum, m) => sum + (m.weight || 1), 0) || 1;
    const prog = arr.reduce((sum, m) => sum + (m.weight || 1) * m.progress, 0) / totalWeight;
    state.objective.progress = prog;
    const bar = document.querySelector('[data-progress-bar]');
    if (bar) bar.style.width = `${prog}%`;
    const num = document.querySelector('[data-progress-number]');
    if (num) num.textContent = `${Math.round(prog)}%`;
    renderStats();
  }

  // Focus mode
  const overlay = document.querySelector('[data-focus-overlay]');
  let focusTimer = null;
  let focusStartTime = null;
  
  document.querySelector('.btn-focus')?.addEventListener('click', () => {
    const active = main.classList.toggle('focus-mode');
    if (overlay) overlay.hidden = !active;
    document.querySelector('[data-left]')?.setAttribute('aria-hidden', active ? 'true' : 'false');
    document.querySelector('[data-right]')?.setAttribute('aria-hidden', active ? 'true' : 'false');
    
    if (active) {
      focusStartTime = new Date();
      startFocusTimer();
      addTimelineEvent('Modo enfoque activado', 'focus');
    } else {
      if (focusStartTime) {
        const focusTime = Math.round((new Date() - focusStartTime) / 60000); // minutes
        addTimelineEvent(`Sesión de enfoque completada: ${focusTime} minutos`, 'focus');
      }
      stopFocusTimer();
    }
  });
  
  function startFocusTimer() {
    const timerEl = document.querySelector('[data-focus-timer]');
    if (!timerEl) return;
    
    focusTimer = setInterval(() => {
      if (focusStartTime) {
        const elapsed = Math.floor((new Date() - focusStartTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        timerEl.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
      }
    }, 1000);
  }
  
  function stopFocusTimer() {
    if (focusTimer) {
      clearInterval(focusTimer);
      focusTimer = null;
    }
    const timerEl = document.querySelector('[data-focus-timer]');
    if (timerEl) timerEl.textContent = '00:00';
  }

  function updateMotivacion(value) {
    const el = document.querySelector('[data-motivacion]');
    if (el) el.textContent = value;
  }
  
  // Modal management
  function openModal(modalId) {
    const modal = document.querySelector(`[data-modal="${modalId}"]`);
    if (modal) {
      modal.classList.add('modal--active');
      document.body.classList.add('modal-open');
    }
  }
  
  function closeModal(modalId) {
    const modal = document.querySelector(`[data-modal="${modalId}"]`);
    if (modal) {
      modal.classList.remove('modal--active');
      document.body.classList.remove('modal-open');
    }
  }
  
  // Close modals on backdrop click
  document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
      e.target.classList.remove('modal--active');
      document.body.classList.remove('modal-open');
    }
  });
  
  // Evidence management
  function addEvidence(milestoneId, evidence) {
    const milestone = state.objective.milestones.find(m => m.id === milestoneId);
    if (milestone) {
      if (!milestone.evidences) milestone.evidences = [];
      milestone.evidences.push({
        id: generateId(),
        type: evidence.type,
        title: evidence.title,
        url: evidence.url,
        timestamp: new Date().toISOString()
      });
      saveField('milestones', state.objective.milestones);
      addTimelineEvent(`Evidencia agregada a "${milestone.title}"`, 'evidence');
    }
  }
  
  // Keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    if (e.ctrlKey || e.metaKey) {
      switch (e.key) {
        case 'f':
          e.preventDefault();
          document.querySelector('.btn-focus')?.click();
          break;
        case 'm':
          e.preventDefault();
          document.querySelector('.add-milestone')?.click();
          break;
        case 'r':
          e.preventDefault();
          document.querySelector('.add-resource')?.click();
          break;
      }
    }
  });

  // Enhanced statistics rendering
  function renderStats() {
    const stats = state.objective.stats;
    
    // Update individual stat elements
    const totalEl = safeQuerySelector('[data-stat-total]');
    const completedEl = safeQuerySelector('[data-stat-completed]');
    const daysEl = safeQuerySelector('[data-stat-days]');
    const velocityEl = safeQuerySelector('[data-stat-velocity]');
    const etaEl = safeQuerySelector('[data-stat-eta]');
    
    if (totalEl) totalEl.textContent = stats.total_milestones;
    if (completedEl) completedEl.textContent = stats.done_milestones;
    if (daysEl) {
      if (stats.days_left > 0) {
        daysEl.textContent = stats.days_left;
        daysEl.parentElement.className = 'stat-card';
      } else if (stats.days_left === 0) {
        daysEl.textContent = 'Hoy';
        daysEl.parentElement.className = 'stat-card stat-card--warning';
      } else {
        daysEl.textContent = `+${Math.abs(stats.days_left)}`;
        daysEl.parentElement.className = 'stat-card stat-card--danger';
      }
    }
    
    if (velocityEl) {
      velocityEl.textContent = `${stats.velocity_week.toFixed(1)}%`;
    }
    
    if (etaEl) {
      const eta = calculateETA();
      etaEl.textContent = eta;
    }
  }
  
  function calculateETA() {
    const stats = state.objective.stats;
    const remainingProgress = 100 - state.objective.progress;
    
    if (stats.velocity_week <= 0 || remainingProgress <= 0) {
      return '--';
    }
    
    const weeksToComplete = remainingProgress / stats.velocity_week;
    const daysToComplete = Math.ceil(weeksToComplete * 7);
    
    if (daysToComplete > 365) {
      return '> 1 año';
    } else if (daysToComplete > 30) {
      const months = Math.ceil(daysToComplete / 30);
      return `${months} mes${months > 1 ? 'es' : ''}`;
    } else {
      return `${daysToComplete} día${daysToComplete > 1 ? 's' : ''}`;
    }
  }
  
  // Resource modal handling
  function initializeResourceModal() {
    const modal = safeQuerySelector('[data-resource-modal]');
    const form = safeQuerySelector('[data-resource-form]');
    const closeButtons = safeQuerySelectorAll('[data-modal-close]');
    const backdrop = safeQuerySelector('[data-modal-backdrop]');
    
    if (!modal || !form) return;
    
    // Open modal
    function openResourceModal() {
      modal.hidden = false;
      modal.setAttribute('aria-hidden', 'false');
      document.body.style.overflow = 'hidden';
      
      // Focus first input
      const firstInput = form.querySelector('input');
      if (firstInput) {
        setTimeout(() => firstInput.focus(), 100);
      }
    }
    
    // Close modal
    function closeResourceModal() {
      modal.hidden = true;
      modal.setAttribute('aria-hidden', 'true');
      document.body.style.overflow = '';
      form.reset();
      clearErrors();
    }
    
    // Clear form errors
    function clearErrors() {
      const errorElements = form.querySelectorAll('.form-error');
      errorElements.forEach(el => {
        el.hidden = true;
        el.textContent = '';
      });
    }
    
    // Show error
    function showError(fieldId, message) {
      const errorEl = form.querySelector(`#${fieldId}-error`);
      if (errorEl) {
        errorEl.textContent = message;
        errorEl.hidden = false;
      }
    }
    
    // Validate URL
    function isValidUrl(string) {
      try {
        new URL(string);
        return true;
      } catch (_) {
        return false;
      }
    }
    
    // Event listeners
    document.addEventListener('click', (e) => {
      if (e.target.matches('.add-resource, .add-resource-cta')) {
        e.preventDefault();
        openResourceModal();
      }
    });
    
    closeButtons.forEach(btn => {
      btn.addEventListener('click', closeResourceModal);
    });
    
    if (backdrop) {
      backdrop.addEventListener('click', closeResourceModal);
    }
    
    // Form submission
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      clearErrors();
      
      const labelInput = form.querySelector('#resource-label');
      const urlInput = form.querySelector('#resource-url');
      
      const label = labelInput?.value.trim();
      const url = urlInput?.value.trim();
      
      let hasErrors = false;
      
      if (!label) {
        showError('label', 'La etiqueta es requerida');
        hasErrors = true;
      }
      
      if (!url) {
        showError('url', 'La URL es requerida');
        hasErrors = true;
      } else if (!isValidUrl(url)) {
        showError('url', 'La URL no es válida');
        hasErrors = true;
      }
      
      if (!hasErrors) {
        state.objective.resources.push({
          id: generateId(),
          type: 'link',
          label,
          url
        });
        
        renderResources();
        addTimelineEvent(`Recurso "${label}" agregado`, 'resource');
        saveField('resources', state.objective.resources);
        closeResourceModal();
      }
    });
    
    // Escape key to close
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !modal.hidden) {
        closeResourceModal();
      }
    });
  }
  
  // Enhanced milestone rendering with all features
  function renderMilestones() {
    const milestoneList = safeQuerySelector('[data-milestone-list]');
    const emptyState = safeQuerySelector('[data-milestones-empty]');
    const skeleton = safeQuerySelector('[data-skeleton]');
    
    if (!milestoneList) return;
    
    // Hide skeleton
    if (skeleton) skeleton.hidden = true;
    
    // Clear existing content
    milestoneList.innerHTML = '';
    
    if (state.objective.milestones.length === 0) {
      if (emptyState) emptyState.hidden = false;
      return;
    }
    
    if (emptyState) emptyState.hidden = true;
    
    state.objective.milestones.forEach((milestone, index) => {
      const li = document.createElement('li');
      li.className = 'milestone-item';
      li.draggable = true;
      li.dataset.id = milestone.id;
      
      // Header section
      const header = document.createElement('div');
      header.className = 'milestone-item__header';
      
      // Checkbox
      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.className = 'milestone-item__checkbox';
      checkbox.checked = milestone.done;
      checkbox.addEventListener('change', () => {
        milestone.done = checkbox.checked;
        updateMilestoneProgress(milestone);
        updateObjectiveProgress();
        renderStats();
        addTimelineEvent(`Meta "${milestone.title}" ${milestone.done ? 'completada' : 'marcada como pendiente'}`, 'milestone');
        saveField('milestones', state.objective.milestones);
      });
      
      // Title (editable)
      const title = document.createElement('input');
      title.type = 'text';
      title.className = 'milestone-item__title';
      title.value = milestone.title;
      title.addEventListener('input', debounce(() => {
        milestone.title = title.value;
        saveField('milestones', state.objective.milestones);
      }, 300));
      
      // Actions
      const actions = document.createElement('div');
      actions.className = 'milestone-item__actions';
      
      const expandBtn = document.createElement('button');
      expandBtn.type = 'button';
      expandBtn.className = 'btn btn--icon';
      expandBtn.innerHTML = '<i class="bi bi-chevron-down" aria-hidden="true"></i>';
      expandBtn.setAttribute('aria-label', 'Expandir detalles');
      
      const deleteBtn = document.createElement('button');
      deleteBtn.type = 'button';
      deleteBtn.className = 'btn btn--icon';
      deleteBtn.innerHTML = '<i class="bi bi-trash" aria-hidden="true"></i>';
      deleteBtn.setAttribute('aria-label', 'Eliminar meta');
      deleteBtn.addEventListener('click', () => {
        if (confirm('¿Estás seguro de que quieres eliminar esta meta?')) {
          state.objective.milestones.splice(index, 1);
          renderMilestones();
          updateObjectiveProgress();
          renderStats();
          addTimelineEvent(`Meta "${milestone.title}" eliminada`, 'milestone');
          saveField('milestones', state.objective.milestones);
        }
      });
      
      actions.append(expandBtn, deleteBtn);
      header.append(checkbox, title, actions);
      
      // Progress bar
      const progressBar = document.createElement('div');
      progressBar.className = 'milestone-item__progress';
      const progressFill = document.createElement('div');
      progressFill.className = 'milestone-item__progress-fill';
      progressFill.style.width = `${milestone.progress || 0}%`;
      progressBar.appendChild(progressFill);
      
      // Details section (initially hidden)
      const details = document.createElement('div');
      details.className = 'milestone-item__details';
      details.hidden = true;
      
      // Weight control
      const weightControl = document.createElement('div');
      weightControl.className = 'milestone-item__weight';
      weightControl.innerHTML = `
        <label class="milestone-item__weight-label">Peso:</label>
        <input type="number" class="milestone-item__weight-input" min="1" max="10" value="${milestone.weight || 1}">
      `;
      
      const weightInput = weightControl.querySelector('input');
      weightInput.addEventListener('change', () => {
        milestone.weight = parseInt(weightInput.value) || 1;
        updateObjectiveProgress();
        renderStats();
        saveField('milestones', state.objective.milestones);
      });
      
      // Subtasks section
      const subtasksSection = document.createElement('div');
      subtasksSection.className = 'subtasks';
      subtasksSection.innerHTML = '<h4>Subtareas</h4>';
      
      const subtasksList = document.createElement('ul');
      subtasksList.className = 'subtasks-list';
      
      if (milestone.subtasks) {
        milestone.subtasks.forEach((subtask, subtaskIndex) => {
          const subtaskItem = document.createElement('li');
          subtaskItem.className = 'subtask-item';
          
          const subtaskCheckbox = document.createElement('input');
          subtaskCheckbox.type = 'checkbox';
          subtaskCheckbox.className = 'subtask-item__checkbox';
          subtaskCheckbox.checked = subtask.done;
          subtaskCheckbox.addEventListener('change', () => {
            subtask.done = subtaskCheckbox.checked;
            updateMilestoneProgress(milestone);
            updateObjectiveProgress();
            renderStats();
            saveField('milestones', state.objective.milestones);
          });
          
          const subtaskTitle = document.createElement('input');
          subtaskTitle.type = 'text';
          subtaskTitle.className = 'subtask-item__title';
          subtaskTitle.value = subtask.title;
          subtaskTitle.addEventListener('input', debounce(() => {
            subtask.title = subtaskTitle.value;
            saveField('milestones', state.objective.milestones);
          }, 300));
          
          const subtaskDelete = document.createElement('button');
          subtaskDelete.type = 'button';
          subtaskDelete.className = 'btn btn--icon';
          subtaskDelete.innerHTML = '<i class="bi bi-x" aria-hidden="true"></i>';
          subtaskDelete.addEventListener('click', () => {
            milestone.subtasks.splice(subtaskIndex, 1);
            updateMilestoneProgress(milestone);
            renderMilestones();
            saveField('milestones', state.objective.milestones);
          });
          
          subtaskItem.append(subtaskCheckbox, subtaskTitle, subtaskDelete);
          subtasksList.appendChild(subtaskItem);
        });
      }
      
      const addSubtaskBtn = document.createElement('button');
      addSubtaskBtn.type = 'button';
      addSubtaskBtn.className = 'btn btn--secondary btn--sm';
      addSubtaskBtn.innerHTML = '<i class="bi bi-plus" aria-hidden="true"></i> <span>Agregar Subtarea</span>';
      addSubtaskBtn.addEventListener('click', () => {
        if (!milestone.subtasks) milestone.subtasks = [];
        milestone.subtasks.push({
          id: generateId(),
          title: 'Nueva subtarea',
          done: false
        });
        renderMilestones();
        saveField('milestones', state.objective.milestones);
      });
      
      subtasksSection.append(subtasksList, addSubtaskBtn);
      details.append(weightControl, subtasksSection);
      
      // Expand/collapse functionality
      let isExpanded = false;
      expandBtn.addEventListener('click', () => {
        isExpanded = !isExpanded;
        details.hidden = !isExpanded;
        expandBtn.innerHTML = isExpanded 
          ? '<i class="bi bi-chevron-up" aria-hidden="true"></i>'
          : '<i class="bi bi-chevron-down" aria-hidden="true"></i>';
        expandBtn.setAttribute('aria-expanded', isExpanded.toString());
      });
      
      // Drag and drop
      li.addEventListener('dragstart', (e) => {
        e.dataTransfer.setData('text/plain', index.toString());
        li.classList.add('dragging');
      });
      
      li.addEventListener('dragend', () => {
        li.classList.remove('dragging');
      });
      
      li.addEventListener('dragover', (e) => {
        e.preventDefault();
      });
      
      li.addEventListener('drop', (e) => {
        e.preventDefault();
        const draggedIndex = parseInt(e.dataTransfer.getData('text/plain'));
        if (draggedIndex !== index) {
          const draggedItem = state.objective.milestones.splice(draggedIndex, 1)[0];
          state.objective.milestones.splice(index, 0, draggedItem);
          renderMilestones();
          saveField('milestones', state.objective.milestones);
        }
      });
      
      li.append(header, progressBar, details);
      milestoneList.appendChild(li);
    });
  }
  
  // Enhanced resource rendering
  function renderResources() {
    const resourceList = safeQuerySelector('[data-resource-list]');
    const emptyState = safeQuerySelector('[data-resources-empty]');
    
    if (!resourceList) return;
    
    resourceList.innerHTML = '';
    
    if (state.objective.resources.length === 0) {
      if (emptyState) emptyState.hidden = false;
      return;
    }
    
    if (emptyState) emptyState.hidden = true;
    
    state.objective.resources.forEach((resource, index) => {
      const li = document.createElement('li');
      li.className = 'resource-item';
      
      // Favicon
      const favicon = document.createElement('img');
      favicon.className = 'resource-item__favicon';
      favicon.src = `https://www.google.com/s2/favicons?domain=${new URL(resource.url).hostname}`;
      favicon.alt = '';
      favicon.onerror = () => {
        favicon.style.display = 'none';
      };
      
      // Content
      const content = document.createElement('div');
      content.className = 'resource-item__content';
      
      const title = document.createElement('div');
      title.className = 'resource-item__title';
      title.textContent = resource.label;
      
      const url = document.createElement('div');
      url.className = 'resource-item__url';
      url.textContent = resource.url;
      
      content.append(title, url);
      
      // Actions
      const actions = document.createElement('div');
      actions.className = 'resource-item__actions';
      
      const openBtn = document.createElement('button');
      openBtn.type = 'button';
      openBtn.className = 'btn btn--secondary btn--sm';
      openBtn.innerHTML = '<i class="bi bi-box-arrow-up-right" aria-hidden="true"></i>';
      openBtn.setAttribute('aria-label', 'Abrir recurso');
      openBtn.addEventListener('click', () => {
        window.open(resource.url, '_blank');
      });
      
      const deleteBtn = document.createElement('button');
      deleteBtn.type = 'button';
      deleteBtn.className = 'btn btn--secondary btn--sm';
      deleteBtn.innerHTML = '<i class="bi bi-trash" aria-hidden="true"></i>';
      deleteBtn.setAttribute('aria-label', 'Eliminar recurso');
      deleteBtn.addEventListener('click', () => {
        if (confirm('¿Estás seguro de que quieres eliminar este recurso?')) {
          state.objective.resources.splice(index, 1);
          renderResources();
          addTimelineEvent(`Recurso "${resource.label}" eliminado`, 'resource');
          saveField('resources', state.objective.resources);
        }
      });
      
      actions.append(openBtn, deleteBtn);
      li.append(favicon, content, actions);
      resourceList.appendChild(li);
    });
  }
  
  // Enhanced focus mode
  function initializeFocusMode() {
    const focusBtn = safeQuerySelector('.btn-focus');
    const exitBtn = safeQuerySelector('[data-focus-exit]');
    const overlay = safeQuerySelector('[data-focus-overlay]');
    const main = safeQuerySelector('.objective-page');
    
    if (!focusBtn || !overlay || !main) return;
    
    function toggleFocusMode() {
      const isActive = main.classList.toggle('focus-mode');
      overlay.hidden = !isActive;
      
      const leftPanel = safeQuerySelector('[data-left]');
      const rightPanel = safeQuerySelector('[data-right]');
      
      if (leftPanel) leftPanel.setAttribute('aria-hidden', isActive.toString());
      if (rightPanel) rightPanel.setAttribute('aria-hidden', isActive.toString());
      
      if (isActive) {
        addTimelineEvent('Modo enfoque activado', 'focus');
        document.body.style.overflow = 'hidden';
      } else {
        addTimelineEvent('Modo enfoque desactivado', 'focus');
        document.body.style.overflow = '';
      }
    }
    
    focusBtn.addEventListener('click', toggleFocusMode);
    if (exitBtn) exitBtn.addEventListener('click', toggleFocusMode);
    
    // Close on escape
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && main.classList.contains('focus-mode')) {
        toggleFocusMode();
      }
    });
  }
  
  // Initialize all components
  function initialize() {
    initializeEditableFields();
    initializeResourceModal();
    initializeFocusMode();
    
    // Add milestone button handlers
    const addMilestoneButtons = safeQuerySelectorAll('.add-milestone, .add-milestone-cta');
    addMilestoneButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const milestone = {
          id: generateId(),
          title: 'Nueva Meta',
          weight: 1,
          progress: 0,
          done: false,
          subtasks: [],
          evidences: []
        };
        
        state.objective.milestones.push(milestone);
        renderMilestones();
        updateObjectiveProgress();
        renderStats();
        addTimelineEvent('Nueva meta agregada', 'milestone');
        saveField('milestones', state.objective.milestones);
      });
    });
    
    // Initial render
    renderMilestones();
    renderResources();
    renderStats();
    renderTimeline();
    updateBadges();
    updateProgress();
    updateCountdown();
    
    // Hide skeleton after initial load
    setTimeout(() => {
      const skeleton = safeQuerySelector('[data-skeleton]');
      if (skeleton) skeleton.hidden = true;
    }, 500);
  }
  
  // Start the application
  initialize();
});
