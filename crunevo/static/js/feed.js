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
    }
    feed.insertAdjacentHTML('beforeend', html);
  });
  if (items.length < 10) {
    loadMore.style.display = 'none';
  }
  page++;
}

function renderApunteCard(data) {
  return `<div class="feed-card">
    <h5>${data.title}</h5>
    <p>${data.summary || ''}</p>
    <small class="text-muted">@${data.author_username} · ${data.downloads} descargas</small>
  </div>`;
}

function renderPostCard(data) {
  const img = data.image_url ? `<img src="${data.image_url}" class="img-fluid rounded mb-2">` : '';
  return `<div class="feed-card">
    <p>${data.content}</p>
    ${img}
    <small class="text-muted">@${data.author_username}</small>
  </div>`;
}

loadMore.addEventListener('click', loadFeed);
document.addEventListener('DOMContentLoaded', loadFeed);

