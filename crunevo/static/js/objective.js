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
      stats: { total_milestones: 0, done_milestones: 0, days_left: 0, streak: 0, velocity_week: 0 }
    }
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
  });

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
  }

  function renderMilestones() {
    milestoneList.innerHTML = '';
    state.objective.milestones.forEach((m, idx) => {
      const li = document.createElement('li');
      li.className = 'milestone-item';
      li.draggable = true;
      li.dataset.id = m.id;

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

      li.append(checkbox, span);

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
    const id = Date.now();
    state.objective.milestones.push({ id, title: 'Nueva Meta', weight: 1, progress: 0, done: false, subtasks: [] });
    renderMilestones();
    saveField('milestones', state.objective.milestones);
  });

  // Resources
  const resourceList = document.querySelector('[data-resource-list]');
  function renderResources() {
    resourceList.innerHTML = '';
    state.objective.resources.forEach(r => {
      const li = document.createElement('li');
      const link = document.createElement('a');
      link.href = r.url;
      link.textContent = r.label;
      link.target = '_blank';
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.textContent = 'Abrir';
      btn.addEventListener('click', () => window.open(r.url, '_blank'));
      li.append(link, btn);
      resourceList.appendChild(li);
    });
  }

  document.querySelector('.add-resource')?.addEventListener('click', () => {
    const label = prompt('Etiqueta');
    const url = prompt('URL');
    if (label && url) {
      state.objective.resources.push({ id: Date.now(), type: 'link', label, url });
      renderResources();
      saveField('resources', state.objective.resources);
    }
  });

  // Stats
  const statsEl = document.querySelector('[data-stats]');
  function renderStats() {
    const s = state.objective.stats;
    s.total_milestones = state.objective.milestones.length;
    s.done_milestones = state.objective.milestones.filter(m => m.done).length;
    if (state.objective.due_at) {
      const due = new Date(state.objective.due_at);
      s.days_left = Math.ceil((due - new Date()) / 86400000);
    }
    const el = statsEl;
    if (el) {
      el.textContent = `Metas: ${s.done_milestones}/${s.total_milestones} | Días restantes: ${s.days_left}`;
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
  document.querySelector('.btn-focus')?.addEventListener('click', () => {
    const active = main.classList.toggle('focus-mode');
    if (overlay) overlay.hidden = !active;
    document.querySelector('[data-left]')?.setAttribute('aria-hidden', active ? 'true' : 'false');
    document.querySelector('[data-right]')?.setAttribute('aria-hidden', active ? 'true' : 'false');
  });

  function updateMotivacion(value) {
    const el = document.querySelector('[data-motivacion]');
    if (el) el.textContent = value;
  }

  renderMilestones();
  renderResources();
  renderStats();
});
