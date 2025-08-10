// Lightweight debounce with global namespace guard and single-init protection
(function() {
window.CRUNEVO = window.CRUNEVO || {};
if (window.CRUNEVO.searchInit) { /* evita re-ejecución */ return; }
window.CRUNEVO.searchInit = true;
window.CRUNEVO.debounce = window.CRUNEVO.debounce || ((fn, ms = 250) => {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), ms);
  };
});
const debounce = window.CRUNEVO.debounce;

// Fallback for legacy templates still using data-action="open-search"
document.addEventListener('click', (e) => {
  const trigger = e.target.closest('[data-action="open-search"]');
  if (!trigger) return;
  e.preventDefault();
  const modalEl = document.getElementById('mobileSearchModal');
  if (modalEl) {
    bootstrap.Modal.getOrCreateInstance(modalEl).show();
  }
});

// ---- DESKTOP ----
(() => {
  const input = document.getElementById('globalSearchInput');
  const menu = document.getElementById('searchDropdown');
  if (!input || !menu) return;

  const open = () => menu.classList.add('show');
  const close = () => {
    menu.classList.remove('show');
    menu.innerHTML = '';
  };
  const goToFullSearch = (q) => (window.location.href = `/search?q=${encodeURIComponent(q)}`);

  const render = (q, data, loading = false) => {
    if (loading) {
      menu.innerHTML = `<div class="search-loading">Buscando “${escapeHtml(q)}”…</div>`;
      open();
      return;
    }
    if (!data || !data.results || data.results.length === 0) {
      menu.innerHTML = `
        <div class="search-empty">No se encontraron resultados</div>
        <div class="search-cta">
          <button class="btn btn-link p-0" data-cta="true">Buscar “${escapeHtml(q)}” en toda la plataforma</button>
        </div>`;
      open();
      return;
    }
    const items = data.results
      .slice(0, 8)
      .map(
        (r) => `
      <a class="search-item dropdown-item" role="option" href="${r.url}">
        <strong>[${escapeHtml(r.type)}]</strong> ${escapeHtml(r.title)}
      </a>`
      )
      .join('');
    menu.innerHTML =
      items +
      `
      <div class="search-cta">
        <button class="btn btn-link p-0" data-cta="true">Ver más resultados de “${escapeHtml(q)}”</button>
      </div>`;
    open();
  };

  const fetchSuggest = debounce(async () => {
    const q = input.value.trim();
    if (!q) {
      close();
      return;
    }
    render(q, null, true);
    try {
      const res = await fetch(`/api/search/suggest?q=${encodeURIComponent(q)}`, {
        headers: { 'X-Requested-With': 'fetch' },
      });
      const data = await res.json();
      render(q, data);
    } catch (e) {
      menu.innerHTML = `<div class="search-empty">Ocurrió un error. Intenta de nuevo.</div>`;
      open();
    }
  }, 250);

  input.addEventListener('input', fetchSuggest);
  input.addEventListener('focus', () => {
    if (input.value.trim()) fetchSuggest();
  });
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const q = input.value.trim();
      if (q) goToFullSearch(q);
    } else if (e.key === 'Escape') {
      close();
    }
  });
  document.addEventListener('click', (e) => {
    if (!menu.contains(e.target) && e.target !== input) close();
  });
  menu.addEventListener('click', (e) => {
    if (e.target && e.target.dataset && e.target.dataset.cta) {
      const q = input.value.trim();
      if (q) goToFullSearch(q);
    }
  });
})();

// ---- MOBILE ----
(() => {
  const modalEl = document.getElementById('mobileSearchModal');
  const input = document.getElementById('mobileSearchInput');
  const list = document.getElementById('mobileSearchResults');
  const submit = document.getElementById('mobileSearchSubmit');
  if (!modalEl || !input || !list || !submit) return;

  const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    const hideOnDesktop = () => {
      if (window.innerWidth >= 768) {
        modal.hide();
      }
    };
    window.addEventListener('resize', hideOnDesktop);
    hideOnDesktop();
  const goToFullSearch = (q) => {
    modal.hide();
    window.location.href = `/search?q=${encodeURIComponent(q)}`;
  };

  const render = (q, data, loading = false) => {
    if (loading) {
      list.innerHTML = `<div class="list-group-item text-muted">Buscando “${escapeHtml(q)}”…</div>`;
      return;
    }
    if (!data || !data.results || data.results.length === 0) {
      list.innerHTML = `<div class="list-group-item text-muted">No se encontraron resultados</div>`;
      return;
    }
    list.innerHTML = data.results
      .slice(0, 8)
      .map(
        (r) => `
      <a class="list-group-item list-group-item-action" role="option" href="${r.url}">
        <strong>[${escapeHtml(r.type)}]</strong> ${escapeHtml(r.title)}
      </a>`
      )
      .join('');
  };

  const fetchSuggest = debounce(async () => {
    const q = input.value.trim();
    if (!q) {
      list.innerHTML = '';
      return;
    }
    render(q, null, true);
    try {
      const res = await fetch(`/api/search/suggest?q=${encodeURIComponent(q)}`, {
        headers: { 'X-Requested-With': 'fetch' },
      });
      const data = await res.json();
      render(q, data);
    } catch (e) {
      list.innerHTML = `<div class="list-group-item text-muted">Ocurrió un error. Intenta de nuevo.</div>`;
    }
  }, 250);

  input.addEventListener('input', fetchSuggest);
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const q = input.value.trim();
      if (q) goToFullSearch(q);
    }
  });
  submit.addEventListener('click', () => {
    const q = input.value.trim();
    if (q) goToFullSearch(q);
  });

    modalEl.addEventListener('shown.bs.modal', () => {
      hideOnDesktop();
      input.focus();
    });
})();

// ---- helpers ----
function escapeHtml(str) {
  return String(str)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

})();

