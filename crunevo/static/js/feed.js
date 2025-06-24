let page = 1;
const feed = document.getElementById('feed');
const feedCategory = feed ? feed.dataset.categoria : '';
const sentinel = document.getElementById('feedEnd');

async function loadFeed() {
  const resp = await fetch(`/api/feed?page=${page}&categoria=${feedCategory}`);
  const items = await resp.json();
  items.forEach(item => {
    let html = '';
    if (item.item_type === 'apunte') {
      html = renderApunteCard(item);
    } else if (item.item_type === 'post') {
      html = renderPostCard(item);
    } else if (item.item_type === 'logro') {
      html = renderBadgeCard(item);
    } else if (item.item_type === 'movimiento') {
      html = renderMovimientoCard(item);
    } else if (item.item_type === 'evento') {
      html = renderEventoCard(item);
    } else if (item.item_type === 'mensaje') {
      html = renderMensajeCard(item);
    }
    if (html) {
      feed.insertAdjacentHTML('beforeend', html);
    }
  });
  if (items.length < 10 && observer) {
    observer.disconnect();
    sentinel.remove();
  }
  page++;
}

function renderApunteCard(data) {
  const highlight = data.is_highlight ? ' feed-card--highlight' : '';
  return `<div class="feed-card${highlight}">
    <h5>${data.title}</h5>
    <p>${data.summary || ''}</p>
    <small class="text-muted">@${data.author_username} · ${data.downloads} descargas</small>
    <div class="mt-2"><a class="btn btn-sm btn-primary" href="/notes/${data.ref_id}">Ver apunte</a></div>
  </div>`;
}

function renderPostCard(data) {
  const highlight = data.is_highlight ? ' feed-card--highlight' : '';
  let fileHtml = '';
  if (data.file_url) {
    if (data.file_url.endsWith('.pdf')) {
      fileHtml = `<a href="${data.file_url}" target="_blank" class="btn btn-sm btn-outline-primary mb-2">Ver PDF</a>`;
    } else {
      fileHtml = `<img src="${data.file_url}" class="img-fluid rounded mb-2">`;
    }
  }
  return `<div class="feed-card${highlight}">
    <p>${data.content}</p>
    ${fileHtml}
    <small class="text-muted">@${data.author_username}</small>
    <div class="mt-2"><a class="btn btn-sm btn-secondary" href="#comentarios">Comentar</a></div>
  </div>`;
}

function renderBadgeCard(data) {
  const highlight = data.is_highlight ? ' feed-card--highlight' : '';
  return `<div class="feed-card${highlight}">
    <span>🏅 ${data.badge_code} para ${data.username}</span>
  </div>`;
}

function renderMovimientoCard(data) {
  const highlight = data.is_highlight ? ' feed-card--highlight' : '';
  return `<div class="feed-card${highlight}">
    <span>💰 ${data.sender} → ${data.receiver}: ${data.amount}</span>
    <div class="mt-2"><a class="btn btn-sm btn-outline-primary" href="/">Detalle</a></div>
  </div>`;
}

function renderEventoCard(data) {
  const highlight = data.is_highlight ? ' feed-card--highlight' : '';
  return `<div class="feed-card${highlight}">📅 ${data.title || 'Evento'}</div>`;
}

function renderMensajeCard(data) {
  const highlight = data.is_highlight ? ' feed-card--highlight' : '';
  return `<div class="feed-card${highlight}">💬 ${data.text || ''}</div>`;
}

function initFeedInteractions() {
  document.querySelectorAll('.like-form').forEach((form) => {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      const btn = this.querySelector('button');
      btn.disabled = true;
      csrfFetch(this.action, { method: 'POST' })
        .then((r) => r.json())
        .then((data) => {
          const target = document.getElementById(this.dataset.target);
          if (target) target.textContent = data.likes;
          showToast('¡Gracias por tu reacción!');
        })
        .finally(() => {
          btn.disabled = false;
        });
    });
  });

  document.querySelectorAll('.comment-form').forEach((form) => {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      const btn = this.querySelector('button');
      btn.disabled = true;
      const data = new FormData(this);
      csrfFetch(this.action, { method: 'POST', body: data })
        .then((r) => r.json())
        .then((c) => {
          const container = document.getElementById(this.dataset.container);
          if (container) {
            const div = document.createElement('div');
            div.className = 'd-flex mb-3 comment';
            div.innerHTML = `<img src="${this.dataset.avatar}" class="rounded-circle me-2" width="32" height="32" alt="avatar"><div><div class="small text-muted">${this.dataset.username} • ${c.timestamp}</div><div>${c.body}</div></div>`;
            container.prepend(div);
            const emptyMsg = container.querySelector('[data-empty-msg]');
            if (emptyMsg) emptyMsg.remove();
          }
          form.reset();
          showToast('Comentario agregado');
        })
        .finally(() => {
          btn.disabled = false;
        });
    });
  });

  document.querySelectorAll('.save-post-form').forEach((form) => {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const btn = form.querySelector('button');
      btn.disabled = true;
      csrfFetch(form.action, { method: 'POST' })
        .then((r) => r.json())
        .then(() => {
          showToast('Guardado actualizado');
        })
        .finally(() => {
          btn.disabled = false;
        });
    });
  });

  const donateModalEl = document.getElementById('donateModal');
  if (donateModalEl) {
    const donateModal = new bootstrap.Modal(donateModalEl);
    document.querySelectorAll('.donate-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        donateModalEl.querySelector('form').action = `/donate/${btn.dataset.post}`;
        donateModal.show();
      });
    });
  }

  document.querySelectorAll('[data-feed-tab]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.feedTab;
      document.querySelectorAll('.feed-section').forEach((section) => {
        section.classList.toggle('d-none', section.dataset.section !== target);
      });
      document.querySelectorAll('[data-feed-tab]').forEach((tab) => {
        tab.classList.remove('active');
      });
      btn.classList.add('active');
    });
  });
}

function initQuickFilters() {
  const container = document.getElementById('quickFilters');
  const feedBox = document.getElementById('feed');
  if (!container || !feedBox) return;
  container.querySelectorAll('button[data-filter]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const filter = btn.dataset.filter;
      container.querySelectorAll('button[data-filter]').forEach((b) => {
        b.classList.remove('btn-primary', 'active');
        b.classList.add('btn-outline-primary');
      });
      btn.classList.add('btn-primary', 'active');
      btn.classList.remove('btn-outline-primary');

      fetch(`/api/quickfeed?filter=${filter}`)
        .then((r) => r.json())
        .then((data) => {
          feedBox.innerHTML = data.html;
          const countSpan = btn.querySelector('.count');
          if (countSpan) {
            countSpan.textContent = data.count;
            countSpan.classList.toggle('tw-hidden', data.count === 0);
          }
          initFeedInteractions();
        });
    });
  });
}

function initImagePreview() {
  const input = document.getElementById('feedImageInput');
  const preview = document.getElementById('previewContainer');
  if (!input || !preview) return;
  input.addEventListener('change', () => {
    const file = input.files[0];
    if (file && file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        preview.innerHTML = `
          <img src="${e.target.result}" alt="preview" class="img-fluid rounded" style="max-height: 300px;" />
        `;
      };
      reader.readAsDataURL(file);
    } else {
      preview.innerHTML = "<p class='text-danger'>Archivo no válido</p>";
    }
  });
}

let observer;
function setupInfiniteScroll() {
  if (!sentinel) return;
  observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) {
      loadFeed();
    }
  });
  observer.observe(sentinel);
}

function initFeedSearch() {
  const input = document.getElementById('feedSearch');
  const results = document.getElementById('feedSearchResults');
  if (!input || !results) return;
  input.addEventListener('input', () => {
    const q = input.value.trim();
    if (q.length < 2) {
      results.innerHTML = '';
      return;
    }
    fetch(`/feed/search?q=${encodeURIComponent(q)}`)
      .then((r) => r.json())
      .then((data) => {
        results.innerHTML = '';
        data.forEach((p) => {
          const a = document.createElement('a');
          a.className = 'list-group-item list-group-item-action';
          a.href = `/posts/${p.id}`;
          a.textContent = p.content;
          results.appendChild(a);
        });
      });
  });
}

