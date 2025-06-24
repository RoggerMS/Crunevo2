// Main entry point

function csrfFetch(url, options = {}) {
  const token = document.querySelector('meta[name="csrf-token"]').content;
  const headers = {
    'X-CSRFToken': token,
    'X-Requested-With': 'XMLHttpRequest',
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

  initPdfPreviews();

  document.querySelectorAll('.achievement-card').forEach((el) => {
    if (el.title && !bootstrap.Tooltip.getInstance(el)) {
      bootstrap.Tooltip.getOrCreateInstance(el);
    }
  });

  // load feed on feed page
  if (typeof loadFeed === 'function' && document.getElementById('feed')) {
    loadFeed();
  }

  if (typeof initFeedToggle === 'function') {
    initFeedToggle();
  }
  if (typeof initFeedInteractions === 'function') {
    initFeedInteractions();
  }
  if (typeof initQuickFilters === 'function') {
    initQuickFilters();
  }
  if (typeof initImagePreview === 'function') {
    initImagePreview();
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
      fetch(`/search?q=${encodeURIComponent(q)}`)
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
  if (postForm && postBtn) {
    postForm.addEventListener('submit', () => {
      postBtn.disabled = true;
      postBtn.innerHTML =
        '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Publicando...';
    });
  }

  initNotifications();

  // Bootstrap collapse handles the mobile menu

});

let notifCount = 0;
function initNotifications() {
  const list = document.getElementById('notifList');
  const badge = document.getElementById('notifBadge');
  const markAll = document.getElementById('markAllRead');
  if (!list || !badge) return;

  function refresh() {
    fetch('/api/notifications')
      .then((r) => r.json())
      .then((items) => {
        if (items.length > notifCount) {
          items.slice(0, items.length - notifCount).forEach((n) => {
            showToast(n.message);
          });
        }
        notifCount = items.length;
        badge.textContent = notifCount;
        badge.classList.toggle('tw-hidden', notifCount === 0);
        list.innerHTML = '';
        items.forEach((n) => {
          const li = document.createElement('li');
          li.innerHTML = `<a class="dropdown-item fw-bold" href="${n.url || '#'}">${n.message}</a>`;
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
