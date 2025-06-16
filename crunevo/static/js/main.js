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

  const overlay = document.getElementById('mobileMenuOverlay');
  const panel = document.getElementById('mobileMenuPanel');
  const toggleBtn = document.getElementById('mobileMenuToggle');
  const closeBtn = document.getElementById('closeMobileMenu');
  const navLinks = document.getElementById('navLinks');
  const desktopContainer = document.getElementById('desktopNavContainer');

  window.addEventListener('load', () => {
    if (window.innerWidth >= 992 && navLinks && desktopContainer) {
      desktopContainer.appendChild(navLinks);
      navLinks.classList.remove('tw-flex-col', 'tw-space-y-4', 'tw-hidden');
      navLinks.classList.add('tw-flex', 'tw-flex-row', 'tw-space-x-4');
    }
  });

  function openMenu() {
    if (window.innerWidth >= 992) return;
    if (!overlay || !panel) return;
    overlay.classList.remove('tw-hidden');
    panel.classList.remove('-tw-translate-x-full');
    if (navLinks && panel) {
      panel.appendChild(navLinks);
      navLinks.classList.remove('tw-hidden');
      navLinks.classList.add('tw-flex-col', 'tw-space-y-4');
      navLinks.classList.remove(
        'md:tw-flex',
        'md:tw-flex-row',
        'md:tw-space-x-4',
      );
    }
    document.body.style.overflow = 'hidden';
    toggleBtn?.setAttribute('aria-expanded', 'true');
  }

  function closeMenu() {
    if (!overlay || !panel) return;
    overlay.classList.add('tw-hidden');
    panel.classList.add('-tw-translate-x-full');
    document.body.style.overflow = 'auto';
    toggleBtn?.setAttribute('aria-expanded', 'false');
    if (navLinks && desktopContainer) {
      desktopContainer.appendChild(navLinks);
      navLinks.classList.remove('tw-flex-col', 'tw-space-y-4');
      navLinks.classList.add('md:tw-flex', 'md:tw-flex-row', 'md:tw-space-x-4');
      navLinks.classList.add('tw-hidden');
    }
    const onEnd = () => {
      overlay.classList.add('tw-hidden');
      panel.removeEventListener('transitionend', onEnd);
    };
    panel.addEventListener('transitionend', onEnd);
  }

  toggleBtn?.addEventListener('click', openMenu);
  closeBtn?.addEventListener('click', closeMenu);

  overlay?.addEventListener('click', (e) => {
    if (e.target === overlay) closeMenu();
  });

  document.addEventListener('click', (e) => {
    if (
      overlay &&
      !overlay.classList.contains('tw-hidden') &&
      panel &&
      !panel.contains(e.target) &&
      toggleBtn &&
      !toggleBtn.contains(e.target)
    ) {
      closeMenu();
    }
  });

  window.addEventListener('pageshow', () => {
    closeMenu();
  });

  // Ensure the mobile menu doesn't stay open when resizing to desktop
  window.addEventListener('resize', () => {
    if (window.innerWidth >= 992) {
      closeMenu();
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !overlay?.classList.contains('tw-hidden')) {
      closeMenu();
    }
  });

});
