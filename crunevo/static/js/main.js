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

function showToast(message) {
  const box = document.querySelector('.fixed.top-20');
  if (!box) return;
  const div = document.createElement('div');
  div.className = 'tw-rounded tw-bg-[var(--primary)]/10 tw-px-4 tw-py-2 tw-text-[var(--primary)] tw-shadow';
  div.textContent = message;
  box.appendChild(div);
  setTimeout(() => div.remove(), 3000);
}

document.addEventListener('DOMContentLoaded', () => {
  // theme persistence
  const saved = localStorage.getItem('theme');
  if (saved) {
    document.documentElement.dataset.bsTheme = saved;
  }
  const toggle = document.getElementById('themeToggle');
  toggle?.addEventListener('click', () => {
    const html = document.documentElement;
    const next = html.dataset.bsTheme === 'dark' ? 'light' : 'dark';
    html.dataset.bsTheme = next;
    localStorage.setItem('theme', next);
  });

  // load feed on feed page
  if (typeof loadFeed === 'function' && document.getElementById('feed')) {
    loadFeed();
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
            a.className = 'tw-block tw-px-2 tw-py-1 hover:tw-bg-gray-100 dark:hover:tw-bg-gray-700';
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

  // close mobile menu when a link is clicked
  document.querySelectorAll('.navbar-crunevo .navbar-nav .nav-link').forEach((el) => {
    el.addEventListener('click', () => {
      const collapse = document.getElementById('navbarNav');
      const bsCollapse = bootstrap.Collapse.getInstance(collapse);
      if (bsCollapse) bsCollapse.hide();
    });
  });

  const collapse = document.getElementById('navbarNav');
  if (collapse) {
    collapse.addEventListener('shown.bs.collapse', () => {
      document.body.classList.add('tw-overflow-hidden');
      const back = document.createElement('div');
      back.id = 'menuBackdrop';
      back.className = 'tw-fixed tw-inset-0 tw-bg-black/50 tw-z-[1030]';
      back.addEventListener('click', () => {
        const inst = bootstrap.Collapse.getInstance(collapse);
        inst.hide();
      });
      document.body.appendChild(back);
    });
    collapse.addEventListener('hidden.bs.collapse', () => {
      document.body.classList.remove('tw-overflow-hidden');
      document.getElementById('menuBackdrop')?.remove();
    });
  }
});
