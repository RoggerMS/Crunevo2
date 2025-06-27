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
  return fetch(url, { ...options, headers });
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



function updateThemeIcons() {
  const dark = document.documentElement.dataset.bsTheme === 'dark';
  document.querySelectorAll('[data-theme-toggle] i').forEach((icon) => {
    icon.className = 'bi ' + (dark ? 'bi-moon' : 'bi-sun');
  });
}

document.addEventListener('DOMContentLoaded', () => {
  if (navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 4) {
    document.body.classList.add('no-anim');
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

  if (window.NEW_ACHIEVEMENTS && window.NEW_ACHIEVEMENTS.length && window.CURRENT_USER_ID) {
    showAchievementPopup(window.NEW_ACHIEVEMENTS[0]);
  }


  initPdfPreviews();
  if (typeof initNoteViewer === 'function') {
    initNoteViewer();
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
  if (typeof initImagePreview === 'function') {
    initImagePreview();
  }
  if (typeof initFeedSearch === 'function') {
    initFeedSearch();
  }

  // simple AJAX search suggestions
  const input = document.getElementById('globalSearchInput');
  const box = document.getElementById('searchSuggestions');
  if (input) {
    input.addEventListener('input', function () {
      const q = this.value.trim();
      if (q.length < 2) {
        box.innerHTML = '';
        return;
      }
      fetch(`/search?q=${encodeURIComponent(q)}`, {
        headers: { 'X-Device-Token': getDeviceToken() },
      })
        .then((r) => r.json())
        .then((data) => {
          box.innerHTML = '';
          data.forEach((item) => {
            const a = document.createElement('a');
            a.className = 'dropdown-item';
            a.href = item.url;
            a.textContent = item.title;
            box.appendChild(a);
          });
        });
    });

    // hide suggestions after blur
    input.addEventListener('blur', function () {
      setTimeout(() => {
        box.innerHTML = '';
      }, 100);
    });
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

  const imgInput = document.getElementById('feedImageInput');
  const previewBox = document.getElementById('previewContainer');
  if (imgInput && previewBox) {
    imgInput.addEventListener('change', () => {
      const file = imgInput.files[0];
      if (file && file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => {
          previewBox.innerHTML = `
            <img src="${e.target.result}" alt="preview" class="img-fluid rounded" style="max-height: 300px;" />
          `;
        };
        reader.readAsDataURL(file);
      } else {
        previewBox.innerHTML = "<p class='text-danger'>Archivo no válido</p>";
      }
    });
  }

  const postForm = document.getElementById('postForm');
  const postBtn = document.getElementById('postSubmitBtn');
  const uploadSpinner = document.getElementById('uploadSpinner');
  if (postForm && postBtn) {
    postForm.addEventListener('submit', () => {
      postBtn.disabled = true;
      postBtn.innerHTML =
        '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Publicando...';
      if (uploadSpinner) {
        uploadSpinner.classList.remove('tw-hidden');
      }
    });
  }

  if (window.HAS_STORE) {
    refreshCartCount();
  }
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
  const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);

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
  if (isMobile) {
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
  const popup = document.getElementById('achievementPopup');
  if (!popup) return;
  popup.querySelector('#achievementTitle').textContent = data.title || data.code;
  popup.querySelector('.credit-gain').textContent = `+${data.credit_reward || 1} Crolar`;
  popup.classList.remove('tw-hidden');
  const content = popup.querySelector('.popup-content');
  content.classList.remove('animate-fade-out-up');
  content.classList.add('animate-fade-in-down');

  const closeBtn = popup.querySelector('#closeAchievementBtn');
  if (closeBtn) {
    closeBtn.onclick = () => closeAchievementPopup();
  }
}

function closeAchievementPopup() {
  const popup = document.getElementById('achievementPopup');
  if (!popup) return;
  const content = popup.querySelector('.popup-content');
  content.classList.remove('animate-fade-in-down');
  content.classList.add('animate-fade-out-up');
  setTimeout(() => {
    popup.classList.add('tw-hidden');
    popup.querySelector('#achievementTitle').textContent = '';
    popup.querySelector('.credit-gain').textContent = '';
    csrfFetch('/api/achievement-popup/mark-shown', { method: 'POST' }).then(() => {
      window.NEW_ACHIEVEMENTS = [];
    });
  }, 300);
}
