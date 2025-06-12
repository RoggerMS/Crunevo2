let page = 1;
const feed = document.getElementById('feed');
const loadMore = document.getElementById('loadMore');

async function loadFeed() {
  const resp = await fetch(`/api/feed?page=${page}`);
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
    }
    if (html) {
      feed.insertAdjacentHTML('beforeend', html);
    }
  });
  if (items.length < 10) {
    loadMore.style.display = 'none';
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
  const img = data.image_url ? `<img src="${data.image_url}" class="img-fluid rounded mb-2">` : '';
  return `<div class="feed-card${highlight}">
    <p>${data.content}</p>
    ${img}
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

loadMore.addEventListener('click', loadFeed);
document.addEventListener('DOMContentLoaded', loadFeed);

