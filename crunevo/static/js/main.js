// Main entry point

function getDeviceToken() {
  let t = localStorage.getItem('crunevo_device_token');
  if (!t) {
    t = crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2) + Date.now();
    localStorage.setItem('crunevo_device_token', t);
  }
  return t;
}

function csrfFetch(url, options = {}) {
  const token = document.querySelector('meta[name="csrf-token"]').content;
  const headers = {
    'X-CSRFToken': token,
    'X-Requested-With': 'XMLHttpRequest',
    'X-Device-Token': getDeviceToken(),
    ...(options.headers || {}),
  };
  return fetch(url, { ...options, headers }).then(async (resp) => {
    if (
      resp.ok &&
      resp.headers.get('Content-Type')?.includes('application/json')
    ) {
      try {
        const data = await resp.clone().json();
        if (data.new_achievement) {
          showAchievementPopup(data.new_achievement);
        }
      } catch {
        // ignore parse errors
      }
    }
    return resp;
  });
}

function showToast(message, options = {}) {
  const box = document.querySelector('.toast-container');
  if (!box) return;
  const div = document.createElement('div');
  div.className = 'toast align-items-center text-bg-primary border-0';
  div.role = 'alert';
  div.ariaLive = 'assertive';
  div.ariaAtomic = 'true';
  div.dataset.bsDelay = options.delay || 3000;
  div.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">${message}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>`;
  box.appendChild(div);
  new bootstrap.Toast(div).show();
}

function claimStreak() {
  csrfFetch('/api/reclamar-racha', { method: 'POST' })
    .then((r) => r.json())
    .then((data) => {
      if (data.success) {
        showToast(`🎉 ¡Día ${data.day}! Has ganado ${data.credits} crolars`);
        const box = document.getElementById('streakBox');
        if (box) box.remove();
        if (typeof updateCreditsDisplay === 'function') {
          updateCreditsDisplay(data.balance);
        }
      } else {
        alert(data.message);
      }
    });
}

function updateCreditsDisplay(balance) {
  document.querySelectorAll('.bi-coin').forEach((icon) => {
    const li = icon.closest('li');
    if (li) li.innerHTML = `<i class="bi bi-coin"></i> ${balance}`;
  });
}

function showReactions(btn) {
  const container = btn.closest('.reaction-container');
  const options = container.querySelector('.reaction-options');
  if (!options) return;
  const current = container.dataset.myReaction;
  if (current) {
    options.querySelectorAll('.reaction-btn').forEach((b) => {
      b.classList.toggle('active', b.dataset.reaction === current);
    });
  }
  options.classList.remove('d-none');
  clearTimeout(options._timeout);
  options._timeout = setTimeout(() => {
    options.classList.add('d-none');
  }, 4000);
}

// Confirmations for important actions
function confirmAction(message, callback) {
  if (confirm(message)) {
    callback();
  }
}

// Show confirmation modals for destructive actions
document.addEventListener('click', (e) => {
  if (e.target.matches('[data-confirm]')) {
    e.preventDefault();
    const message = e.target.dataset.confirm;
    const href = e.target.href || e.target.dataset.href;
    
    if (confirm(message)) {
      if (href) {
        window.location.href = href;
      } else if (e.target.onclick) {
        e.target.onclick();
      }
    }
  }
});

function initReactions() {
  document.querySelectorAll('.reaction-container').forEach((container) => {
    const mainBtn = container.querySelector('.btn-reaction');
    const options = container.querySelector('.reaction-options');
    const span = container.querySelector('.count');
    const countsDiv = container.querySelector('.reaction-counts');
    const postId = container.dataset.postId;
    let currentReaction = container.dataset.myReaction || null;

    let isSending = false;

    function sendReaction(reaction) {
      if (isSending) return;
      isSending = true;
      const mainEmoji = container.querySelector('.main-emoji');
      const prevEmoji = mainEmoji ? mainEmoji.textContent : '🔥';
      const prevLikes = span ? parseInt(span.textContent) || 0 : 0;

      const prevReaction = currentReaction;
      let predictedLikes = prevLikes;
      if (currentReaction === reaction) {
        predictedLikes = Math.max(prevLikes - 1, 0);
        currentReaction = null;
      } else if (currentReaction === null) {
        predictedLikes = prevLikes + 1;
        currentReaction = reaction;
      } else {
        currentReaction = reaction;
      }

      if (span) span.textContent = predictedLikes;
      if (mainEmoji) mainEmoji.textContent = reaction;
      mainBtn.classList.add('reaction-active');
      setTimeout(() => mainBtn.classList.remove('reaction-active'), 200);

      const data = new URLSearchParams();
      data.set('reaction', reaction);
      csrfFetch(`/like/${postId}`, { method: 'POST', body: data })
        .then((r) => r.json())
        .then((d) => {
          if (span) span.textContent = d.likes;
          const entries = Object.entries(d.counts).sort((a, b) => b[1] - a[1]);
          if (countsDiv) {
            countsDiv.innerHTML = entries.map(([e, c]) => `${e} ${c}`).join(' ');
          }
          if (mainEmoji) {
            mainEmoji.textContent = entries.length ? entries[0][0] : '🔥';
          }
          if (d.status === 'removed') {
            currentReaction = null;
          } else {
            currentReaction = reaction;
          }
          container.dataset.myReaction = currentReaction || '';
        })
        .catch(() => {
          if (mainEmoji) mainEmoji.textContent = prevEmoji;
          if (span) span.textContent = prevLikes;
          showToast('No se pudo registrar tu reacción. Intenta nuevamente.');
          currentReaction = prevReaction;
        })
        .finally(() => {
          isSending = false;
        });
    }

    let pressTimer;
    let longPress = false;
    let moved = false;
    let pressing = false;
    let startX = 0;
    let startY = 0;

    function startPress(e) {
      e.preventDefault();
      moved = false;
      longPress = false;
      pressing = true;
      const t = e.touches ? e.touches[0] : e;
      startX = t.clientX;
      startY = t.clientY;
      pressTimer = setTimeout(() => {
        longPress = true;
        showReactions(mainBtn);
      }, 600);
    }

    function movePress(e) {
      if (!pressing) return;
      const t = e.touches ? e.touches[0] : e;
      const dx = Math.abs(t.clientX - startX);
      const dy = Math.abs(t.clientY - startY);
      if (dx > 10 || dy > 10) {
        moved = true;
        clearTimeout(pressTimer);
      }
    }

    function endPress() {
      if (!pressing) return;
      pressing = false;
      clearTimeout(pressTimer);
      if (!longPress && !moved) {
        const emoji = container.querySelector('.main-emoji');
        sendReaction(emoji ? emoji.textContent.trim() : '🔥');
      }
    }

    mainBtn.addEventListener('mousedown', startPress);
    mainBtn.addEventListener('touchstart', startPress, { passive: false });
    mainBtn.addEventListener('touchmove', movePress);
    mainBtn.addEventListener('mousemove', movePress);
    mainBtn.addEventListener('wheel', movePress);
    ['mouseup', 'mouseleave'].forEach((ev) => {
      mainBtn.addEventListener(ev, endPress);
    });
    mainBtn.addEventListener('touchend', endPress);
    mainBtn.addEventListener('touchcancel', endPress);

    container.querySelectorAll('.reaction-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        const reaction = btn.dataset.reaction;
        btn.classList.add('reaction-active');
        setTimeout(() => btn.classList.remove('reaction-active'), 200);
        sendReaction(reaction);
        if (options) options.classList.add('d-none');
      });
    });
  });
}

function initPdfPreviews() {
  if (typeof pdfjsLib === 'undefined') return;
  document.querySelectorAll('canvas.pdf-thumb').forEach((canvas) => {
    const url = canvas.dataset.pdf;
    if (!url) return;
    pdfjsLib
      .getDocument(url)
      .promise.then((pdf) => pdf.getPage(1))
      .then((page) => {
        const viewport = page.getViewport({ scale: 0.5 });
        canvas.height = viewport.height;
        canvas.width = viewport.width;
        page.render({ canvasContext: canvas.getContext('2d'), viewport });
      })
      .catch(() => {
        const div = document.createElement('div');
        div.className = 'text-center text-muted small';
        div.textContent = 'Vista previa no disponible';
        canvas.replaceWith(div);
      });
  });
}

function initGlobalSearch() {
  const searchInput = document.getElementById('globalSearchInput');
  const searchResults = document.getElementById('searchResultsContainer');
  const searchLoading = document.getElementById('searchLoading');
  const noResults = document.getElementById('noResults');
  const suggestions = document.getElementById('searchSuggestions');

  if (!searchInput || !searchResults) return;

  let searchTimeout;
  let currentFilter = 'all';

  document.querySelectorAll('.filter-btn').forEach((btn) => {
    btn.addEventListener('click', function () {
      document
        .querySelectorAll('.filter-btn')
        .forEach((b) => b.classList.remove('active'));
      this.classList.add('active');
      currentFilter = this.dataset.filter;
      if (searchInput.value.trim()) {
        performSearch(searchInput.value.trim());
      }
    });
  });

  searchInput.addEventListener('input', function () {
    const query = this.value.trim();
    clearTimeout(searchTimeout);
    if (query.length >= 2) {
      searchTimeout = setTimeout(() => {
        performSearch(query);
        loadSuggestions(query);
      }, 300);
    } else {
      searchResults.innerHTML = '';
      suggestions.style.display = 'none';
    }
  });

  document.addEventListener('click', function (e) {
    if (!suggestions.contains(e.target) && e.target !== searchInput) {
      suggestions.style.display = 'none';
    }
  });

  document.querySelectorAll('.quick-search-card').forEach((card) => {
    card.addEventListener('click', function () {
      const term = this.querySelector('p').textContent;
      searchInput.value = term;
      performSearch(term);
    });
  });

  async function performSearch(query) {
    if (!query) return;
    searchLoading.style.display = 'block';
    searchResults.innerHTML = '';
    noResults.style.display = 'none';
    try {
      const resp = await fetch(
        `/search/api?q=${encodeURIComponent(query)}&category=${currentFilter}`
      );
      const data = await resp.json();
      searchLoading.style.display = 'none';
      if (data.total === 0) {
        noResults.style.display = 'block';
        return;
      }
      renderResults(data.results);
    } catch (err) {
      console.error('Search error:', err);
      searchLoading.style.display = 'none';
      searchResults.innerHTML =
        '<div class="alert alert-danger">Error al realizar la búsqueda</div>';
    }
  }

  async function loadSuggestions(query) {
    if (query.length < 2) return;
    try {
      const resp = await fetch(
        `/search/suggestions?q=${encodeURIComponent(query)}`
      );
      const data = await resp.json();
      if (data.length > 0) {
        suggestions.innerHTML = data
          .map(
            (item) =>
              `<div class="dropdown-item" onclick="selectSuggestion('${item.text}')">
                 <i class="${item.icon} me-2"></i>${item.text}
                 <small class="text-muted ms-auto">${item.type}</small>
               </div>`
          )
          .join('');
        suggestions.style.display = 'block';
      } else {
        suggestions.style.display = 'none';
      }
    } catch (err) {
      console.error('Suggestions error:', err);
    }
  }

  window.selectSuggestion = function (text) {
    searchInput.value = text;
    suggestions.style.display = 'none';
    performSearch(text);
  };

  window.clearSearch = function () {
    searchInput.value = '';
    searchResults.innerHTML = '';
    noResults.style.display = 'none';
    currentFilter = 'all';
    document.querySelectorAll('.filter-btn').forEach((btn) => {
      btn.classList.toggle('active', btn.dataset.filter === 'all');
    });
  };

  function renderResults(results) {
    let html = '';
    Object.keys(results).forEach((category) => {
      if (results[category].length > 0) {
        html += `<div class="result-category mb-4">
          <h5 class="fw-bold text-capitalize mb-3">
            <i class="bi bi-${getCategoryIcon(category)} me-2"></i>
            ${getCategoryLabel(category)} (${results[category].length})
          </h5>
          <div class="row">`;
        results[category].forEach((item) => {
          html += renderResultItem(item, category);
        });
        html += '</div></div>';
      }
    });
    searchResults.innerHTML = html;
  }

  function renderResultItem(item, category) {
    switch (category) {
      case 'notes':
        return `<div class="col-md-6 col-lg-4 mb-3">
          <div class="card h-100 search-result-item">
            <div class="card-body">
              <h6 class="card-title">${item.title}</h6>
              <p class="card-text small text-muted">${item.content_preview}</p>
              <div class="d-flex justify-content-between align-items-center">
                <small class="text-muted">Por ${item.author.username}</small>
                <a href="${item.url}" class="btn btn-sm btn-outline-primary">Ver</a>
              </div>
            </div>
          </div>
        </div>`;
      case 'users':
        return `<div class="col-md-6 col-lg-4 mb-3">
          <div class="card h-100 search-result-item">
            <div class="card-body text-center">
              <img src="${item.avatar_url || '/static/img/default.png'}" class="rounded-circle mb-2" width="48" height="48">
              <h6 class="card-title">${item.username}</h6>
              <p class="card-text small text-muted">${item.about || 'Sin descripción'}</p>
              <div class="d-flex justify-content-between align-items-center">
                <small class="text-muted">${item.points} pts</small>
                <a href="${item.url}" class="btn btn-sm btn-outline-primary">Ver perfil</a>
              </div>
            </div>
          </div>
        </div>`;
      case 'products':
        return `<div class="col-md-6 col-lg-4 mb-3">
          <div class="card h-100 search-result-item">
            <div class="card-body">
              <h6 class="card-title">${item.name}</h6>
              <p class="card-text small text-muted">${item.description}</p>
              <div class="d-flex justify-content-between align-items-center">
                <span class="fw-bold text-primary">S/ ${item.price}</span>
                <a href="${item.url}" class="btn btn-sm btn-outline-primary">Ver</a>
              </div>
            </div>
          </div>
        </div>`;
      case 'courses':
        return `<div class="col-md-6 col-lg-4 mb-3">
          <div class="card h-100 search-result-item">
            <img src="${item.thumbnail_url || '/static/img/course.png'}" class="card-img-top" alt="thumbnail">
            <div class="card-body">
              <h6 class="card-title">${item.title}</h6>
              <p class="card-text small text-muted">${item.category}</p>
              <div class="d-flex justify-content-between align-items-center">
                <small class="text-muted">por ${item.creator}</small>
                <a href="${item.url}" class="btn btn-sm btn-outline-primary">Ver</a>
              </div>
            </div>
          </div>
        </div>`;
      default:
        return `<div class="col-12 mb-3">
          <div class="card search-result-item">
            <div class="card-body">
              <h6 class="card-title">${item.title || item.name || item.content}</h6>
              <a href="${item.url}" class="btn btn-sm btn-outline-primary">Ver</a>
            </div>
          </div>
        </div>`;
    }
  }

  function getCategoryIcon(category) {
    const icons = {
      notes: 'file-text',
      users: 'people',
      posts: 'chat-square-text',
      products: 'shop',
      courses: 'play-circle',
      chats: 'chat-dots',
      missions: 'trophy',
    };
    return icons[category] || 'grid';
  }

  function getCategoryLabel(category) {
    const labels = {
      notes: 'Apuntes',
      users: 'Usuarios',
      posts: 'Publicaciones',
      products: 'Productos',
      courses: 'Cursos',
      chats: 'Mensajes',
      missions: 'Misiones',
    };
    return labels[category] || category;
  }

  if (searchInput.value.trim()) {
    performSearch(searchInput.value.trim());
  }
}



function updateThemeIcons() {
  const dark = document.documentElement.dataset.bsTheme === 'dark';
  document.querySelectorAll('[data-theme-toggle] i').forEach((icon) => {
    icon.className = 'bi ' + (dark ? 'bi-moon' : 'bi-sun');
  });
}

function initNavbarSearchLegacy() {
  const globalSearch = document.getElementById('globalSearch');
  const searchDropdown = document.getElementById('searchDropdown');
  const searchResults = document.getElementById('searchResults');
  let searchTimeout;

  if (globalSearch) {
    globalSearch.addEventListener('input', () => {
      const query = globalSearch.value.trim();
      clearTimeout(searchTimeout);
      if (query.length >= 2) {
        searchTimeout = setTimeout(() => perform(query), 300);
      } else {
        hide();
      }
    });

    globalSearch.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        const query = globalSearch.value.trim();
        if (query) {
          window.location.href = `/search?q=${encodeURIComponent(query)}`;
        }
      }
    });

    document.addEventListener('click', (e) => {
      if (!globalSearch.contains(e.target) && !searchDropdown.contains(e.target)) {
        hide();
      }
    });
  }

  const mobileSearchInput = document.getElementById('mobileSearchInput');
  const mobileSearchModal = document.getElementById('mobileSearchModal');
  if (mobileSearchInput) {
    mobileSearchInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        performMobileSearch();
      }
    });
    if (mobileSearchModal) {
      mobileSearchModal.addEventListener('shown.bs.modal', () => {
        mobileSearchInput.focus();
      });
    }
  }

  async function perform(query) {
    try {
      const resp = await fetch(`/search/suggestions?q=${encodeURIComponent(query)}`);
      const suggestions = await resp.json();
      display(suggestions, query);
    } catch (err) {
      console.error('Search error:', err);
    }
  }

  function display(items, query) {
    if (!searchDropdown || !searchResults) return;
    if (items.length === 0) {
      searchResults.innerHTML = `
        <div class="dropdown-item-text text-muted">
          <i class="bi bi-search me-2"></i>No se encontraron resultados
        </div>
        <div class="dropdown-divider"></div>
        <a href="/search?q=${encodeURIComponent(query)}" class="dropdown-item">
          <i class="bi bi-arrow-right me-2"></i>Buscar "${query}" en toda la plataforma
        </a>`;
    } else {
      searchResults.innerHTML =
        items
          .map(
            (u) => `
        <a href="${u.url}" class="dropdown-item d-flex align-items-center py-2">
          <i class="${u.icon} me-3 text-muted"></i>
          <div>
            <div>${u.text}</div>
            <small class="text-muted">${u.type}</small>
          </div>
        </a>`
          )
          .join('') +
        `
        <div class="dropdown-divider"></div>
        <a href="/search?q=${encodeURIComponent(query)}" class="dropdown-item text-center">
          <i class="bi bi-search me-2"></i>Ver todos los resultados
        </a>`;
    }
    searchDropdown.style.display = 'block';
  }

  function hide() {
    if (searchDropdown) searchDropdown.style.display = 'none';
  }

  window.performMobileSearch = function () {
    const q = mobileSearchInput ? mobileSearchInput.value.trim() : '';
    if (q) {
      window.location.href = `/search?q=${encodeURIComponent(q)}`;
    }
  };
}

function initAuthPage() {
  const themeBtn = document.getElementById('toggle-theme');
  document.querySelectorAll('.toggle-password').forEach((btn) => {
    btn.addEventListener('click', () => {
      const input = btn.previousElementSibling;
      const hide = input.type === 'text';
      input.type = hide ? 'password' : 'text';
      btn.innerHTML = hide ? '🙈' : '🙊';
      btn.setAttribute('aria-label', hide ? 'Mostrar contraseña' : 'Ocultar contraseña');
    });
  });
  if (!themeBtn) return;
  function setThemeIcon(t) {
    themeBtn.textContent = t === 'dark' ? '🌙' : '☀️';
  }
  const stored = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-bs-theme', stored);
  setThemeIcon(stored);
  themeBtn.addEventListener('click', () => {
    const html = document.documentElement;
    const next = html.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-bs-theme', next);
    localStorage.setItem('theme', next);
    setThemeIcon(next);
  });

  const wrapper = document.querySelector('.login-wrapper');
  if (wrapper) {
    const wait = parseInt(wrapper.dataset.wait || '0', 10);
    if (wait > 0) {
      const el = document.getElementById('loginCountdown');
      if (el) {
        let remaining = wait;
        function tick() {
          const m = Math.floor(remaining / 60);
          const s = remaining % 60;
          el.textContent = ` ${m}:${s.toString().padStart(2, '0')}`;
          if (remaining > 0) remaining--;
        }
        tick();
        setInterval(tick, 1000);
      }
    }
    const frases = [
      'Insp\u00edrate, aprende y deja huella con tus apuntes.',
      'Crunevo une a j\u00f3venes que se esfuerzan cada d\u00eda por construir un futuro mejor.',
      'Aqu\u00ed tu conocimiento vale y se comparte.',
    ];
    let i = 0;
    const fraseEl = document.getElementById('frase-bienvenida');
    if (fraseEl) fraseEl.textContent = frases[0];
    setInterval(() => {
      if (fraseEl) {
        fraseEl.style.opacity = 0;
        setTimeout(() => {
          i = (i + 1) % frases.length;
          fraseEl.textContent = frases[i];
          fraseEl.style.opacity = 1;
        }, 500);
      }
    }, 8000);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const isMobile = window.innerWidth < 768;
  const wasMobile = localStorage.getItem('was_mobile') === 'true';
  if (isMobile !== wasMobile) {
    localStorage.setItem('was_mobile', isMobile.toString());
    location.reload();
    return;
  }
  if (navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 4) {
    document.body.classList.add('no-anim');
  }
  const fixedNav = document.querySelector('.navbar.fixed-top');
  if (fixedNav) {
    document.body.style.paddingTop = fixedNav.offsetHeight + 'px';
  }
  if (window.NEW_ACHIEVEMENTS && window.NEW_ACHIEVEMENTS.length > 0) {
    showAchievementPopup(window.NEW_ACHIEVEMENTS[0]);
  }
  if (sessionStorage.getItem('notifHighlight')) {
    sessionStorage.removeItem('notifHighlight');
    document.body.classList.add('notification-highlight');
    setTimeout(() => document.body.classList.remove('notification-highlight'), 2000);
  }
  // theme persistence
  const saved = localStorage.getItem('theme');
  if (saved) {
    document.documentElement.dataset.bsTheme = saved;
  }
  updateThemeIcons();
  document.querySelectorAll('[data-theme-toggle]').forEach((btn) => {
    new bootstrap.Tooltip(btn);
    btn.addEventListener('click', () => {
      const html = document.documentElement;
      const next = html.dataset.bsTheme === 'dark' ? 'light' : 'dark';
      html.dataset.bsTheme = next;
      localStorage.setItem('theme', next);
      updateThemeIcons();
    });
  });

  document.querySelectorAll('.toast').forEach((t) => {
    new bootstrap.Toast(t).show();
  });

  /* ----------------------------------------------------------------------
   * ACHIEVEMENT POPUP — delegated close handler
   * -------------------------------------------------------------------- */
  document.addEventListener('click', (ev) => {
    const btn = ev.target.closest('#closeAchievementBtn');
    if (btn) {
      ev.preventDefault();
      closeAchievementPopup();
    }
  });




  initPdfPreviews();
  if (typeof initNoteViewer === 'function') {
    initNoteViewer();
  }

  if (typeof initFeedManager === 'function') {
    initFeedManager();
  }
  if (typeof initNotificationManager === 'function') {
    initNotificationManager();
  }
  if (typeof initShareButtons === 'function') {
    initShareButtons();
  }
  if (typeof initChatIA === 'function') {
    initChatIA();
  }

  document.querySelectorAll('.achievement-card').forEach((el) => {
    if (el.title && !bootstrap.Tooltip.getInstance(el)) {
      bootstrap.Tooltip.getOrCreateInstance(el);
    }
  });

  // load feed on feed page
  if (typeof loadFeed === 'function' && document.getElementById('feed')) {
    loadFeed();
    if (typeof setupInfiniteScroll === 'function') {
      setupInfiniteScroll();
    }
  }

  if (typeof initFeedToggle === 'function') {
    initFeedToggle();
  }
  if (typeof initFeedInteractions === 'function') {
    initFeedInteractions();
  }
  if (typeof initReactions === 'function') {
    initReactions();
  }
  if (typeof initQuickFilters === 'function') {
    initQuickFilters();
  }
  if (typeof initFeedSearch === 'function') {
    initFeedSearch();
  }
  initGlobalSearch();
  initNavbarSearchLegacy();
  initAuthPage();
  if (typeof initSettingsPage === 'function') {
    initSettingsPage();
  }

  if (typeof initAdminCharts === 'function') {
    initAdminCharts();
  }

  if (typeof initDataTables === 'function') {
    initDataTables();
  }
  if (typeof initDropdowns === 'function') {
    initDropdowns();
  }

  if (typeof initEmailPreview === 'function') {
    initEmailPreview();
  }

  const avatarInput = document.getElementById('avatarFileInput');
  const avatarPreview = document.getElementById('avatarPreview');
  const avatarUrlInput = document.getElementById('avatarUrlInput');
  if (avatarInput && avatarPreview) {
    avatarInput.addEventListener('change', () => {
      const file = avatarInput.files[0];
      if (file) {
        avatarPreview.src = URL.createObjectURL(file);
        avatarPreview.classList.remove('tw-hidden');
      } else {
        if (!avatarUrlInput || !avatarUrlInput.value) {
          avatarPreview.classList.add('tw-hidden');
        }
      }
    });
  }
  if (avatarUrlInput && avatarPreview) {
    avatarUrlInput.addEventListener('input', () => {
      if (avatarUrlInput.value) {
        avatarPreview.src = avatarUrlInput.value;
        avatarPreview.classList.remove('tw-hidden');
      } else if (!avatarInput || !avatarInput.files[0]) {
        avatarPreview.classList.add('tw-hidden');
      }
    });
  }

  const mainImage = document.getElementById('mainImage');
  if (mainImage) {
    document.querySelectorAll('.product-thumb').forEach((img) => {
      img.addEventListener('click', () => {
        mainImage.src = img.dataset.src || img.src;
      });
    });
  }

  const shareBtn = document.getElementById('shareBtn');
  if (shareBtn) {
    shareBtn.addEventListener('click', () => {
      navigator.clipboard.writeText(window.location.href).then(() => {
        showToast('Enlace copiado');
      });
    });
  }

  document.querySelectorAll('.share-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const url = btn.dataset.shareUrl || window.location.href;
      navigator.clipboard.writeText(url).then(() => {
        showToast('Enlace copiado');
      });
    });
  });

  // Feed interactions are handled by FeedManager in feed.js

  if (window.HAS_STORE) {
    refreshCartCount();
  }

  const photoMatch = window.location.pathname.match(/\/feed\/post\/(\d+)\/photo\/(\d+)/);
  if (photoMatch && typeof openImageModal === 'function') {
    const postId = photoMatch[1];
    const idx = parseInt(photoMatch[2], 10) - 1;
    const container = document.querySelector(`[data-post-id='${postId}']`);
    if (container) {
      const imgs = container.querySelectorAll('.image-thumb img, > img');
      if (imgs[idx]) {
        openImageModal(imgs[idx].src, idx, postId);
      }
    }
  }

  window.addEventListener('popstate', () => {
    if (!window.location.pathname.match(/\/feed\/post\/\d+\/photo\/\d+/)) {
      const modal = document.getElementById('imageModal');
      if (modal && !modal.classList.contains('hidden')) {
        modal.classList.add('hidden');
        document.getElementById('imageModalInfo').innerHTML = '';
      }
    }
  });
  document.querySelectorAll('.add-cart-btn').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const pid = btn.dataset.productId;
      fetch(`/store/add/${pid}`, {
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-Device-Token': getDeviceToken(),
        },
      })
        .then((r) => r.json())
        .then((data) => {
          showToast('Producto agregado');
          updateCartBadge(data.count);
        });
    });
  });

  initNotifications();
  initNotificationFilters();

  // Auto hide navbar on scroll for all viewports
  let lastScrollTop = 0;
  const navbar = document.querySelector('.navbar-crunevo');
  const isMobileUA = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);

  function handleScroll() {
    if (!navbar) return;
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    if (scrollTop > lastScrollTop) {
      navbar.classList.add('navbar-hidden');
    } else {
      navbar.classList.remove('navbar-hidden');
    }
    lastScrollTop = scrollTop <= 0 ? 0 : scrollTop;
  }

  window.addEventListener('scroll', handleScroll);
  if (isMobileUA) {
    window.addEventListener('touchmove', handleScroll, { passive: true });
  }

  // Bootstrap collapse handles the mobile menu

});

let notifCount = 0;
function initNotifications() {
  const list = document.getElementById('notifList');
  const badge = document.getElementById('notifBadge');
  const icon = document.getElementById('notifIcon');
  const markAll = document.getElementById('markAllRead');
  if (!list || !badge) return;

function getNotiInfo(msg) {
  const m = msg.toLowerCase();
  if (m.includes('reaccion'))
    return { icon: 'bi-hand-thumbs-up-fill text-warning', type: 'reaction' };
  if (m.includes('coment'))
    return { icon: 'bi-chat-left-dots-fill text-info', type: 'comment' };
  if (m.includes('reporte'))
    return { icon: 'bi-exclamation-circle-fill text-danger', type: 'report' };
  if (m.includes('logro'))
    return { icon: 'bi-trophy-fill text-purple', type: 'achievement' };
  if (m.includes('seguidor'))
    return { icon: 'bi-person-plus-fill text-success', type: 'follow' };
  return { icon: 'bi-bell-fill text-secondary', type: 'other' };
}

  function timeAgo(ts) {
    const d = new Date(ts);
    const diff = Math.floor((Date.now() - d.getTime()) / 1000);
    if (diff < 60) return 'hace unos segundos';
    const m = Math.floor(diff / 60);
    if (m < 60) return `hace ${m} min`;
    const h = Math.floor(m / 60);
    if (h < 24) return `hace ${h} h`;
    const dday = Math.floor(h / 24);
    if (dday === 1) return 'ayer';
    return `hace ${dday} d`;
  }

  function refresh() {
    fetch('/api/notifications', { headers: { 'X-Device-Token': getDeviceToken() } })
      .then((r) => r.json())
      .then((items) => {
        if (items.length > notifCount) {
          items.slice(0, items.length - notifCount).forEach((n) => {
            showToast(n.message);
          });
        }
        notifCount = items.length;
        badge.classList.toggle('tw-hidden', notifCount === 0);
        if (icon) icon.classList.toggle('text-warning', notifCount > 0);
        list.innerHTML = '';
        items.forEach((n) => {
          const li = document.createElement('li');
          const info = getNotiInfo(n.message);
          const time = timeAgo(n.timestamp);
          li.innerHTML = `<a class="dropdown-item d-flex align-items-start gap-2 noti-item" href="${n.url || '#'}"><i class="${info.icon} me-2"></i><span class="flex-grow-1">${n.message}</span><small class="noti-time text-muted ms-2">${time}</small></a>`;
          const a = li.querySelector('a');
          a.addEventListener('click', () => {
            sessionStorage.setItem('notifHighlight', '1');
          });
          list.appendChild(li);
        });
      });
  }

  refresh();
  setInterval(refresh, 30000);

  if (markAll) {
    markAll.addEventListener('click', (e) => {
      e.preventDefault();
      csrfFetch('/notifications/read_all', { method: 'POST' }).then(refresh);
    });
  }
}

function updateCartBadge(count) {
  document.querySelectorAll('#cartBadge, #cartBadgeDesktop, #mobileCartBadge').forEach((b) => {
    b.textContent = count;
    b.classList.toggle('tw-hidden', count === 0);
  });
}

function refreshCartCount() {
  fetch('/store/api/cart_count', { headers: { 'X-Device-Token': getDeviceToken() } })
    .then((r) => r.json())
    .then((data) => updateCartBadge(data.count));
}

function initNotificationFilters() {
  const group = document.getElementById('notiFilterGroup');
  if (!group) return;
  const buttons = group.querySelectorAll('[data-noti-filter]');
  const cards = document.querySelectorAll('.notification-card');
  buttons.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const filter = btn.dataset.notiFilter;
      buttons.forEach((b) => b.classList.toggle('active', b === btn));
      cards.forEach((c) => {
        c.classList.toggle('tw-hidden', filter !== 'all' && c.dataset.type !== filter);
      });
    });
  });
}

function showAchievementPopup(data) {
  if (!window.NEW_ACHIEVEMENTS || window.NEW_ACHIEVEMENTS.length === 0) return;
  const popup = document.getElementById('achievementPopup');
  if (!popup) return;
  popup.querySelector('#achievementTitle').textContent = data.title || data.code;
  popup.querySelector('.credit-gain').textContent = `+${data.credit_reward || 1} Crolar`;
  popup.classList.remove('tw-hidden', 'd-none');
  const content = popup.querySelector('.popup-content');
  content.classList.remove('animate-fade-out-up');
  content.classList.add('animate-fade-in-down');

  // Mark achievements as shown immediately after displaying
  csrfFetch('/api/achievement-popup/mark-shown', { method: 'POST' }).then((r) => {
    if (r.ok) {
      window.NEW_ACHIEVEMENTS = undefined;
    }
  });

  const closeBtn = popup.querySelector('#closeAchievementBtn');
  if (closeBtn) {
    closeBtn.onclick = () => closeAchievementPopup();
  }
}

function closeAchievementPopup() {
  const popup = document.getElementById('achievementPopup');
  if (!popup) return;
  const content = popup.querySelector('.popup-content');
   content.classList.replace('animate-fade-in-down', 'animate-fade-out-up');
  setTimeout(() => {
    popup.classList.add('tw-hidden', 'd-none');
    popup.removeAttribute('style');
    popup.querySelector('#achievementTitle').textContent = '';
    popup.querySelector('.credit-gain').textContent = '';
  }, 300);
}

window.addEventListener('beforeunload', () => {
  window.NEW_ACHIEVEMENTS = undefined;
  const popup = document.getElementById('achievementPopup');
  if (popup) popup.classList.add('d-none', 'tw-hidden');
});

// Share functionality
function sharePost(postId) {
    const url = `${window.location.origin}/feed/post/${postId}`;
    if (navigator.share) {
        navigator.share({
            title: 'Publicación en CRUNEVO',
            url: url
        });
    } else {
        copyToClipboard(url);
        showToast('Enlace copiado al portapapeles');
    }
}

// Save content functionality
function toggleSave(contentType, contentId, button) {
    fetch('/api/guardar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            content_type: contentType,
            content_id: contentId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const icon = button.querySelector('i');
            const text = button.querySelector('span');

            if (data.saved) {
                icon.className = 'bi bi-bookmark-fill';
                if (text) text.textContent = 'Guardado';
                showToast('Contenido guardado');
            } else {
                icon.className = 'bi bi-bookmark';
                if (text) text.textContent = 'Guardar';
                showToast('Contenido removido de guardados');
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error al guardar contenido', 'error');
    });
}