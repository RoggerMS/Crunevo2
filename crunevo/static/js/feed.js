// CRUNEVO Modern Feed System - Facebook-style functionality
class ModernFeedManager {
  constructor() {
    this.currentPage = 1;
    this.isLoading = false;
    this.currentFilter = 'recientes';
    this.posts = new Map();
    this.imageFiles = [];
    this.currentImageIndex = 0;
    this.imageList = [];
    this.currentPostId = null;
    this.init();
  }

  init() {
    this.initFeedForm();
    this.initImagePreview();
    this.initFeedFilters();
    this.initInfiniteScroll();
    this.initPostInteractions();
    this.initImageModal();
    this.initCommentSystem();
    this.initPostCreation();
    this.initSkeletonLoading();
  }

  // Initialize post creation form
  initPostCreation() {
    const postCreationTrigger = document.querySelector('.post-creation-trigger');
    const postModal = document.getElementById('crearPublicacionModal');

    if (postCreationTrigger && postModal) {
      postCreationTrigger.addEventListener('click', () => {
        const modal = new bootstrap.Modal(postModal);
        modal.show();
      });
    }
  }

  // Initialize skeleton loading
  initSkeletonLoading() {
    this.showSkeletonPosts();

    // Remove skeletons after content loads
    setTimeout(() => {
      this.removeSkeletonPosts();
    }, 1000);
  }

  showSkeletonPosts() {
    const container = document.getElementById('feedContainer');
    if (!container) return;

    const skeletonHTML = `
      <div class="post-skeleton">
        <div style="display: flex; gap: 12px; margin-bottom: 12px;">
          <div class="skeleton-avatar"></div>
          <div style="flex: 1;">
            <div class="skeleton-line short"></div>
            <div class="skeleton-line" style="width: 40%; height: 8px;"></div>
          </div>
        </div>
        <div class="skeleton-line"></div>
        <div class="skeleton-line medium"></div>
        <div class="skeleton-line" style="height: 200px; margin-top: 12px;"></div>
      </div>
    `;

    // Add 3 skeleton posts
    for (let i = 0; i < 3; i++) {
      container.insertAdjacentHTML('afterbegin', skeletonHTML);
    }
  }

  removeSkeletonPosts() {
    document.querySelectorAll('.post-skeleton').forEach(skeleton => {
      skeleton.classList.add('fade-out');
      setTimeout(() => skeleton.remove(), 300);
    });
  }

  // Initialize feed form
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

    // File input handling
    form.querySelectorAll('input[type="file"]').forEach(input => {
      input.addEventListener('change', () => this.updatePostButtonState());
    });

    this.updatePostButtonState();
  }

  // Submit post with modern UI feedback
  async submitPost(form) {
    const submitBtn = form.querySelector('button[type="submit"]');

    try {
      this.setButtonLoading(submitBtn, true);

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

        // Close modal if open
        const modal = bootstrap.Modal.getInstance(document.getElementById('crearPublicacionModal'));
        if (modal) modal.hide();

        // Refresh feed
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
    }
  }

  // Initialize comment system
  initCommentSystem() {
    document.addEventListener('click', (e) => {
      if (e.target.matches('.comment-btn') || e.target.closest('.comment-btn')) {
        const btn = e.target.closest('.comment-btn');
        const postId = btn.dataset.postId;
        this.toggleComments(postId);
      }
    });

    // Handle comment form submissions
    document.addEventListener('submit', (e) => {
      if (e.target.matches('.comment-form')) {
        e.preventDefault();
        const form = e.target;
        const postId = form.dataset.postId;
        this.submitComment(form, postId);
      }
    });

    // Handle comment input changes
    document.addEventListener('input', (e) => {
      if (e.target.matches('.comment-input')) {
        const form = e.target.closest('.comment-form');
        const submitBtn = form.querySelector('.comment-submit-btn');
        submitBtn.disabled = !e.target.value.trim();
      }
    });
  }

  // Toggle comments visibility
  toggleComments(postId) {
    const commentsSection = document.getElementById(`comments-${postId}`);
    if (!commentsSection) return;

    if (commentsSection.style.display === 'none') {
      commentsSection.style.display = 'block';
      commentsSection.classList.add('fade-in');

      // Focus on comment input
      const commentInput = commentsSection.querySelector('.comment-input');
      if (commentInput) {
        setTimeout(() => commentInput.focus(), 100);
      }
    } else {
      commentsSection.classList.add('fade-out');
      setTimeout(() => {
        commentsSection.style.display = 'none';
        commentsSection.classList.remove('fade-out');
      }, 300);
    }
  }

  // Submit comment
  async submitComment(form, postId) {
    const input = form.querySelector('.comment-input');
    const submitBtn = form.querySelector('.comment-submit-btn');
    const body = input.value.trim();

    if (!body) return;

    try {
      submitBtn.disabled = true;

      const formData = new FormData();
      formData.append('body', body);
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
        this.addCommentToUI(comment, postId);
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

  // Add comment to UI
  addCommentToUI(comment, postId) {
    const commentsContainer = document.querySelector(`#comments-${postId} .comments-container`);
    if (!commentsContainer) return;

    const commentHTML = `
      <div class="comment-item fade-in">
        <div class="comment-avatar">
          <img src="${comment.avatar || '/static/img/default.png'}" 
               alt="${comment.author}"
               class="comment-avatar-img">
        </div>
        <div class="comment-content">
          <div class="comment-bubble">
            <div class="comment-author">${comment.author}</div>
            <div class="comment-text">${comment.body}</div>
          </div>
          <div class="comment-meta">
            <span class="comment-time">ahora</span>
            <button class="comment-reply-btn">Responder</button>
          </div>
        </div>
      </div>
    `;

    commentsContainer.insertAdjacentHTML('beforeend', commentHTML);

    // Update comment count
    const commentBtn = document.querySelector(`[data-post-id="${postId}"].comment-btn`);
    if (commentBtn) {
      const countSpan = commentBtn.querySelector('.action-count');
      if (countSpan) {
        const currentCount = parseInt(countSpan.textContent) || 0;
        countSpan.textContent = currentCount + 1;
      }
    }
  }

  // Initialize post interactions
  initPostInteractions() {
    // Like buttons
    document.addEventListener('click', (e) => {
      if (e.target.matches('.like-btn') || e.target.closest('.like-btn')) {
        const btn = e.target.closest('.like-btn');
        this.handleLike(btn);
      }
    });

    // Share buttons
    document.addEventListener('click', (e) => {
      if (e.target.matches('.share-btn') || e.target.closest('.share-btn')) {
        const btn = e.target.closest('.share-btn');
        this.handleShare(btn);
      }
    });

    // Save buttons
    document.addEventListener('click', (e) => {
      if (e.target.matches('.save-btn') || e.target.closest('.save-btn')) {
        const btn = e.target.closest('.save-btn');
        this.handleSave(btn);
      }
    });
  }

  // Handle like button
  async handleLike(btn) {
    const postId = btn.dataset.postId;
    const reaction = btn.dataset.reaction || '🔥';

    if (btn.disabled) return;

    try {
      btn.disabled = true;
      btn.classList.add('like-animation');

      const formData = new FormData();
      formData.append('reaction', reaction);
      formData.append('csrf_token', this.getCSRFToken());

      const response = await fetch(`/feed/like/${postId}`, {
        method: 'POST',
        body: formData
      });

      const data = await response.json();

      // Update like count
      const countSpan = btn.querySelector('.action-count');
      if (countSpan) {
        countSpan.textContent = data.likes || '';
      }

      // Update button state
      const icon = btn.querySelector('i');
      if (data.status === 'added') {
        btn.classList.add('active');
        if (icon) {
          icon.classList.add('bi-fire-fill');
          icon.classList.remove('bi-fire');
        }
        this.showToast(`¡Reaccionaste con ${reaction}!`, 'success');
      } else if (data.status === 'removed') {
        btn.classList.remove('active');
        if (icon) {
          icon.classList.remove('bi-fire-fill');
          icon.classList.add('bi-fire');
        }
        this.showToast('Reacción removida', 'info');
      }

    } catch (error) {
      console.error('Error handling like:', error);
      this.showToast('Error al procesar reacción', 'error');
    } finally {
      btn.disabled = false;
      setTimeout(() => btn.classList.remove('like-animation'), 300);
    }
  }

  // Handle share button
  handleShare(btn) {
    const postId = btn.dataset.postId;
    const shareUrl = `${window.location.origin}/feed/post/${postId}`;
    const shareTitle = 'Publicación en CRUNEVO';
    const shareText = '¡Mira esta publicación en CRUNEVO!';

    // Native share API for mobile
    if (navigator.share && /Mobile|Android|iPhone/i.test(navigator.userAgent)) {
      navigator.share({
        title: shareTitle,
        text: shareText,
        url: shareUrl
      }).catch(console.error);
      return;
    }

    // Desktop: Copy to clipboard
    this.copyToClipboard(shareUrl);
    this.showToast('¡Enlace copiado al portapapeles!', 'success');
  }

  // Handle save button
  async handleSave(btn) {
    const postId = btn.dataset.postId;

    try {
      btn.disabled = true;

      const response = await this.fetchWithCSRF(`/feed/save/${postId}`, {
        method: 'POST'
      });

      const data = await response.json();

      const icon = btn.querySelector('i');
      if (data.saved) {
        btn.classList.add('active');
        if (icon) {
          icon.classList.add('bi-bookmark-fill');
          icon.classList.remove('bi-bookmark');
        }
        this.showToast('Publicación guardada', 'success');
      } else {
        btn.classList.remove('active');
        if (icon) {
          icon.classList.remove('bi-bookmark-fill');
          icon.classList.add('bi-bookmark');
        }
        this.showToast('Publicación removida de guardados', 'info');
      }
    } catch (error) {
      console.error('Error toggling save:', error);
      this.showToast('Error al guardar', 'error');
    } finally {
      btn.disabled = false;
    }
  }

  // Initialize image modal
  initImageModal() {
    // Close modal on escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.currentPostId) {
        this.closeImageModal();
      }
    });

    // Navigate images with arrow keys
    document.addEventListener('keydown', (e) => {
      if (!this.currentPostId) return;

      if (e.key === 'ArrowRight') {
        this.nextImage();
      } else if (e.key === 'ArrowLeft') {
        this.prevImage();
      }
    });
  }

  // Open image modal
  openImageModal(src, index, postId, evt) {
    const container = evt?.currentTarget.closest('.image-gallery-container') || 
                     document.querySelector(`[data-post-id='${postId}'] .image-gallery-container`);

    if (container && container.dataset.images) {
      try {
        this.imageList = JSON.parse(container.dataset.images);
      } catch {
        this.imageList = [src];
      }
    } else {
      this.imageList = [src];
    }

    this.currentImageIndex = index;
    this.currentPostId = postId;

    // Create modal
    this.createImageModal(src, index);

    // Update URL
    window.history.pushState({ photo: true }, '', `/feed/post/${postId}/photo/${index + 1}`);
  }

  // Create image modal
  createImageModal(src, index) {
    const modal = document.createElement('div');
    modal.id = 'imageModal';
    modal.className = 'image-modal';
    modal.innerHTML = `
      <div class="modal-backdrop" onclick="modernFeedManager.closeImageModal()"></div>
      <div class="modal-content">
        <div class="modal-header">
          <span class="modal-counter">${index + 1} / ${this.imageList.length}</span>
          <button class="modal-close" onclick="modernFeedManager.closeImageModal()" aria-label="Cerrar">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>
        <div class="modal-body">
          <img src="${src}" alt="Imagen ${index + 1}" class="modal-image">
          ${this.imageList.length > 1 ? `
            <button class="modal-nav prev" onclick="modernFeedManager.prevImage()" ${index === 0 ? 'disabled' : ''}>
              <i class="bi bi-chevron-left"></i>
            </button>
            <button class="modal-nav next" onclick="modernFeedManager.nextImage()" ${index === this.imageList.length - 1 ? 'disabled' : ''}>
              <i class="bi bi-chevron-right"></i>
            </button>
          ` : ''}
        </div>
      </div>
    `;

    document.body.appendChild(modal);
    document.body.classList.add('modal-open');

    // Fade in animation
    setTimeout(() => modal.classList.add('show'), 10);
  }

  // Close image modal
  closeImageModal() {
    const modal = document.getElementById('imageModal');
    if (modal) {
      modal.classList.remove('show');
      setTimeout(() => {
        modal.remove();
        document.body.classList.remove('modal-open');
      }, 300);
    }

    this.currentPostId = null;
    this.currentImageIndex = 0;
    this.imageList = [];

    // Restore URL
    window.history.back();
  }

  // Navigate to next image
  nextImage() {
    if (this.currentImageIndex < this.imageList.length - 1) {
      this.currentImageIndex++;
      this.updateModalImage();
    }
  }

  // Navigate to previous image
  prevImage() {
    if (this.currentImageIndex > 0) {
      this.currentImageIndex--;
      this.updateModalImage();
    }
  }

  // Update modal image
  updateModalImage() {
    const modal = document.getElementById('imageModal');
    if (!modal) return;

    const img = modal.querySelector('.modal-image');
    const counter = modal.querySelector('.modal-counter');
    const prevBtn = modal.querySelector('.modal-nav.prev');
    const nextBtn = modal.querySelector('.modal-nav.next');

    if (img) {
      img.src = this.imageList[this.currentImageIndex];
      img.alt = `Imagen ${this.currentImageIndex + 1}`;
    }

    if (counter) {
      counter.textContent = `${this.currentImageIndex + 1} / ${this.imageList.length}`;
    }

    if (prevBtn) {
      prevBtn.disabled = this.currentImageIndex === 0;
    }

    if (nextBtn) {
      nextBtn.disabled = this.currentImageIndex === this.imageList.length - 1;
    }

    // Update URL
    if (this.currentPostId) {
      window.history.replaceState({ photo: true }, '', `/feed/post/${this.currentPostId}/photo/${this.currentImageIndex + 1}`);
    }
  }

  // Initialize image preview for post creation
  initImagePreview() {
    const input = document.getElementById('feedImageInput');
    const preview = document.getElementById('previewContainer');

    if (!input || !preview) return;

    input.addEventListener('change', (e) => {
      const files = Array.from(e.target.files);
      files.forEach(file => {
        if (file && file.type.startsWith('image/')) {
          this.imageFiles.push(file);
        }
      });
      input.value = '';
      this.updateImagePreviews();
    });
  }

  // Update image previews
  updateImagePreviews() {
    const container = document.getElementById('previewContainer');
    if (!container) return;

    container.innerHTML = '';
    this.imageFiles.forEach((file, index) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const div = document.createElement('div');
        div.className = 'preview-item';
        div.innerHTML = `
          <img src="${e.target.result}" alt="Vista previa" class="preview-image">
          <button type="button" class="preview-remove" onclick="modernFeedManager.removeImage(${index})">
            <i class="bi bi-x"></i>
          </button>
        `;
        container.appendChild(div);
      };
      reader.readAsDataURL(file);
    });
  }

  // Remove image from preview
  removeImage(index) {
    this.imageFiles.splice(index, 1);
    this.updateImagePreviews();
    this.updatePostButtonState();
  }

  // Clear image preview
  clearImagePreview() {
    this.imageFiles = [];
    const container = document.getElementById('previewContainer');
    if (container) container.innerHTML = '';
    this.updatePostButtonState();
  }

  // Initialize feed filters
  initFeedFilters() {
    document.querySelectorAll('[data-filter]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        this.setActiveFilter(btn);
        this.loadFilteredFeed(btn.dataset.filter);
      });
    });
  }

  // Set active filter
  setActiveFilter(activeBtn) {
    document.querySelectorAll('[data-filter]').forEach(btn => {
      btn.classList.remove('btn-primary', 'active');
      btn.classList.add('btn-outline-primary');
    });
    activeBtn.classList.remove('btn-outline-primary');
    activeBtn.classList.add('btn-primary', 'active');
  }

  // Load filtered feed
  async loadFilteredFeed(filter) {
    const container = document.getElementById('feedContainer');
    if (!container) return;

    try {
      this.currentFilter = filter;
      this.currentPage = 1;

      // Show loading state
      this.showSkeletonPosts();

      const response = await fetch(`/feed/api/quickfeed?filter=${filter}`);
      const data = await response.json();

      // Hide skeletons
      this.removeSkeletonPosts();

      // Update content
      container.innerHTML = data.html || '';

      // Reinitialize interactions
      this.initPostInteractions();
      this.initCommentSystem();

      this.showToast(`Filtro "${filter}" aplicado`, 'info');
    } catch (error) {
      console.error('Error loading filtered feed:', error);
      this.showToast('Error al cargar contenido', 'error');
      this.removeSkeletonPosts();
    }
  }

  // Initialize infinite scroll
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

  // Load more posts
  async loadMorePosts() {
    if (this.isLoading) return;
    this.isLoading = true;

    try {
      this.currentPage++;
      const response = await fetch(`/feed/api/feed?page=${this.currentPage}&categoria=${this.currentFilter}&format=html`);
      const data = await response.json();

      if (!data.html || data.count === 0) {
        const end = document.getElementById('feedEnd');
        if (end) end.style.display = 'none';
        return;
      }

      const container = document.getElementById('feedContainer');
      const temp = document.createElement('div');
      temp.innerHTML = data.html;

      Array.from(temp.children).forEach(el => {
        const postId = el.getAttribute('data-post-id');
        if (postId) {
          const exists = container.querySelector(`[data-post-id="${postId}"]`);
          if (exists) return;
        }
        el.classList.add('fade-in');
        container.appendChild(el);
      });

    } catch (error) {
      console.error('Error loading more posts:', error);
      this.showToast('Error al cargar más publicaciones', 'error');
    } finally {
      this.isLoading = false;
    }
  }

  // Utility methods
  autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
  }

  updatePostButtonState() {
    const form = document.getElementById('feedForm');
    if (!form) return;

    const content = form.querySelector('textarea[name="content"]')?.value.trim() || '';
    const hasImages = this.imageFiles.length > 0;
    const submitBtn = form.querySelector('button[type="submit"]');

    if (submitBtn) {
      submitBtn.disabled = !(content.length >= 2 || hasImages);
    }
  }

  setButtonLoading(btn, isLoading) {
    const text = btn.querySelector('.btn-text, .action-text');
    const spinner = btn.querySelector('.spinner-border');

    if (isLoading) {
      btn.disabled = true;
      if (text) text.textContent = 'Publicando...';
      if (!spinner) {
        btn.insertAdjacentHTML('afterbegin', '<span class="spinner-border spinner-border-sm me-2"></span>');
      }
    } else {
      btn.disabled = false;
      if (text) text.textContent = 'Publicar';
      if (spinner) spinner.remove();
    }
  }

  copyToClipboard(text) {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text);
    } else {
      const textArea = document.createElement('textarea');
      textArea.value = text;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
    }
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

  showToast(message, type = 'info') {
    const toastContainer = this.getOrCreateToastContainer();

    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-bg-${this.getBootstrapColorClass(type)} border-0 show`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
      <div class="d-flex">
        <div class="toast-body fw-semibold">${message}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
      </div>
    `;

    toastContainer.appendChild(toast);

    // Auto-remove after delay
    setTimeout(() => {
      toast.classList.add('fade-out');
      setTimeout(() => toast.remove(), 300);
    }, type === 'error' ? 5000 : 3000);
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

// Global functions for backwards compatibility
function openImageModal(src, index, postId, evt) {
  if (window.modernFeedManager) {
    window.modernFeedManager.openImageModal(src, index, postId, evt);
  }
}

function editPost(postId) {
  const modal = document.getElementById('editPostModal');
  if (modal) {
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
  }
}

function deletePost(postId) {
  if (!confirm('¿Estás seguro de que quieres eliminar esta publicación?')) return;

  fetch(`/feed/post/eliminar/${postId}`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': window.modernFeedManager?.getCSRFToken() || ''
    }
  })
  .then(response => {
    if (response.ok) {
      const postElement = document.querySelector(`[data-post-id="${postId}"]`);
      if (postElement) {
        postElement.classList.add('fade-out');
        setTimeout(() => postElement.remove(), 300);
      }
      window.modernFeedManager?.showToast('Publicación eliminada', 'success');
    } else {
      window.modernFeedManager?.showToast('Error al eliminar', 'error');
    }
  })
  .catch(() => {
    window.modernFeedManager?.showToast('Error de conexión', 'error');
  });
}

function reportPost(postId) {
  if (confirm('¿Quieres reportar esta publicación?')) {
    window.modernFeedManager?.showToast('Publicación reportada', 'info');
  }
}

function copyPostLink(postId) {
  const url = `${window.location.origin}/feed/post/${postId}`;
  if (window.modernFeedManager) {
    window.modernFeedManager.copyToClipboard(url);
    window.modernFeedManager.showToast('¡Enlace copiado!', 'success');
  }
}

function savePost(postId) {
  if (window.modernFeedManager) {
    const btn = document.querySelector(`[data-post-id="${postId}"].save-btn`);
    if (btn) {
      window.modernFeedManager.handleSave(btn);
    }
  }
}

// Initialize the modern feed manager
let modernFeedManager;

function initModernFeedManager() {
  modernFeedManager = new ModernFeedManager();
  window.modernFeedManager = modernFeedManager;
}

// Auto-initialize
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initModernFeedManager);
} else {
  initModernFeedManager();
}

// CSS for image modal
const modalStyles = `
<style>
.image-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1070;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.image-modal.show {
  opacity: 1;
}

.image-modal .modal-backdrop {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: transparent;
}

.image-modal .modal-content {
  position: relative;
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.image-modal .modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  color: white;
}

.image-modal .modal-counter {
  font-size: 14px;
  font-weight: 500;
}

.image-modal .modal-close {
  background: none;
  border: none;
  color: white;
  font-size: 20px;
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  transition: background-color 0.2s;
}

.image-modal .modal-close:hover {
  background: rgba(255, 255, 255, 0.1);
}

.image-modal .modal-body {
  position: relative;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-modal .modal-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.image-modal .modal-nav {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(0, 0, 0, 0.5);
  border: none;
  color: white;
  font-size: 24px;
  cursor: pointer;
  padding: 12px 16px;
  border-radius: 50%;
  transition: background-color 0.2s;
}

.image-modal .modal-nav:hover:not(:disabled) {
  background: rgba(0, 0, 0, 0.8);
}

.image-modal .modal-nav:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.image-modal .modal-nav.prev {
  left: 20px;
}

.image-modal .modal-nav.next {
  right: 20px;
}

.preview-item {
  position: relative;
  display: inline-block;
  margin: 8px;
}

.preview-image {
  max-width: 150px;
  max-height: 150px;
  border-radius: 8px;
  object-fit: cover;
}

.preview-remove {
  position: absolute;
  top: -8px;
  right: -8px;
  background: #dc3545;
  border: none;
  color: white;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
}

.preview-remove:hover {
  background: #c82333;
}

body.modal-open {
  overflow: hidden;
}

@media (max-width: 768px) {
  .image-modal .modal-nav {
    display: none;
  }

  .image-modal .modal-content {
    max-width: 100vw;
    max-height: 100vh;
  }
}
</style>
`;

// Add modal styles to head
document.head.insertAdjacentHTML('beforeend', modalStyles);

// Export for global access
window.modernFeedManager = modernFeedManager;
window.openImageModal = openImageModal;
window.editPost = editPost;
window.deletePost = deletePost;
window.reportPost = reportPost;
window.copyPostLink = copyPostLink;
window.savePost = savePost;