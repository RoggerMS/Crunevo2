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

function applyGalleryOrientation() {
  document.querySelectorAll('.facebook-gallery.two-images').forEach((gal) => {
    const imgs = gal.querySelectorAll('img');
    if (imgs.length !== 2) return;
    const update = () => {
      if (imgs[0].naturalWidth && imgs[1].naturalWidth) {
        const ratio1 = imgs[0].naturalHeight / imgs[0].naturalWidth;
        const ratio2 = imgs[1].naturalHeight / imgs[1].naturalWidth;
        const isVertical1 = ratio1 > 1.2;
        const isVertical2 = ratio2 > 1.2;
        gal.classList.add(isVertical1 && isVertical2 ? 'two-vertical' : 'two-horizontal');
      }
    };
    imgs.forEach((img) => {
      if (img.complete) update();
      else img.addEventListener('load', update, { once: true });
    });
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
        return page
          .render({ canvasContext: canvas.getContext('2d'), viewport })
          .promise;
      })
      .then(() => {
        canvas.classList.remove('d-none');
        canvas.closest('.note-preview')
          ?.querySelector('.loading-shimmer')
          ?.remove();
      })
      .catch(() => {
        const div = document.createElement('div');
        div.className = 'text-center text-muted small';
        div.textContent = 'Vista previa no disponible';
        canvas.replaceWith(div);
      });
  });

  document.querySelectorAll('img.note-img').forEach((img) => {
    if (img.complete) {
      img.classList.remove('d-none');
      img.closest('.note-preview')?.querySelector('.loading-shimmer')?.remove();
    } else {
      img.addEventListener('load', () => {
        img.classList.remove('d-none');
        img.closest('.note-preview')
          ?.querySelector('.loading-shimmer')
          ?.remove();
      });
      img.addEventListener('error', () => {
        img.closest('.note-preview')?.querySelector('.loading-shimmer')?.remove();
      });
    }
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
              <img src="${item.avatar_url || '/static/img/default.png'}" class="rounded-circle mb-2" width="48" height="48" alt="">
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

  document.querySelectorAll('.toast[data-autoshow]').forEach((t) => {
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
  const langSelect = document.getElementById('langSelect');
  if (langSelect) {
    const titleEl = document.getElementById('noteTitle');
    const descEl = document.getElementById('noteDesc');
    const origTitle = titleEl?.textContent;
    const origDesc = descEl?.textContent;
    langSelect.addEventListener('change', (e) => {
      const lang = e.target.value;
      if (lang === 'original') {
        if (titleEl) titleEl.textContent = origTitle;
        if (descEl) descEl.textContent = origDesc;
        return;
      }
      fetch(`/notes/${langSelect.dataset.noteId}/translation/${lang}`)
        .then((r) => r.json())
        .then((data) => {
          if (titleEl && data.title) titleEl.textContent = data.title;
          if (descEl && data.description) descEl.textContent = data.description;
        });
    });
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

  if (typeof initCheckoutShipping === 'function') {
    initCheckoutShipping();
  }

  initCoursesPage();
  initEventList();
  initPrivateChat();
  if (typeof initCareerPage === 'function') {
    initCareerPage();
  }
  if (typeof initPersonalSpace === 'function') {
    initPersonalSpace();
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

  const profileInput = document.getElementById('avatarInput');
  const profilePreview = document.getElementById('avatarPreview');
  const profileSaveBtn = document.getElementById('saveAvatarBtn');
  const triggerBtn = document.getElementById('editAvatarBtn');
  if (triggerBtn && profileInput && profilePreview && profileSaveBtn) {
    triggerBtn.onclick = () => profileInput.click();
    profileInput.onchange = () => {
      const file = profileInput.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
          profilePreview.src = e.target.result;
          profileSaveBtn.classList.remove('d-none');
        };
        reader.readAsDataURL(file);
      }
    };
  }

  const bannerInput = document.getElementById('bannerInput');
  const bannerPreview = document.getElementById('bannerPreview');
  const saveBannerBtn = document.getElementById('saveBannerBtn');
  if (bannerInput && bannerPreview) {
    bannerInput.addEventListener('change', () => {
      const file = bannerInput.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
          bannerPreview.src = e.target.result;
          if (saveBannerBtn) {
            saveBannerBtn.classList.remove('d-none');
          }
        };
        reader.readAsDataURL(file);
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

  document.querySelectorAll('.embed-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const url = btn.dataset.embedUrl;
      if (!url) return;
      const code = `<iframe src="${url}" style="border:none;width:100%;height:500px;"></iframe>`;
      navigator.clipboard.writeText(code).then(() => {
        showToast('Código copiado');
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
    const imgs = container?.querySelectorAll('.gallery-image') || [];
    if (imgs[idx]) {
      openImageModal(imgs[idx].src, idx, postId);
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
  initOnlineCount();

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

    initMissionClaimButtons();
    initGroupMissionClaimButtons();
    highlightNewAchievements();
    initQuickNotes();
    initKeyboardShortcuts();

    initWeatherWidget();
    initStorePage();
    initGlobalChat();
    initChatIA();
    initLauncherMenu();
    removeFloatingOptions();

    applyGalleryOrientation();
    initAchievementsShowMore();

  // Bootstrap collapse handles the mobile menu

});

let notifCount = 0;
function initNotifications() {
  const list = document.getElementById('notifList');
  const badge = document.getElementById('notifBadge');
  const icon = document.getElementById('notifIcon');
  const markAll = document.getElementById('markAllRead');
  const sound = document.getElementById('notifSound');
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
            if (window.CRUNEVO_CONFIG?.soundEnabled && sound) {
              try {
                sound.currentTime = 0;
                sound.play();
              } catch {}
            }
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

function initOnlineCount() {
  const badge = document.getElementById('onlineCountBadge');
  if (!badge || typeof io === 'undefined') return;
  try {
    const socket = io('/online', { transports: ['websocket', 'polling'] });
    socket.on('count', (data) => {
      badge.textContent = data.count;
      badge.classList.remove('tw-hidden');
    });
  } catch (e) {
    console.error('Socket.IO unavailable', e);
  }
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

function claimMission(missionId, button) {
    button.disabled = true;
    button.innerHTML = '<i class="bi bi-hourglass"></i> Reclamando...';

    csrfFetch(`/misiones/reclamar_mision/${missionId}`, { method: 'POST' })
        .then((r) => {
            if (!r.ok) throw new Error('fail');

            const card = button.closest('.mission-card');
            if (card) card.classList.add('bounce-once', 'fade-in');

            const modalEl = document.getElementById('missionClaimModal');
            if (modalEl) {
                const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
                modal.show();
                modalEl.addEventListener('hidden.bs.modal', () => location.reload(), { once: true });
            } else {
                location.reload();
            }

            button.innerHTML = '<i class="bi bi-check-circle"></i> Completada';
            button.className = 'btn btn-success btn-sm';
            button.disabled = true;
        })
        .catch(() => {
            button.disabled = false;
            button.innerHTML = '<i class="bi bi-gift"></i> Reclamar';
            showToast('Error al reclamar la misión', 'error');
        });
}

function claimGroupMission(groupId, button) {
    button.disabled = true;
    button.innerHTML = '<i class="bi bi-hourglass"></i> Reclamando...';

    csrfFetch(`/misiones/reclamar_mision_grupal/${groupId}`, { method: 'POST' })
        .then((r) => {
            if (!r.ok) throw new Error('fail');

            const card = button.closest('.mission-card');
            if (card) card.classList.add('bounce-once', 'fade-in');

            const modalEl = document.getElementById('missionClaimModal');
            if (modalEl) {
                const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
                modal.show();
                modalEl.addEventListener('hidden.bs.modal', () => location.reload(), { once: true });
            } else {
                location.reload();
            }

            button.innerHTML = '<i class="bi bi-check-circle"></i> Completada';
            button.className = 'btn btn-success btn-sm';
            button.disabled = true;
        })
        .catch(() => {
            button.disabled = false;
            button.innerHTML = '<i class="bi bi-gift"></i> Reclamar';
            showToast('Error al reclamar la misión', 'error');
        });
}

function initGroupMissionClaimButtons() {
    document.querySelectorAll('.claim-group-btn').forEach((btn) => {
        btn.addEventListener('click', () => {
            const id = btn.dataset.missionId;
            if (id) claimGroupMission(id, btn);
        });
    });
}

function initMissionClaimButtons() {
    document.querySelectorAll('.claim-btn').forEach((btn) => {
        btn.addEventListener('click', () => {
            const missionId = btn.dataset.missionId;
            if (missionId) claimMission(missionId, btn);
        });
    });
}

function highlightNewAchievements() {
    if (!window.NEW_ACHIEVEMENTS || window.NEW_ACHIEVEMENTS.length === 0) return;
    window.NEW_ACHIEVEMENTS.forEach((a) => {
        const el = document.getElementById(`achievement-${a.code}`);
        if (el) el.classList.add('bounce-once', 'fade-in');
    });
}

function initAchievementsShowMore() {
  document.querySelectorAll('[data-show-more-target]').forEach((section) => {
    const btn = section.parentElement.querySelector('.show-more-btn');
    if (!btn) return;
    const hidden = section.querySelectorAll('.extra');
    if (hidden.length === 0) {
      btn.remove();
      return;
    }
    btn.addEventListener('click', () => {
      hidden.forEach((el) => el.classList.remove('d-none'));
      btn.remove();
    });
  });
}

function initQuickNotes() {
  const textarea = document.getElementById('quickNotesTextarea');
  const saveBtn = document.getElementById('quickNotesSaveBtn');
  if (!textarea || !saveBtn) return;
  textarea.value = localStorage.getItem('quick_notes') || '';
  saveBtn.addEventListener('click', () => {
    localStorage.setItem('quick_notes', textarea.value);
    bootstrap.Modal.getOrCreateInstance(
      document.getElementById('quickNotesModal')
    ).hide();
    showToast('Nota guardada');
  });
}

function initKeyboardShortcuts() {
  document.addEventListener('keydown', (e) => {
    if (!e.shiftKey) return;
    const target = e.target;
    if (
      target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.isContentEditable
    ) {
      return;
    }
    const key = e.key.toUpperCase();
    if (key === 'H' && window.SHORTCUTS?.home) {
      window.location.href = window.SHORTCUTS.home;
    } else if (key === 'N') {
      const modal = document.getElementById('crearPublicacionModal');
      if (modal) {
        e.preventDefault();
        bootstrap.Modal.getOrCreateInstance(modal).show();
      }
    } else if (key === 'Q') {
      const modal = document.getElementById('quickNotesModal');
      if (modal) {
        e.preventDefault();
        bootstrap.Modal.getOrCreateInstance(modal).show();
      }
    }
  });
}

function initLauncherMenu() {
  const launcherBtn = document.querySelector('.launcher-toggle');
  const launcherMenu = document.querySelector('.app-launcher-grid');
  if (!launcherBtn || !launcherMenu) return;
  launcherBtn.addEventListener('click', () => {
    launcherMenu.classList.toggle('show');
  });
  document.addEventListener('click', (e) => {
    if (!launcherBtn.contains(e.target) && !launcherMenu.contains(e.target)) {
      launcherMenu.classList.remove('show');
    }
  });
}

function removeFloatingOptions() {
  const floating =
    document.querySelector('#floating-options-button') ||
    document.querySelector('.toast-launcher');
  if (floating) floating.remove();
}

function initCoursesPage() {
  const filterBtns = document.querySelectorAll('.filter-btn');
  const courseItems = document.querySelectorAll('.course-item');
  if (!filterBtns.length) return;
  filterBtns.forEach((btn) => {
    btn.addEventListener('click', function () {
      filterBtns.forEach((b) => b.classList.remove('active'));
      this.classList.add('active');
      const selected = this.dataset.category;
      courseItems.forEach((item) => {
        const cat = item.dataset.category;
        const premium = item.dataset.premium === 'True';
        const show =
          selected === 'all' ||
          (selected === 'premium' && premium) ||
          selected === cat;
        if (show) {
          item.style.display = 'block';
          item.style.animation = 'fadeInUp 0.5s ease';
        } else {
          item.style.display = 'none';
        }
      });
    });
  });
}

function enrollCourse(courseId) {
  csrfFetch('/courses/enroll', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ course_id: courseId }),
  })
    .then((r) => r.json())
    .then((data) => {
      if (data.success) {
        showToast('¡Te has inscrito exitosamente!', 'success');
        setTimeout(() => location.reload(), 1500);
      } else {
        showToast(data.message || 'Error al inscribirse', 'error');
      }
    })
    .catch(() => showToast('Error de conexión', 'error'));
}

function buyCourse(courseId) {
  window.location.href = `/courses/${courseId}/purchase`;
}

function showPremiumModal() {
  const modalEl = document.getElementById('premiumModal');
  if (modalEl) bootstrap.Modal.getOrCreateInstance(modalEl).show();
}

window.enrollCourse = enrollCourse;
window.buyCourse = buyCourse;
window.showPremiumModal = showPremiumModal;

function initEventList() {
  document.querySelectorAll('[data-tab]').forEach((tab) => {
    tab.addEventListener('click', function (e) {
      e.preventDefault();
      document
        .querySelectorAll('[data-tab]')
        .forEach((t) => t.classList.remove('active'));
      this.classList.add('active');
      document.querySelectorAll('.tab-content').forEach((c) => {
        c.style.display = 'none';
      });
      const target =
        this.dataset.tab === 'upcoming'
          ? 'upcoming-events'
          : this.dataset.tab === 'past'
          ? 'past-events'
          : 'my-events';
      document.getElementById(target).style.display = 'block';
    });
  });
}

async function joinEvent(eventId) {
  const btn = document.querySelector(`button[onclick="joinEvent(${eventId})"]`);
  if (!btn) return;
  const original = btn.innerHTML;
  btn.innerHTML =
    '<div class="spinner-border spinner-border-sm me-1"></div>Inscribiendo...';
  btn.disabled = true;
  try {
    const r = await csrfFetch(`/evento/${eventId}/participar`, { method: 'POST' });
    const data = await r.json();
    if (r.ok) {
      btn.innerHTML = '<i class="bi bi-check-circle me-1"></i>Inscrito';
      btn.classList.add('btn-success');
      const countEl = document.getElementById(`participants-${eventId}`);
      if (countEl) {
        const current = parseInt(countEl.textContent.split(' ')[0]) || 0;
        countEl.textContent = `${current + 1} participantes`;
      }
      showToast('¡Te has inscrito al evento exitosamente! 🎉', 'success');
    } else {
      btn.innerHTML = original;
      btn.disabled = false;
      showToast(data.error || 'Error al inscribirse', 'error');
    }
  } catch {
    btn.innerHTML = original;
    btn.disabled = false;
    showToast('Error de conexión', 'error');
  }
}

window.joinEvent = joinEvent;

function initPrivateChat() {
  const container = document.getElementById('messagesContainer');
  if (!container) return;
  const partnerId = container.dataset.partnerId;
  let lastId = parseInt(container.dataset.lastId || '0', 10);
  const form = document.getElementById('messageForm');
  const input = document.getElementById('messageInput');
  const audioInput = document.getElementById('audioInput');
  const audioBtn = document.getElementById('audioBtn');
  const fileInput = document.getElementById('fileInput');
  const fileBtn = document.getElementById('fileBtn');
  const filePreview = document.getElementById('filePreview');
  container.scrollTop = container.scrollHeight;
  audioBtn?.addEventListener('click', () => audioInput?.click());
  fileBtn?.addEventListener('click', () => fileInput?.click());

  fileInput?.addEventListener('change', () => {
    const f = fileInput.files[0];
    if (!f) {
      filePreview?.classList.add('d-none');
      return;
    }
    const cancel = document.createElement('button');
    cancel.type = 'button';
    cancel.className = 'btn-close';
    cancel.addEventListener('click', () => {
      fileInput.value = '';
      filePreview.classList.add('d-none');
    });
    filePreview.innerHTML = '';
    if (f.type.startsWith('image/')) {
      const img = document.createElement('img');
      const reader = new FileReader();
      reader.onload = (e) => {
        img.src = e.target.result;
      };
      reader.readAsDataURL(f);
      filePreview.appendChild(img);
    } else {
      filePreview.textContent = f.name;
    }
    filePreview.appendChild(cancel);
    filePreview.classList.remove('d-none');
  });
  form?.addEventListener('submit', (e) => {
    e.preventDefault();
    const content = input.value.trim();
    const file = audioInput.files[0];
    const attach = fileInput.files[0];
    if (!content && !file && !attach) return;
    const fd = new FormData();
    fd.append('content', content);
    fd.append('receiver_id', partnerId);
    fd.append('is_global', 'false');
    if (file) fd.append('audio', file);
    if (attach) fd.append('file', attach);
    csrfFetch('/chat/enviar', { method: 'POST', body: fd })
      .then((r) => r.json())
      .then((data) => {
        if (data.status === 'ok') {
          input.value = '';
          audioInput.value = '';
          if (fileInput) fileInput.value = '';
          if (filePreview) filePreview.classList.add('d-none');
          addMessage(data.message, true);
          lastId = data.message.id;
        }
      });
  });
  setInterval(() => {
    fetch(`/chat/mensajes/privados/${partnerId}?since_id=${lastId}`)
      .then((r) => r.json())
      .then((msgs) => {
        msgs.forEach((m) => {
          if (m.sender_id !== window.CURRENT_USER_ID) addMessage(m, false);
          lastId = Math.max(lastId, m.id);
        });
      });
  }, 2000);
  function addMessage(message, sent) {
    const div = document.createElement('div');
    div.className = `message-bubble ${sent ? 'sent' : 'received'}`;
    let body = message.content || '';
    if (message.audio_url) {
      body += `<audio controls src="${message.audio_url}" class="w-100 mt-1"></audio>`;
    }
    if (message.attachment_url) {
      const ext = message.attachment_url.split('.').pop().toLowerCase();
      if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext)) {
        body += `<img src="${message.attachment_url}" class="img-fluid mt-1" alt="" />`;
      } else {
        body += `<a href="${message.attachment_url}" target="_blank" class="d-block mt-1">Archivo adjunto</a>`;
      }
    }
    div.innerHTML = `<div class="bubble-content ${sent ? 'sent' : 'received'}">${body}</div><div class="message-time">${new Date(
      message.timestamp
    ).toLocaleTimeString()}</div>`;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
  }
}

function initWeatherWidget() {
  const widget = document.getElementById('weatherWidget');
  if (!widget) return;
  if (!navigator.geolocation) return;
  navigator.geolocation.getCurrentPosition(async (pos) => {
    const { latitude, longitude } = pos.coords;
    const resp = await fetch(`/dashboard/weather?lat=${latitude}&lon=${longitude}`);
    if (!resp.ok) return;
    const data = await resp.json();
    document.getElementById('weatherCity').textContent = data.city;
    document.getElementById('weatherTemp').textContent = `${data.temp}°C - ${data.desc}`;
    document.getElementById('weatherIcon').src = data.icon;
  });
}

function initStorePage() {
  const grid = document.getElementById('productsGrid');
  if (!grid) return;
  const categoryBtns = document.querySelectorAll('.category-btn');
  const productItems = document.querySelectorAll('.product-item');
  const currencyToggle = document.querySelectorAll('input[name="currency"]');

  categoryBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      categoryBtns.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      const selected = btn.dataset.category;
      productItems.forEach((item) => {
        const cat = item.dataset.category;
        const prem = item.dataset.premium;
        const offer = item.dataset.offer;
        let show = false;
        if (selected === 'all') show = true;
        else if (selected === 'premium' && prem === 'premium') show = true;
        else if (selected === 'offers' && offer === 'offers') show = true;
        else if (selected === cat) show = true;
        item.style.display = show ? 'block' : 'none';
        if (show) item.style.animation = 'fadeInUp 0.5s ease';
      });
    });
  });

  currencyToggle.forEach((radio) => {
    radio.addEventListener('change', () => {
      updatePrices(radio.value);
    });
  });

  function updatePrices(currency) {
    document
      .querySelectorAll('.price-current, .price-original')
      .forEach((el) => {
        const pen = el.dataset.pen;
        const usd = el.dataset.usd;
        el.textContent = currency === 'USD' ? `$ ${usd}` : `S/ ${pen}`;
      });
  }

  window.addToCart = function (productId) {
    csrfFetch(`/store/add/${productId}`, { method: 'POST' })
      .then((r) => r.json())
      .then((data) => {
        if (data.count !== undefined) {
          showToast('Producto agregado al carrito', 'success');
          updateCartBadge(data.count);
        } else {
          showToast('Error al agregar al carrito', 'error');
        }
      })
      .catch(() => showToast('Error de conexión', 'error'));
  };

  window.viewProduct = function (productId) {
    window.location.href = `/store/product/${productId}`;
  };

  window.scrollToOffers = function () {
    document.querySelector('[data-category="offers"]')?.click();
    window.scrollTo({ top: grid.offsetTop - 100, behavior: 'smooth' });
  };

  refreshCartCount();
}

function initGlobalChat() {
  const container = document.getElementById('chatContainer');
  if (!container) return;
  const form = document.getElementById('messageForm');
  const input = document.getElementById('messageInput');
  const audioInput = document.getElementById('audioInput');
  const audioBtn = document.getElementById('audioBtn');
  const fileInput = document.getElementById('fileInput');
  const fileBtn = document.getElementById('fileBtn');
  const filePreview = document.getElementById('filePreview');
  let lastId = parseInt(container.dataset.lastId || '0', 10);
  container.scrollTop = container.scrollHeight;
  audioBtn?.addEventListener('click', () => audioInput?.click());
  fileBtn?.addEventListener('click', () => fileInput?.click());

  fileInput?.addEventListener('change', () => {
    const f = fileInput.files[0];
    if (!f) {
      filePreview?.classList.add('d-none');
      return;
    }
    const cancel = document.createElement('button');
    cancel.type = 'button';
    cancel.className = 'btn-close';
    cancel.addEventListener('click', () => {
      fileInput.value = '';
      filePreview.classList.add('d-none');
    });
    filePreview.innerHTML = '';
    if (f.type.startsWith('image/')) {
      const img = document.createElement('img');
      const reader = new FileReader();
      reader.onload = (e) => {
        img.src = e.target.result;
      };
      reader.readAsDataURL(f);
      filePreview.appendChild(img);
    } else {
      filePreview.textContent = f.name;
    }
    filePreview.appendChild(cancel);
    filePreview.classList.remove('d-none');
  });

  form?.addEventListener('submit', (e) => {
    e.preventDefault();
    const content = input.value.trim();
    const file = audioInput.files[0];
    const attach = fileInput.files[0];
    if (!content && !file && !attach) return;
    const fd = new FormData();
    fd.append('content', content);
    fd.append('is_global', 'true');
    if (file) fd.append('audio', file);
    if (attach) fd.append('file', attach);
    csrfFetch('/chat/enviar', { method: 'POST', body: fd })
      .then((r) => r.json())
      .then((data) => {
        if (data.status === 'ok') {
          input.value = '';
          audioInput.value = '';
          if (fileInput) fileInput.value = '';
          if (filePreview) filePreview.classList.add('d-none');
          addMessage(data.message);
          lastId = data.message.id;
        }
      })
      .catch(console.error);
  });

  setInterval(() => {
    fetch(`/chat/mensajes/global?since_id=${lastId}`)
      .then((r) => r.json())
      .then((msgs) => {
        msgs.forEach((msg) => {
          if (msg.sender_id !== window.CURRENT_USER_ID) addMessage(msg);
          lastId = Math.max(lastId, msg.id);
        });
      })
      .catch(console.error);
  }, 2000);

  function refreshActiveUsers() {
    fetch('/chat/ping', { method: 'POST' });
    fetch('/chat/usuarios/activos')
      .then((r) => r.json())
      .then((list) => {
        const box = document.querySelector('.active-users');
        if (!box) return;
        box.innerHTML = list
          .map(
            (u) => `
          <div class="user-item" onclick="startPrivateChat(${u.id})">
            <div class="position-relative">
              <img src="${u.avatar_url || '/static/img/default.png'}" class="user-avatar" alt="${u.username}">
              <div class="status-indicator"></div>
            </div>
            <div class="flex-grow-1">
              <div class="fw-semibold">${u.username}</div>
              <small class="text-muted">${u.role.charAt(0).toUpperCase() + u.role.slice(1)}</small>
            </div>
          </div>`
          )
          .join('');
      });
  }

  refreshActiveUsers();
  setInterval(refreshActiveUsers, 15000);

  function addMessage(message) {
    const div = document.createElement('div');
    div.className = `message-item ${message.sender_id === window.CURRENT_USER_ID ? 'own' : ''}`;
    let body = message.content || '';
    if (message.audio_url) {
      body += `<audio controls src="${message.audio_url}" class="w-100 mt-1"></audio>`;
    }
    if (message.attachment_url) {
      const ext = message.attachment_url.split('.').pop().toLowerCase();
      if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext)) {
        body += `<img src="${message.attachment_url}" class="img-fluid mt-1" alt="" />`;
      } else {
        body += `<a href="${message.attachment_url}" target="_blank" class="d-block mt-1">Archivo adjunto</a>`;
      }
    }
    div.innerHTML = `
      <img src="${message.sender_avatar || '/static/img/default.png'}" alt="${message.sender_username}" class="user-avatar">
      <div class="message-content">
        <div class="fw-semibold small">${message.sender_username}</div>
        ${body}
        <div class="message-meta">
          ${new Date(message.timestamp).toLocaleTimeString()}
        </div>
      </div>`;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
  }
}

window.startPrivateChat = function (userId) {
  window.location.href = `/chat/privado/${userId}`;
};

function initChatIA() {
  const chatForm = document.getElementById('chat-form');
  if (!chatForm) return;
  if (window.chatIAInitialized) return;
  window.chatIAInitialized = true;
  const messageInput = document.getElementById('message-input');
  const chatMessages = document.getElementById('chat-messages');
  const sendButton = document.getElementById('send-button');
  const typingIndicator = document.getElementById('typing-indicator');
  const iaEnabled = chatMessages.dataset.iaEnabled === 'true';

  const QUICK_RESPONSES = {
    '¿Cómo funciona CRUNEVO?':
      'CRUNEVO es una comunidad educativa donde puedes subir apuntes, ganar Crolars, participar en misiones y mucho más. ¡Explora todas sus secciones desde el menú superior!',
    '¿Cómo ganar Crolars?':
      'Puedes ganar Crolars subiendo apuntes útiles, comentando, ayudando en el foro y completando misiones académicas.',
    'Explícame los clubes académicos':
      'Los clubes académicos son grupos de estudio y colaboración en los que podrás compartir recursos y participar en eventos.',
    '¿Cómo subir apuntes?':
      "Dirígete a la sección 'Apuntes' y haz clic en 'Subir apunte' para compartir tus materiales.",
    '¿Qué es CRUNEVO+?':
      'CRUNEVO+ es la suscripción premium que ofrece beneficios adicionales y contenido exclusivo.',
    '¿Dónde están los cursos?':
      "Los cursos están disponibles en la sección 'Cursos' del menú superior. Allí encontrarás contenidos en video, PDF o enlaces educativos.",
  };

  chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    sendMessage();
  });

  document.querySelectorAll('.quick-question').forEach((button) => {
    button.addEventListener('click', () => {
      const question = button.dataset.question;
      if (!iaEnabled) {
        addMessageToChat(question, 'sent', 'Tú');
        const answer = QUICK_RESPONSES[question];
        if (answer) {
          addMessageToChat(answer, 'received', 'Crunebot');
        }
      } else {
        messageInput.value = question;
        sendMessage();
      }
    });
  });

  function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;
    messageInput.disabled = true;
    sendButton.disabled = true;
    addMessageToChat(message, 'sent', 'Tú');
    messageInput.value = '';

    if (!iaEnabled) {
      const response =
        QUICK_RESPONSES[message] ||
        'Por ahora Crunebot está desactivado. Solo puedes usar las opciones rápidas del menú lateral mientras completamos la configuración.';
      addMessageToChat(response, 'received', 'Crunebot');
      messageInput.disabled = false;
      sendButton.disabled = false;
      messageInput.focus();
      return;
    }

    showTypingIndicator();
    csrfFetch('/ia/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    })
      .then((r) => r.json())
      .then((data) => {
        hideTypingIndicator();
        if (data.answer) {
          addMessageToChat(data.answer, 'received', 'Crunebot');
        } else {
          addMessageToChat('Lo siento, ha ocurrido un error. Inténtalo de nuevo.', 'received', 'Crunebot');
        }
      })
      .catch((error) => {
        hideTypingIndicator();
        console.error('Error:', error);
        addMessageToChat('Error de conexión. Por favor, inténtalo de nuevo.', 'received', 'Crunebot');
      })
      .finally(() => {
        messageInput.disabled = false;
        sendButton.disabled = false;
        messageInput.focus();
      });
  }

  function addMessageToChat(message, type, sender) {
    const container = document.createElement('div');
    container.className = 'message-container mb-4';
    const currentTime = new Date().toLocaleTimeString('es-ES', {
      hour: '2-digit',
      minute: '2-digit',
    });
    const avatar =
      type === 'received'
        ? '/static/img/default.png'
        : chatMessages.dataset.userAvatar || '/static/img/default.png';
    container.innerHTML = `
      <div class="message ${type}">
        <div class="message-content">
          <div class="message-header mb-2">
            <img src="${avatar}" alt="${sender}" class="rounded-circle me-2" width="32" height="32">
            <span class="fw-semibold">${sender}</span>
            <span class="text-muted small ms-2">${currentTime}</span>
          </div>
          <div class="message-bubble ${type}-bubble">
            ${formatMessage(message)}
          </div>
        </div>
      </div>`;
    chatMessages.appendChild(container);
    scrollToBottom();
  }

  function formatMessage(message) {
    return message
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br>');
  }

  function showTypingIndicator() {
    typingIndicator.style.display = 'block';
  }

  function hideTypingIndicator() {
    typingIndicator.style.display = 'none';
  }

  function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  messageInput.focus();
}

window.clearChat = function () {
  if (confirm('¿Estás seguro de que quieres limpiar la conversación?')) {
    const chatMessages = document.getElementById('chat-messages');
    const welcome = chatMessages.firstElementChild;
    chatMessages.innerHTML = '';
    if (welcome) chatMessages.appendChild(welcome);
  }
};

window.saveConversation = function () {
  csrfFetch('/ia/save', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ conversation: 'todo' }),
  })
    .then((r) => r.json())
    .then(() => showToast('Conversación guardada', { delay: 3000 }))
    .catch(() => showToast('Error al guardar la conversación', { delay: 3000 }));
};

window.attachFile = function () {
  alert('Función de adjuntar archivo próximamente disponible');
};
