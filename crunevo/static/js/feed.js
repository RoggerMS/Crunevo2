
// Enhanced Feed JavaScript with modern interactions
class FeedManager {
  constructor() {
    this.currentPage = 1;
    this.isLoading = false;
    this.currentFilter = 'recientes';
    this.posts = new Map();
    this.imageFiles = [];
    this.init();
  }

  init() {
    this.initFeedForm();
    this.initImagePreview();
    this.initFeedFilters();
    this.initInfiniteScroll();
    this.initPostInteractions();
    this.initStreakClaim();
    this.initModals();
    this.initTooltips();
    this.initQuickButtons();
  }

  initFeedForm() {
    const form = document.getElementById('feedForm');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      await this.submitPost(form);
    });

    // Auto-resize textarea
    const textarea = form.querySelector('textarea[name="content"]');
    if (textarea) {
      textarea.addEventListener('input', () => {
        this.autoResizeTextarea(textarea);
        this.updatePostButtonState();
      });
    }

    form.querySelectorAll('input[type="file"]').forEach((inp) => {
      inp.addEventListener('change', () => this.updatePostButtonState());
    });

    this.updatePostButtonState();
  }

  async submitPost(form) {
    const submitBtn = form.querySelector('.feed-submit-btn');
    const submitText = submitBtn.querySelector('.submit-text');
    const spinner = submitBtn.querySelector('.spinner-border');

    try {
      // Show loading state
      this.setButtonLoading(submitBtn, true);

      const imgInput = document.getElementById('feedImageInput');
      const dt = new DataTransfer();
      this.imageFiles.forEach((f) => dt.items.add(f));
      if (imgInput) imgInput.files = dt.files;

      const formData = new FormData(form);
      const response = await this.fetchWithCSRF(form.action || window.location.pathname, {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        this.showToast('¡Publicación creada exitosamente! 🎉', 'success');
        form.reset();
        this.clearImagePreview();
        this.updatePostButtonState();
        // Reload feed or add new post to top
        setTimeout(() => window.location.reload(), 1000);
      } else {
        const errorText = await response.text();
        this.showToast('Error al publicar: ' + errorText, 'error');
      }
    } catch (error) {
      console.error('Error submitting post:', error);
      this.showToast('Error de conexión. Intenta nuevamente.', 'error');
    } finally {
      this.setButtonLoading(submitBtn, false);
      this.updatePostButtonState();
    }
  }

  initImagePreview() {
    const input = document.getElementById('feedImageInput');
    const preview = document.getElementById('previewContainer');

    if (!input || !preview) return;

    input.addEventListener('change', (e) => {
      const files = Array.from(e.target.files);
      files.forEach((file) => {
        if (
          file &&
          file.type.startsWith('image/') &&
          !this.imageFiles.some(
            (f) => f.name === file.name && f.size === file.size && f.lastModified === file.lastModified
          )
        ) {
          this.imageFiles.push(file);
        }
      });
      input.value = '';
      this.updateImagePreviews();
    });
  }

  updateImagePreviews() {
    const container = document.getElementById('previewContainer');
    if (!container) return;
    container.innerHTML = '';
    this.imageFiles.forEach((file, idx) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const div = document.createElement('div');
        div.className = 'preview-item';
        div.innerHTML = `
          <img src="${e.target.result}" class="img-fluid rounded-3 shadow-sm" style="max-height: 150px;">
          <button type="button" class="btn btn-danger btn-sm rounded-circle remove-btn" data-index="${idx}" aria-label="Eliminar imagen">
            <i class="bi bi-x"></i>
          </button>`;
        container.appendChild(div);
        div.querySelector('button').addEventListener('click', (ev) => {
          ev.stopPropagation();
          this.removeImage(idx);
        });
      };
      reader.readAsDataURL(file);
    });
    this.updatePostButtonState();
  }

  removeImage(index) {
    this.imageFiles.splice(index, 1);
    this.updateImagePreviews();
  }

  clearImagePreview() {
    this.imageFiles = [];
    document.getElementById('previewContainer').innerHTML = '';
    document.getElementById('feedImageInput').value = '';
    this.updatePostButtonState();
  }

  updatePostButtonState() {
    const form = document.getElementById('feedForm');
    if (!form) return;

    const content = form.querySelector('textarea[name="content"]').value.trim();
    const fileInputs = form.querySelectorAll('input[type="file"]');
    let hasFile = this.imageFiles.length > 0;

    fileInputs.forEach(inp => {
      if (inp.files && inp.files.length > 0) {
        hasFile = true;
      }
    });

    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) {
      submitBtn.disabled = !(content.length >= 2 || hasFile);
    }
  }

  initFeedFilters() {
    document.querySelectorAll('[data-filter]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        this.setActiveFilter(btn);
        this.loadFilteredFeed(btn.dataset.filter);
      });
    });
  }

  setActiveFilter(activeBtn) {
    document.querySelectorAll('[data-filter]').forEach(btn => {
      btn.classList.remove('btn-primary', 'active');
      btn.classList.add('btn-outline-primary');
    });
    activeBtn.classList.remove('btn-outline-primary');
    activeBtn.classList.add('btn-primary', 'active');
  }

  async loadFilteredFeed(filter) {
    const container = document.getElementById('feedContainer');
    const loading = document.getElementById('feedLoading');

    if (!container) return;

    try {
      this.currentFilter = filter;
      this.currentPage = 1;

      // Show loading state
      container.style.opacity = '0.5';
      if (loading) loading.classList.remove('d-none');

      const response = await fetch(`/feed/api/quickfeed?filter=${filter}`);
      const data = await response.json();

      container.innerHTML = data.html || '';
      this.initPostInteractions();

      this.showToast(`Filtro "${filter}" aplicado`, 'info');
    } catch (error) {
      console.error('Error loading filtered feed:', error);
      this.showToast('Error al cargar contenido', 'error');
    } finally {
      container.style.opacity = '1';
      if (loading) loading.classList.add('d-none');
    }
  }

  initPostInteractions() {
    // Like buttons
    document.querySelectorAll('.like-btn').forEach(btn => {
      btn.addEventListener('click', (e) => this.handleLike(e));
    });

    // Comment buttons
    document.querySelectorAll('.comment-btn').forEach(btn => {
      btn.addEventListener('click', (e) => this.openCommentModal(e));
    });

    // Share buttons
    document.querySelectorAll('.share-btn').forEach(btn => {
      btn.addEventListener('click', (e) => this.openShareModal(e));
    });

    // Save buttons
    document.querySelectorAll('.save-btn').forEach(btn => {
      btn.addEventListener('click', (e) => this.toggleSavePost(e));
    });
  }

  async handleLike(e) {
    e.preventDefault();
    const btn = e.currentTarget;
    const postId = btn.dataset.postId;
    const reaction = btn.dataset.reaction || '👍';

    if (btn.disabled) return;

    try {
      btn.disabled = true;
      
      const formData = new FormData();
      formData.append('reaction', reaction);
      formData.append('csrf_token', this.getCSRFToken());

      const response = await fetch(`/feed/like/${postId}`, {
        method: 'POST',
        body: formData
      });

      const data = await response.json();

      // Update like count
      const countEl = document.querySelector(`#likeCount${postId}`);
      if (countEl) countEl.textContent = data.likes || 0;

      // Update button state
      const icon = btn.querySelector('i');
      if (data.status === 'added') {
        btn.classList.add('active');
        if (icon) icon.classList.add('bi-fire', 'text-danger');
        this.animateButton(btn, '🔥');
      } else if (data.status === 'removed') {
        btn.classList.remove('active');
        if (icon) icon.classList.remove('text-danger');
        if (icon) icon.classList.add('bi-fire');
      }

      this.showToast(data.status === 'added' ? '¡Te gusta esta publicación!' : 'Ya no te gusta esta publicación', 'success');
    } catch (error) {
      console.error('Error handling like:', error);
      this.showToast('Error al procesar reacción', 'error');
    } finally {
      btn.disabled = false;
    }
  }

  openCommentModal(e) {
    const postId = e.currentTarget.dataset.postId;
    const modalEl = document.getElementById('commentModal');
    const bodyEl = document.getElementById('commentModalBody');
    if (!modalEl || !bodyEl) return;
    bodyEl.innerHTML = '<div class="text-center p-3"><div class="spinner-border"></div></div>';
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.show();

    fetch(`/feed/api/post/${postId}`)
      .then((r) => r.json())
      .then((data) => {
        bodyEl.innerHTML = data.html;
        const form = bodyEl.querySelector('#commentForm');
        if (form) {
          form.onsubmit = (ev) => this.submitComment(ev, postId);
        }
        setTimeout(() => {
          const input = bodyEl.querySelector('#commentForm input[name="body"]');
          if (input) input.focus();
        }, 300);
      })
      .catch(() => {
        bodyEl.innerHTML = '<div class="text-center text-muted p-3">Error al cargar publicación</div>';
      });
  }

  async loadComments(postId) {
    const container = document.getElementById('commentsContainer');
    if (!container) return;

    try {
      container.innerHTML = '<div class="text-center p-3"><div class="spinner-border spinner-border-sm"></div></div>';
      
      const response = await fetch(`/feed/api/comments/${postId}`);
      const comments = await response.json();

      container.innerHTML = comments.map(comment => `
        <div class="comment-item d-flex gap-3 mb-3 comment-box">
          <img src="${comment.avatar}" class="rounded-circle" width="32" height="32">
          <div class="flex-grow-1">
            <div class="comment-box p-3 rounded-3">
              <div class="fw-semibold small mb-1">${comment.author}</div>
              <div class="small">${comment.body}</div>
            </div>
            <div class="small text-muted mt-1">${this.timeAgo(comment.timestamp)}</div>
          </div>
        </div>
      `).join('');

      // Setup comment form
      const form = document.getElementById('commentForm');
      if (form) {
        form.onsubmit = (e) => this.submitComment(e, postId);
      }
    } catch (error) {
      console.error('Error loading comments:', error);
      container.innerHTML = '<div class="text-center text-muted p-3">Error al cargar comentarios</div>';
    }
  }

  async submitComment(e, postId) {
    e.preventDefault();
    const form = e.target;
    const input = form.querySelector('input[name="body"]');
    const submitBtn = form.querySelector('button[type="submit"]');

    if (!input.value.trim()) return;

    try {
      submitBtn.disabled = true;
      
      const formData = new FormData();
      formData.append('body', input.value.trim());
      formData.append('csrf_token', this.getCSRFToken());

      const response = await fetch(`/feed/comment/${postId}`, {
        method: 'POST',
        body: formData
      });

      if (response.status === 202) {
        this.showToast('Comentario pendiente de aprobación', 'info');
        input.value = '';
      } else if (response.ok) {
        const comment = await response.json();
        this.addCommentToUI(comment);
        input.value = '';
        this.showToast('Comentario agregado', 'success');
      } else {
        this.showToast('Error al agregar comentario', 'error');
      }
    } catch (error) {
      console.error('Error submitting comment:', error);
      this.showToast('Error de conexión', 'error');
    } finally {
      submitBtn.disabled = false;
    }
  }

  addCommentToUI(comment) {
    const container = document.getElementById('commentsContainer');
    if (!container) return;

    const commentHtml = `
      <div class="comment-item d-flex gap-3 mb-3 comment-box">
        <img src="${comment.avatar || '/static/img/default.png'}" class="rounded-circle" width="32" height="32">
        <div class="flex-grow-1">
          <div class="comment-box p-3 rounded-3">
            <div class="fw-semibold small mb-1">${comment.author}</div>
            <div class="small">${comment.body}</div>
          </div>
          <div class="small text-muted mt-1">ahora</div>
        </div>
      </div>
    `;
    
    container.insertAdjacentHTML('afterbegin', commentHtml);
  }

  openShareModal(e) {
    const shareUrl = e.currentTarget.dataset.shareUrl;
    window.currentShareUrl = shareUrl;

    const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('shareModal'));
    modal.show();
  }

  async toggleSavePost(e) {
    const btn = e.currentTarget;
    const postId = btn.dataset.postId;

    try {
      btn.disabled = true;
      
      const response = await this.fetchWithCSRF(`/feed/save/${postId}`, {
        method: 'POST'
      });

      const data = await response.json();
      
      const icon = btn.querySelector('i');
      if (data.saved) {
        icon.classList.add('bi-bookmark-fill');
        icon.classList.remove('bi-bookmark');
        this.showToast('Publicación guardada', 'success');
      } else {
        icon.classList.remove('bi-bookmark-fill');
        icon.classList.add('bi-bookmark');
        this.showToast('Publicación removida de guardados', 'info');
      }
    } catch (error) {
      console.error('Error toggling save:', error);
      this.showToast('Error al guardar', 'error');
    } finally {
      btn.disabled = false;
    }
  }

  initStreakClaim() {
    const claimBtn = document.getElementById('claimStreakBtn');
    if (!claimBtn) return;

    claimBtn.addEventListener('click', async () => {
      try {
        claimBtn.disabled = true;
        claimBtn.innerHTML = '<div class="spinner-border spinner-border-sm"></div>';

        const response = await this.fetchWithCSRF('/api/reclamar-racha', {
          method: 'POST'
        });

        if (response.ok) {
          const banner = document.getElementById('streakBanner');
          if (banner) {
            banner.style.animation = 'fadeOut 0.5s ease-out forwards';
            setTimeout(() => banner.remove(), 500);
          }
          this.showToast('¡Crolars reclamados! 🎉', 'success');
        } else {
          this.showToast('Error al reclamar racha', 'error');
        }
      } catch (error) {
        console.error('Error claiming streak:', error);
        this.showToast('Error de conexión', 'error');
      }
    });
  }

  initInfiniteScroll() {
    const sentinel = document.getElementById('feedEnd');
    if (!sentinel) return;

    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && !this.isLoading) {
        this.loadMorePosts();
      }
    }, {
      rootMargin: '100px'
    });

    observer.observe(sentinel);
  }

  async loadMorePosts() {
    if (this.isLoading) return;
    this.isLoading = true;

    try {
      this.currentPage++;
      const response = await fetch(`/feed/api/feed?page=${this.currentPage}&categoria=${this.currentFilter}`);
      const items = await response.json();

      if (items.length === 0) {
        const end = document.getElementById('feedEnd');
        if (end) end.style.display = 'none';
        return;
      }

      const container = document.getElementById('feedContainer');
      items.forEach(item => {
        const html = this.renderFeedItem(item);
        if (html) container.insertAdjacentHTML('beforeend', html);
      });

      this.initPostInteractions();
    } catch (error) {
      console.error('Error loading more posts:', error);
      this.showToast('Error al cargar más publicaciones', 'error');
    } finally {
      this.isLoading = false;
    }
  }

  renderFeedItem(item) {
    // Basic rendering - can be expanded based on item type
    if (item.item_type === 'post') {
      return `
        <div class="card mb-4 shadow-sm border-0 rounded-4 post-card">
          <div class="card-body p-4">
            <p>${item.content || ''}</p>
            <small class="text-muted">@${item.author_username}</small>
          </div>
        </div>
      `;
    }
    return '';
  }

  initModals() {
    // Initialize Bootstrap modals
    document.querySelectorAll('.modal').forEach(modalEl => {
      modalEl.addEventListener('hidden.bs.modal', () => {
        // Clean up modal content when closed
        const form = modalEl.querySelector('form');
        if (form) form.reset();
      });
    });
  }

  initTooltips() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(tooltipTriggerEl => {
      return new bootstrap.Tooltip(tooltipTriggerEl);
    });
  }

  initQuickButtons() {
    const modalEl = document.getElementById('crearPublicacionModal');
    const photoBtn = document.getElementById('photoVideoBtn');
    if (!modalEl || !photoBtn) return;
    let openWithImage = false;
    photoBtn.addEventListener('click', () => {
      openWithImage = true;
      bootstrap.Modal.getOrCreateInstance(modalEl).show();
    });
    modalEl.addEventListener('shown.bs.modal', () => {
      if (openWithImage) {
        document.getElementById('feedImageInput')?.click();
        openWithImage = false;
      }
    });
  }

  // Utility methods
  autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
  }

  setButtonLoading(btn, isLoading) {
    const text = btn.querySelector('.submit-text, .btn-text');
    const spinner = btn.querySelector('.spinner-border');

    if (isLoading) {
      btn.disabled = true;
      if (text) text.classList.add('d-none');
      if (spinner) spinner.classList.remove('d-none');
    } else {
      btn.disabled = false;
      if (text) text.classList.remove('d-none');
      if (spinner) spinner.classList.add('d-none');
    }
  }

  animateButton(btn, emoji) {
    const rect = btn.getBoundingClientRect();
    const animEl = document.createElement('div');
    animEl.textContent = emoji;
    animEl.style.cssText = `
      position: fixed;
      left: ${rect.left + rect.width / 2}px;
      top: ${rect.top}px;
      font-size: 1.5rem;
      pointer-events: none;
      z-index: 1000;
      animation: floatUp 1s ease-out forwards;
    `;
    
    document.body.appendChild(animEl);
    setTimeout(() => animEl.remove(), 1000);
  }

  async fetchWithCSRF(url, options = {}) {
    const headers = {
      ...options.headers,
      'X-CSRFToken': this.getCSRFToken()
    };

    return fetch(url, {
      ...options,
      headers
    });
  }

  getCSRFToken() {
    const token = document.querySelector('[name="csrf_token"]');
    return token ? token.value : '';
  }

  timeAgo(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);

    if (diffInSeconds < 60) return 'ahora';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h`;
    return `${Math.floor(diffInSeconds / 86400)}d`;
  }

  showToast(message, type = 'info') {
    const toastContainer = this.getOrCreateToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-bg-${this.getBootstrapColorClass(type)} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
      <div class="d-flex">
        <div class="toast-body fw-semibold">${message}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
      </div>
    `;

    toastContainer.appendChild(toast);

    const bsToast = new bootstrap.Toast(toast, {
      autohide: true,
      delay: type === 'error' ? 5000 : 3000
    });
    
    bsToast.show();

    toast.addEventListener('hidden.bs.toast', () => {
      toast.remove();
    });
  }

  getOrCreateToastContainer() {
    let container = document.getElementById('toastContainer');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toastContainer';
      container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
      container.style.zIndex = '1060';
      document.body.appendChild(container);
    }
    return container;
  }

  getBootstrapColorClass(type) {
    const colorMap = {
      success: 'success',
      error: 'danger',
      warning: 'warning',
      info: 'info'
    };
    return colorMap[type] || 'info';
  }
}

// Global share functions
function shareToWhatsApp() {
  const url = encodeURIComponent(window.currentShareUrl);
  const text = encodeURIComponent('¡Mira esta publicación en CRUNEVO!');
  window.open(`https://wa.me/?text=${text} ${url}`, '_blank');
}

function shareToTwitter() {
  const url = encodeURIComponent(window.currentShareUrl);
  const text = encodeURIComponent('¡Mira esta publicación en CRUNEVO!');
  window.open(`https://twitter.com/intent/tweet?text=${text}&url=${url}`, '_blank');
}

function copyLink() {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(window.currentShareUrl).then(() => {
      feedManager.showToast('¡Enlace copiado al portapapeles!', 'success');
      bootstrap.Modal.getInstance(document.getElementById('shareModal')).hide();
    });
  } else {
    // Fallback for older browsers
    const textArea = document.createElement('textarea');
    textArea.value = window.currentShareUrl;
    document.body.appendChild(textArea);
    textArea.select();
    document.execCommand('copy');
    document.body.removeChild(textArea);
    feedManager.showToast('¡Enlace copiado!', 'success');
    bootstrap.Modal.getInstance(document.getElementById('shareModal')).hide();
  }
}

// Global functions for post actions
function editPost(postId) {
  const card = document.querySelector(`[data-post-id='${postId}']`);
  const textarea = document.querySelector('#editPostForm textarea[name="content"]');
  const select = document.querySelector('#editPostForm select[name="comment_permission"]');
  const form = document.getElementById('editPostForm');
  if (!card || !textarea || !form) return;
  const contentEl = card.querySelector('.post-content p');
  textarea.value = contentEl ? contentEl.textContent.trim() : '';
  if (select) {
    select.value = card.dataset.commentPermission || 'all';
  }
  form.dataset.postId = postId;
  const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('editPostModal'));
  modal.show();
}

function deletePost(postId) {
  if (!confirm('¿Estás seguro de que quieres eliminar esta publicación?')) return;
  feedManager.fetchWithCSRF(`/feed/post/eliminar/${postId}`, { method: 'POST' })
    .then((resp) => {
      if (resp.ok) {
        document.querySelector(`[data-post-id='${postId}']`)?.remove();
        feedManager.showToast('Publicación eliminada', 'success');
      } else {
        feedManager.showToast('Error al eliminar', 'error');
      }
    })
    .catch(() => feedManager.showToast('Error de conexión', 'error'));
}

function reportPost(postId) {
  if (confirm('¿Quieres reportar esta publicación?')) {
    // Implement report functionality
    feedManager.showToast('Publicación reportada', 'info');
  }
}

function copyPostLink(postId) {
  const url = `${window.location.origin}/feed/post/${postId}`;
  if (navigator.clipboard) {
    navigator.clipboard.writeText(url).then(() => {
      feedManager.showToast('¡Enlace copiado!', 'success');
    });
  }
}


// CSS animations
const style = document.createElement('style');
style.textContent = `
  @keyframes floatUp {
    0% {
      transform: translateY(0) scale(1);
      opacity: 1;
    }
    100% {
      transform: translateY(-30px) scale(1.2);
      opacity: 0;
    }
  }
  
  @keyframes fadeOut {
    from { opacity: 1; transform: translateY(0); }
    to { opacity: 0; transform: translateY(-10px); }
  }
`;
document.head.appendChild(style);

// Feed manager initialization handled in main.js
let feedManager;
function initFeedManager() {
  feedManager = new FeedManager();
}
window.initFeedManager = initFeedManager;

let currentImageIndex = 0;
let imageList = [];
let currentPostId = null;
let currentScale = 1;
let modalImageEl;
let postData = null;

function handleModalKeydown(e) {
  if (e.key === 'Escape') {
    closeImageModal();
  } else if (e.key === 'ArrowRight') {
    nextImage();
  } else if (e.key === 'ArrowLeft') {
    prevImage();
  } else if (e.key === '+' || e.key === '=') {
    zoomIn();
  } else if (e.key === '-') {
    zoomOut();
  }
}

function handleWheel(e) {
  e.preventDefault();
  if (e.deltaY < 0) {
    zoomIn();
  } else {
    zoomOut();
  }
}

function applyZoom() {
  const img = document.getElementById('modalImage');
  if (img) {
    img.style.transform = `scale(${currentScale})`;
  }
}

function zoomIn() {
  currentScale += 0.2;
  applyZoom();
}

function zoomOut() {
  currentScale = Math.max(0.2, currentScale - 0.2);
  applyZoom();
}

function resetZoom() {
  currentScale = 1;
  applyZoom();
}

function openImageModal(src, index, postId) {
  if (index === undefined || index === null || isNaN(index)) {
    console.error('Índice inválido para modal:', index);
    return;
  }
  
  // Get image list from data attribute or fallback to DOM search
  const container = document.querySelector(`[data-post-id='${postId}']`);
  if (container && container.dataset.images) {
    try {
      imageList = JSON.parse(container.dataset.images);
    } catch {
      imageList = [];
    }
  }
  if (!imageList.length) {
    const selector = `[data-post-id='${postId}'] .gallery-image`;
    imageList = Array.from(document.querySelectorAll(selector)).map((img) => img.src);
  }
  
  currentImageIndex = index;
  currentPostId = postId;
  currentScale = 1;
  
  // Create or update modal HTML
  let modal = document.getElementById('imageModal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'imageModal';
    modal.className = 'image-modal';
    document.body.appendChild(modal);
  }
  
  modal.innerHTML = `
    <div class="modal-container">
      <div class="modal-image-section">
        <img id="modalImage" src="${src}" alt="Imagen ${index + 1} de ${imageList.length}">
        
        <div class="modal-top-controls">
          <button class="modal-control-btn" onclick="zoomOut()" title="Reducir zoom">
            <i class="bi bi-dash"></i>
          </button>
          <button class="modal-control-btn" onclick="zoomIn()" title="Aumentar zoom">
            <i class="bi bi-plus"></i>
          </button>
          <button class="modal-control-btn" onclick="resetZoom()" title="Tamaño original">
            <i class="bi bi-arrows-fullscreen"></i>
          </button>
          <a href="${src}" target="_blank" class="modal-control-btn" title="Abrir en nueva pestaña">
            <i class="bi bi-box-arrow-up-right"></i>
          </a>
          <button class="modal-control-btn" onclick="closeImageModal()" title="Cerrar">
            <i class="bi bi-x"></i>
          </button>
        </div>
        
        ${imageList.length > 1 ? `
          <button class="modal-nav prev" onclick="prevImage()" title="Imagen anterior">
            <i class="bi bi-chevron-left"></i>
          </button>
          <button class="modal-nav next" onclick="nextImage()" title="Siguiente imagen">
            <i class="bi bi-chevron-right"></i>
          </button>
        ` : ''}
        
        <div class="modal-counter" id="modalCounter">${index + 1} / ${imageList.length}</div>
      </div>
      
      <div class="modal-info-section" id="imageModalInfo">
        <div class="d-flex justify-content-center align-items-center h-100">
          <div class="spinner-border text-primary"></div>
        </div>
      </div>
    </div>
  `;
  
  modalImageEl = modal.querySelector('#modalImage');
  modal.classList.remove('hidden');
  document.body.classList.add('photo-modal-open');
  
  // Load post data for right panel
  loadPostDataForModal(postId);
  
  // Event listeners
  window.addEventListener('keydown', handleModalKeydown);
  modalImageEl.addEventListener('wheel', handleWheel, { passive: false });
  
  // Update URL
  window.history.pushState({ photo: true }, '', `/feed/post/${postId}/photo/${index + 1}`);
}

function loadPostDataForModal(postId) {
  fetch(`/feed/api/post/${postId}`)
    .then(response => response.json())
    .then(data => {
      const infoSection = document.getElementById('imageModalInfo');
      if (infoSection) {
        infoSection.innerHTML = `
          <div class="modal-post-header">
            <img src="${data.author?.avatar_url || '/static/img/default.png'}" alt="Avatar">
            <div class="modal-user-info">
              <h6>${data.author?.username || 'Usuario'}</h6>
              <small class="modal-timestamp">${data.created_at || 'Hace tiempo'}</small>
            </div>
          </div>
          
          ${data.content ? `<div class="modal-post-content">${data.content}</div>` : ''}
          
          <div class="modal-post-actions">
            <button class="modal-action-btn like-btn ${data.user_liked ? 'active' : ''}" data-post-id="${postId}">
              <i class="bi bi-fire${data.user_liked ? '-fill' : ''}"></i>
              Me gusta
            </button>
            <button class="modal-action-btn comment-btn" data-post-id="${postId}">
              <i class="bi bi-chat"></i>
              Comentar
            </button>
            <button class="modal-action-btn share-btn" data-post-id="${postId}">
              <i class="bi bi-share"></i>
              Compartir
            </button>
          </div>
          
          <div class="modal-comments-section">
            ${data.comments ? data.comments.map(comment => `
              <div class="comment-item d-flex gap-3 mb-3">
                <img src="${comment.author?.avatar_url || '/static/img/default.png'}" 
                     class="rounded-circle" width="32" height="32">
                <div class="flex-grow-1">
                  <div class="comment-box p-3 rounded-3">
                    <div class="fw-semibold small mb-1">${comment.author?.username}</div>
                    <div class="small">${comment.body}</div>
                  </div>
                  <div class="small text-muted mt-1">${comment.timestamp || 'Hace tiempo'}</div>
                </div>
              </div>
            `).join('') : '<p class="text-muted text-center">No hay comentarios aún.</p>'}
          </div>
          
          <div class="modal-comment-form">
            <form onsubmit="submitModalComment(event, '${postId}')">
              <div class="input-group">
                <input type="text" class="form-control" placeholder="Escribe un comentario..." required>
                <button type="submit" class="btn btn-primary">Enviar</button>
              </div>
            </form>
          </div>
        `;
        
        // Re-initialize post interactions for modal
        initModalPostInteractions();
      }
    })
    .catch(error => {
      console.error('Error loading post data:', error);
      document.getElementById('imageModalInfo').innerHTML = 
        '<div class="text-center text-muted p-3">Error al cargar información del post</div>';
    });
}

function initModalPostInteractions() {
  // Like button in modal
  const likeBtn = document.querySelector('.modal-action-btn.like-btn');
  if (likeBtn) {
    likeBtn.addEventListener('click', (e) => feedManager.handleLike(e));
  }
  
  // Comment button in modal
  const commentBtn = document.querySelector('.modal-action-btn.comment-btn');
  if (commentBtn) {
    commentBtn.addEventListener('click', () => {
      const input = document.querySelector('.modal-comment-form input');
      if (input) input.focus();
    });
  }
  
  // Share button in modal
  const shareBtn = document.querySelector('.modal-action-btn.share-btn');
  if (shareBtn) {
    shareBtn.addEventListener('click', (e) => feedManager.openShareModal(e));
  }
}

function submitModalComment(event, postId) {
  event.preventDefault();
  const form = event.target;
  const input = form.querySelector('input');
  const body = input.value.trim();
  
  if (!body) return;
  
  const formData = new FormData();
  formData.append('body', body);
  formData.append('csrf_token', feedManager.getCSRFToken());
  
  fetch(`/feed/comment/${postId}`, {
    method: 'POST',
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      input.value = '';
      loadPostDataForModal(postId); // Reload comments
      feedManager.showToast('Comentario agregado', 'success');
    } else {
      feedManager.showToast('Error al agregar comentario', 'error');
    }
  })
  .catch(error => {
    console.error('Error submitting comment:', error);
    feedManager.showToast('Error de conexión', 'error');
  });
}

function closeImageModal() {
  document.getElementById('imageModal').classList.add('hidden');
  document.getElementById('imageModalInfo').innerHTML = '';
  document.body.classList.remove('photo-modal-open');
  window.removeEventListener('keydown', handleModalKeydown);
  if (modalImageEl) {
    modalImageEl.removeEventListener('wheel', handleWheel);
  }
  currentPostId = null;
  window.history.back();
}

function nextImage() {
  currentImageIndex = (currentImageIndex + 1) % imageList.length;
  document.getElementById('modalImage').src = imageList[currentImageIndex];
  const link = document.getElementById('modalImageLink');
  if (link) link.href = imageList[currentImageIndex];
  updateModalCounter();
  if (currentPostId) {
    updateModalRoute(currentPostId, currentImageIndex);
  }
}

function prevImage() {
  currentImageIndex = (currentImageIndex - 1 + imageList.length) % imageList.length;
  document.getElementById('modalImage').src = imageList[currentImageIndex];
  const link = document.getElementById('modalImageLink');
  if (link) link.href = imageList[currentImageIndex];
  updateModalCounter();
  if (currentPostId) {
    updateModalRoute(currentPostId, currentImageIndex);
  }
}

function updateModalRoute(postId, index) {
  const url = `/feed/post/${postId}/photo/${index + 1}`;
  history.replaceState({ photo: true }, '', url);
}

function updateModalCounter() {
  document.getElementById('modalCounter').textContent = `${currentImageIndex + 1} / ${imageList.length}`;
}

function outsideImageClick(ev) {
  if (ev.target.id === 'imageModal') {
    closeImageModal();
  }
}

window.openImageModal = openImageModal;
window.closeImageModal = closeImageModal;
window.nextImage = nextImage;
window.prevImage = prevImage;
window.outsideImageClick = outsideImageClick;
window.zoomIn = zoomIn;
window.zoomOut = zoomOut;
window.resetZoom = resetZoom;
window.editPost = editPost;
window.deletePost = deletePost;
window.reportPost = reportPost;
window.copyPostLink = copyPostLink;

const editPostForm = document.getElementById('editPostForm');
if (editPostForm) {
  editPostForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.currentTarget;
  const postId = form.dataset.postId;
  const content = form.querySelector('textarea[name="content"]').value.trim();
  const permission = form.querySelector('select[name="comment_permission"]').value;

  const formData = new FormData();
  formData.append('content', content);
  formData.append('comment_permission', permission);
  formData.append('csrf_token', feedManager.getCSRFToken());

    try {
      const resp = await feedManager.fetchWithCSRF(`/feed/post/editar/${postId}`, {
        method: 'POST',
        body: formData
      });
      if (resp.ok) {
        const card = document.querySelector(`[data-post-id='${postId}']`);
        const contentEl = card ? card.querySelector('.post-content p') : null;
        if (contentEl) {
          contentEl.textContent = content;
        }
        feedManager.showToast('Publicación actualizada', 'success');
        bootstrap.Modal.getInstance(document.getElementById('editPostModal')).hide();
      } else {
        feedManager.showToast('Error al editar publicación', 'error');
      }
    } catch (error) {
      feedManager.showToast('Error de conexión', 'error');
    }
  });
}
