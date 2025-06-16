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

  const overlayMenu = document.getElementById('mobileOverlayMenu');
  const openBtn = document.getElementById('openMobileMenu');
  const closeBtn = document.getElementById('closeMobileMenu');

  if (openBtn && overlayMenu) {
    openBtn.addEventListener('click', () => {
      overlayMenu.classList.remove('tw-hidden');
      document.body.style.overflow = 'hidden';
    });
  }

  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      overlayMenu.classList.add('tw-hidden');
      document.body.style.overflow = 'auto';
    });
  }

});
