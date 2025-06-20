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

function initDropdowns(scope = document) {
  scope.querySelectorAll('[data-bs-toggle="dropdown"]').forEach((el) => {
    bootstrap.Dropdown.getOrCreateInstance(el);
    if (el.title) {
      const tip = bootstrap.Tooltip.getOrCreateInstance(el);
      if (!el.dataset.dropdownTooltipBound) {
        el.addEventListener('show.bs.dropdown', () => tip.hide());
        el.dataset.dropdownTooltipBound = 'true';
      }
    }
  });
}

function initDataTables() {
  if (typeof simpleDatatables === 'undefined') return;
  document.querySelectorAll('[data-datatable]').forEach((table) => {
    const dt = new simpleDatatables.DataTable(table);
    const refresh = () => initDropdowns(table.parentElement);
    ['datatable.init', 'datatable.page', 'datatable.update', 'datatable.sort', 'datatable.search'].forEach((e) => dt.on(e, refresh));
    refresh();
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

  // load feed on feed page
  if (typeof loadFeed === 'function' && document.getElementById('feed')) {
    loadFeed();
  }

  if (typeof initFeedToggle === 'function') {
    initFeedToggle();
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

  initDataTables();
  initDropdowns();

  // Bootstrap collapse handles the mobile menu

});
