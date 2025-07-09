
// CRUNEVO Feed System - Enhanced JavaScript
class CrunevoFeedManager {
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
    this.initGalleryEnhancements();
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
      
      // Hashtag and mention detection
      textarea.addEventListener('input', (e) => {
        this.handleTextInput(e);
      });
    }

    form.querySelectorAll('input[type="file"]').forEach((inp) => {
      inp.addEventListener('change', () => this.updatePostButtonState());
    });

    this.updatePostButtonState();
  }

  handleTextInput(e) {
    const text = e.target.value;
    const cursorPos = e.target.selectionStart;
    
    // Simple hashtag detection for future implementation
    const hashtags = text.match(/#\w+/g) || [];
    const mentions = text.match(/@\w+/g) || [];
    
    // Could implement autocomplete here
    console.debug('Hashtags found:', hashtags);
    console.debug('Mentions found:', mentions);
  }

  async submitPost(form) {
    const submitBtn = form.querySelector('.feed-submit-btn');

    try {
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
    const container = document.getElementById('previewContainer');
    if (container) container.innerHTML = '';
    const input = document.getElementById('feedImageInput');
    if (input) input.value = '';
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

  initGalleryEnhancements() {
    // Initialize lazy loading for gallery images
    if ('IntersectionObserver' in window) {
      const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const img = entry.target;
            if (img.dataset.src) {
              img.src = img.dataset.src;
              img.removeAttribute('data-src');
              imageObserver.unobserve(img);
            }
            img.classList.add('loaded');
          }
        });
      }, {
        rootMargin: '50px'
      });

      document.querySelectorAll('.gallery-img[data-src]').forEach(img => {
        imageObserver.observe(img);
      });
    }

    // Add loading states to gallery images
    document.querySelectorAll('.gallery-img').forEach(img => {
      if (!img.complete) {
        img.addEventListener('load', () => {
          img.classList.add('loaded');
        });
      } else {
        img.classList.add('loaded');
      }
    });
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

      container.style.opacity = '0.5';
      if (loading) loading.classList.remove('d-none');

      const response = await fetch(`/feed/api/quickfeed?filter=${filter}`);
      const data = await response.json();

      container.innerHTML = data.html || '';
      this.initPostInteractions();
      this.initGalleryEnhancements();

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
    // Like buttons with enhanced reactions
    document.querySelectorAll('.like-btn, .action-btn.like-btn').forEach(btn => {
      btn.addEventListener('click', (e) => this.handleLike(e));
      
      // Long press for reaction selector
      let pressTimer;
      btn.addEventListener('mousedown', (e) => {
        pressTimer = setTimeout(() => {
          this.showReactionSelector(btn);
        }, 500);
      });
      
      btn.addEventListener('mouseup', () => {
        clearTimeout(pressTimer);
      });
      
      btn.addEventListener('mouseleave', () => {
        clearTimeout(pressTimer);
      });
    });

    // Comment buttons
    document.querySelectorAll('.comment-btn, .action-btn.comment-btn').forEach(btn => {
      btn.addEventListener('click', (e) => this.openCommentModal(e));
    });

    // Share buttons
    document.querySelectorAll('.share-btn, .action-btn.share-btn').forEach(btn => {
      btn.addEventListener('click', (e) => this.handleShare(e));
    });

    // Save buttons
    document.querySelectorAll('.save-btn, .action-btn.save-btn').forEach(btn => {
      btn.addEventListener('click', (e) => this.toggleSavePost(e));
    });
  }

  showReactionSelector(btn) {
    // Hide any existing selectors
    document.querySelectorAll('.reaction-selector').forEach(sel => {
      sel.classList.remove('show');
    });

    const selector = document.createElement('div');
    selector.className = 'reaction-selector show';
    selector.innerHTML = `
      <button class="reaction-option" data-reaction="🔥" title="Fuego">🔥</button>
      <button class="reaction-option" data-reaction="❤️" title="Me encanta">❤️</button>
      <button class="reaction-option" data-reaction="😂" title="Me divierte">😂</button>
      <button class="reaction-option" data-reaction="😮" title="Me sorprende">😮</button>
      <button class="reaction-option" data-reaction="😢" title="Me entristece">😢</button>
      <button class="reaction-option" data-reaction="😡" title="Me enoja">😡</button>
    `;

    btn.style.position = 'relative';
    btn.appendChild(selector);

    // Handle reaction selection
    selector.querySelectorAll('.reaction-option').forEach(option => {
      option.addEventListener('click', (e) => {
        e.stopPropagation();
        const reaction = option.dataset.reaction;
        this.handleLike({ currentTarget: btn, reaction });
        selector.classList.remove('show');
        setTimeout(() => selector.remove(), 300);
      });
    });

    // Auto-hide after 3 seconds
    setTimeout(() => {
      if (selector.parentElement) {
        selector.classList.remove('show');
        setTimeout(() => selector.remove(), 300);
      }
    }, 3000);
  }

  async handleLike(e) {
    e.preventDefault();
    const btn = e.currentTarget;
    const postId = btn.dataset.postId;
    const reaction = e.reaction || btn.dataset.reaction || '🔥';

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
      const countEl = document.querySelector(`#likeCount${postId}, [data-count-post="${postId}"]`);
      if (countEl) countEl.textContent = data.likes || 0;

      // Update button state
      const icon = btn.querySelector('i');
      if (data.status === 'added') {
        btn.classList.add('active');
        if (icon) {
          icon.classList.add('bi-fire-fill', 'text-danger');
          icon.classList.remove('bi-fire');
        }
        this.animateButton(btn, reaction);
      } else if (data.status === 'removed') {
        btn.classList.remove('active');
        if (icon) {
          icon.classList.remove('text-danger', 'bi-fire-fill');
          icon.classList.add('bi-fire');
        }
      }

      const message = data.status === 'added' ? 
        `¡Reaccionaste con ${reaction}!` : 
        'Reacción removida';
      this.showToast(message, 'success');
      
    } catch (error) {
      console.error('Error handling like:', error);
      this.showToast('Error al procesar reacción', 'error');
    } finally {
      btn.disabled = false;
    }
  }

  handleShare(e) {
    const btn = e.currentTarget;
    const postId = btn.dataset.postId;
    const shareUrl = `${window.location.origin}/feed/post/${postId}`;

    // Native share API for mobile
    if (navigator.share && /Mobile|Android|iPhone/i.test(navigator.userAgent)) {
      navigator.share({
        title: 'Publicación en CRUNEVO',
        text: '¡Mira esta publicación en CRUNEVO!',
        url: shareUrl
      }).catch(console.error);
      return;
    }

    // Show custom share menu
    this.showShareMenu(btn, shareUrl);
  }

  showShareMenu(btn, shareUrl) {
    // Hide any existing menus
    document.querySelectorAll('.share-menu').forEach(menu => {
      menu.classList.remove('show');
    });

    const menu = document.createElement('div');
    menu.className = 'share-menu show';
    menu.innerHTML = `
      <button class="share-option" onclick="window.open('https://wa.me/?text=${encodeURIComponent('¡Mira esta publicación! ' + shareUrl)}', '_blank')">
        <i class="bi bi-whatsapp"></i>
        <span>WhatsApp</span>
      </button>
      <button class="share-option" onclick="window.open('https://twitter.com/intent/tweet?url=${encodeURIComponent(shareUrl)}&text=${encodeURIComponent('¡Mira esta publicación en CRUNEVO!')}', '_blank')">
        <i class="bi bi-twitter"></i>
        <span>Twitter</span>
      </button>
      <button class="share-option" onclick="crunevoFeedManager.copyToClipboard('${shareUrl}')">
        <i class="bi bi-clipboard"></i>
        <span>Copiar enlace</span>
      </button>
    `;

    btn.style.position = 'relative';
    btn.appendChild(menu);

    // Auto-hide when clicking outside
    setTimeout(() => {
      document.addEventListener('click', function hideMenu(e) {
        if (!menu.contains(e.target)) {
          menu.classList.remove('show');
          setTimeout(() => menu.remove(), 300);
          document.removeEventListener('click', hideMenu);
        }
      });
    }, 100);
  }

  copyToClipboard(text) {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text).then(() => {
        this.showToast('¡Enlace copiado al portapapeles!', 'success');
      });
    } else {
      // Fallback
      const textArea = document.createElement('textarea');
      textArea.value = text;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      this.showToast('¡Enlace copiado!', 'success');
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
      <div class="comment-item d-flex gap-3 mb-3">
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
      console.log('Loading page', this.currentPage);
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
      Array.from(temp.children).forEach((el) => {
        const postId = el.getAttribute('data-post-id');
        if (postId) {
          const exists = container.querySelector(`[data-post-id="${postId}"]`);
          if (exists) return;
        }
        container.appendChild(el);
      });

      this.initPostInteractions();
      this.initGalleryEnhancements();
    } catch (error) {
      console.error('Error loading more posts:', error);
      this.showToast('Error al cargar más publicaciones', 'error');
    } finally {
      this.isLoading = false;
    }
  }


  initModals() {
    document.querySelectorAll('.modal').forEach(modalEl => {
      modalEl.addEventListener('hidden.bs.modal', () => {
        const form = modalEl.querySelector('form');
        if (form) form.reset();
      });
    });
  }

  initTooltips() {
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

// Enhanced Image Modal System
let currentImageIndex = 0;
let imageList = [];
let currentPostId = null;
let currentScale = 1;
let modalImageEl;
let postData = null;
let touchStartX = 0;
let touchEndX = 0;
let isDragging = false;
let dragStartX = 0;
let dragStartY = 0;

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
  } else if (e.key === ' ') {
    e.preventDefault();
    resetZoom();
  }
}

function handleWheel(e) {
  e.preventDefault();
  const rect = modalImageEl.getBoundingClientRect();
  const centerX = rect.left + rect.width / 2;
  const centerY = rect.top + rect.height / 2;
  
  if (e.deltaY < 0) {
    zoomIn(e.clientX - centerX, e.clientY - centerY);
  } else {
    zoomOut();
  }
}

function handleTouchStart(e) {
  if (e.touches.length === 1) {
    touchStartX = e.touches[0].screenX;
    isDragging = currentScale > 1;
    dragStartX = e.touches[0].clientX;
    dragStartY = e.touches[0].clientY;
  }
}

function handleTouchEnd(e) {
  if (e.changedTouches.length === 1 && !isDragging) {
    touchEndX = e.changedTouches[0].screenX;
    handleSwipe();
  }
  isDragging = false;
}

function handleSwipe() {
  const swipeThreshold = 50;
  const diff = touchStartX - touchEndX;
  
  if (Math.abs(diff) > swipeThreshold) {
    if (diff > 0) {
      nextImage();
    } else {
      prevImage();
    }
  }
}

function applyZoom(originX = 0, originY = 0) {
  const img = document.getElementById('modalImage');
  if (img) {
    img.style.transformOrigin = `${originX}px ${originY}px`;
    img.style.transform = `scale(${currentScale})`;
    
    if (currentScale > 1) {
      img.style.cursor = 'grab';
    } else {
      img.style.cursor = 'zoom-in';
    }
  }
}

function zoomIn(originX = 0, originY = 0) {
  currentScale = Math.min(3, currentScale + 0.25);
  applyZoom(originX, originY);
}

function zoomOut() {
  currentScale = Math.max(0.5, currentScale - 0.25);
  applyZoom();
}

function resetZoom() {
  currentScale = 1;
  applyZoom();
}

function openImageModal(src, index, postId, evt) {
  if (index === undefined || index === null || isNaN(index)) {
    console.error('Índice inválido para modal:', index);
    return;
  }
  
  let container = null;
  if (evt && evt.currentTarget) {
    container = evt.currentTarget.closest('.crunevo-gallery-wrapper');
  }
  if (!container) {
    container = document.querySelector(`[data-post-id='${postId}']`);
  }

  if (container && container.dataset.images) {
    try {
      imageList = JSON.parse(container.dataset.images);
    } catch {
      imageList = [];
    }
  }
  if (!imageList.length && container) {
    imageList = Array.from(container.querySelectorAll('.gallery-img')).map((img) => img.src);
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
  
  const hasMultipleImages = imageList.length > 1;
  
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
        
        ${hasMultipleImages ? `
          <button class="modal-nav prev" onclick="prevImage()" title="Imagen anterior" ${index === 0 ? 'disabled' : ''}>
            <i class="bi bi-chevron-left"></i>
          </button>
          <button class="modal-nav next" onclick="nextImage()" title="Siguiente imagen" ${index === imageList.length - 1 ? 'disabled' : ''}>
            <i class="bi bi-chevron-right"></i>
          </button>
        ` : ''}
        
        <div class="modal-counter" id="modalCounter">${index + 1} / ${imageList.length}</div>
        
        <div class="touch-indicator">
          Desliza ← → para navegar<br>
          Pellizca para hacer zoom
        </div>
      </div>
      
      <div class="modal-info-section" id="imageModalInfo">
        <div class="modal-loading">
          <div class="spinner-border text-primary"></div>
        </div>
      </div>
    </div>
  `;
  
  modalImageEl = modal.querySelector('#modalImage');
  modal.classList.remove('hidden');
  modal.classList.add('modal-fade-in');
  document.body.classList.add('photo-modal-open');
  
  // Add event listeners
  window.addEventListener('keydown', handleModalKeydown);
  modalImageEl.addEventListener('wheel', handleWheel, { passive: false });
  modalImageEl.addEventListener('touchstart', handleTouchStart, { passive: true });
  modalImageEl.addEventListener('touchend', handleTouchEnd, { passive: true });
  
  // Double-click to zoom
  modalImageEl.addEventListener('dblclick', (e) => {
    if (currentScale === 1) {
      const rect = modalImageEl.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      zoomIn(x, y);
    } else {
      resetZoom();
    }
  });
  
  // Load post data for right panel
  loadPostDataForModal(postId);
  
  // Update URL
  window.history.pushState({ photo: true }, '', `/feed/post/${postId}/photo/${index + 1}`);
  
  // Preload adjacent images
  preloadAdjacentImages(index);
}

function preloadAdjacentImages(currentIndex) {
  const preloadIndices = [currentIndex - 1, currentIndex + 1];
  preloadIndices.forEach(idx => {
    if (idx >= 0 && idx < imageList.length && idx !== currentIndex) {
      const img = new Image();
      img.src = imageList[idx];
    }
  });
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
              <span>Me gusta</span>
            </button>
            <button class="modal-action-btn comment-btn" data-post-id="${postId}">
              <i class="bi bi-chat"></i>
              <span>Comentar</span>
            </button>
            <button class="modal-action-btn share-btn" data-post-id="${postId}">
              <i class="bi bi-share"></i>
              <span>Compartir</span>
            </button>
            <button class="modal-action-btn save-btn" data-post-id="${postId}">
              <i class="bi bi-bookmark"></i>
              <span>Guardar</span>
            </button>
          </div>
          
          <div class="modal-comments-section">
            ${data.comments ? data.comments.map(comment => `
              <div class="comment-item">
                <img src="${comment.author?.avatar_url || '/static/img/default.png'}" 
                     alt="Avatar" width="32" height="32">
                <div>
                  <div class="comment-box">
                    <div class="fw-semibold">${comment.author?.username}</div>
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
    likeBtn.addEventListener('click', (e) => crunevoFeedManager.handleLike(e));
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
    shareBtn.addEventListener('click', (e) => crunevoFeedManager.handleShare(e));
  }
  
  // Save button in modal
  const saveBtn = document.querySelector('.modal-action-btn.save-btn');
  if (saveBtn) {
    saveBtn.addEventListener('click', (e) => crunevoFeedManager.toggleSavePost(e));
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
  formData.append('csrf_token', crunevoFeedManager.getCSRFToken());
  
  fetch(`/feed/comment/${postId}`, {
    method: 'POST',
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    if (data.success !== false) {
      input.value = '';
      loadPostDataForModal(postId); // Reload comments
      crunevoFeedManager.showToast('Comentario agregado', 'success');
    } else {
      crunevoFeedManager.showToast('Error al agregar comentario', 'error');
    }
  })
  .catch(error => {
    console.error('Error submitting comment:', error);
    crunevoFeedManager.showToast('Error de conexión', 'error');
  });
}

function closeImageModal() {
  const modal = document.getElementById('imageModal');
  if (modal) {
    modal.classList.add('modal-fade-out');
    modal.classList.remove('modal-fade-in');
    
    setTimeout(() => {
      modal.classList.add('hidden');
      modal.classList.remove('modal-fade-out');
      document.getElementById('imageModalInfo').innerHTML = '';
      document.body.classList.remove('photo-modal-open');
    }, 300);
    
    window.removeEventListener('keydown', handleModalKeydown);
    if (modalImageEl) {
      modalImageEl.removeEventListener('wheel', handleWheel);
      modalImageEl.removeEventListener('touchstart', handleTouchStart);
      modalImageEl.removeEventListener('touchend', handleTouchEnd);
    }
    currentPostId = null;
    window.history.back();
  }
}

function nextImage() {
  if (currentImageIndex < imageList.length - 1) {
    currentImageIndex++;
    updateModalImage();
  }
}

function prevImage() {
  if (currentImageIndex > 0) {
    currentImageIndex--;
    updateModalImage();
  }
}

function updateModalImage() {
  const modalImg = document.getElementById('modalImage');
  if (modalImg && imageList[currentImageIndex]) {
    modalImg.src = imageList[currentImageIndex];
    modalImg.alt = `Imagen ${currentImageIndex + 1} de ${imageList.length}`;
    
    // Update navigation button states
    const prevBtn = document.querySelector('.modal-nav.prev');
    const nextBtn = document.querySelector('.modal-nav.next');
    
    if (prevBtn) {
      prevBtn.disabled = currentImageIndex === 0;
    }
    if (nextBtn) {
      nextBtn.disabled = currentImageIndex === imageList.length - 1;
    }
    
    updateModalCounter();
    if (currentPostId) {
      updateModalRoute(currentPostId, currentImageIndex);
    }
    
    // Reset zoom
    currentScale = 1;
    applyZoom();
    
    // Preload adjacent images
    preloadAdjacentImages(currentImageIndex);
  }
}

function updateModalRoute(postId, index) {
  const url = `/feed/post/${postId}/photo/${index + 1}`;
  history.replaceState({ photo: true }, '', url);
}

function updateModalCounter() {
  const counter = document.getElementById('modalCounter');
  if (counter) {
    counter.textContent = `${currentImageIndex + 1} / ${imageList.length}`;
  }
}

// Global functions for post actions
function editPost(postId) {
  const card = document.querySelector(`[data-post-id='${postId}']`);
  const textarea = document.querySelector('#editPostForm textarea[name="content"]');
  const select = document.querySelector('#editPostForm select[name="comment_permission"]');
  const form = document.getElementById('editPostForm');
  
  if (!card || !textarea || !form) return;
  
  const contentEl = card.querySelector('.post-text, .feed-text');
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
  
  crunevoFeedManager.fetchWithCSRF(`/feed/post/eliminar/${postId}`, { method: 'POST' })
    .then((resp) => {
      if (resp.ok) {
        document.querySelector(`[data-post-id='${postId}']`)?.remove();
        crunevoFeedManager.showToast('Publicación eliminada', 'success');
      } else {
        crunevoFeedManager.showToast('Error al eliminar', 'error');
      }
    })
    .catch(() => crunevoFeedManager.showToast('Error de conexión', 'error'));
}

function reportPost(postId) {
  if (confirm('¿Quieres reportar esta publicación?')) {
    crunevoFeedManager.showToast('Publicación reportada', 'info');
  }
}

function copyPostLink(postId) {
  const url = `${window.location.origin}/feed/post/${postId}`;
  crunevoFeedManager.copyToClipboard(url);
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

  .gallery-img.loaded {
    opacity: 1;
    transition: opacity 0.3s ease;
  }

  .gallery-img:not(.loaded) {
    opacity: 0.7;
  }
`;
document.head.appendChild(style);

// Feed manager initialization
let crunevoFeedManager;
function initFeedManager() {
  crunevoFeedManager = new CrunevoFeedManager();
}

// Auto-initialize if DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initFeedManager);
} else {
  initFeedManager();
}

// Global exports
window.crunevoFeedManager = crunevoFeedManager;
window.openImageModal = openImageModal;
window.closeImageModal = closeImageModal;
window.nextImage = nextImage;
window.prevImage = prevImage;
window.zoomIn = zoomIn;
window.zoomOut = zoomOut;
window.resetZoom = resetZoom;
window.editPost = editPost;
window.deletePost = deletePost;
window.reportPost = reportPost;
window.copyPostLink = copyPostLink;
window.initFeedManager = initFeedManager;

// Edit post form handler
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
    formData.append('csrf_token', crunevoFeedManager.getCSRFToken());

    try {
      const resp = await crunevoFeedManager.fetchWithCSRF(`/feed/post/editar/${postId}`, {
        method: 'POST',
        body: formData
      });
      
      if (resp.ok) {
        const card = document.querySelector(`[data-post-id='${postId}']`);
        const contentEl = card ? card.querySelector('.post-text, .feed-text') : null;
        if (contentEl) {
          contentEl.textContent = content;
        }
        crunevoFeedManager.showToast('Publicación actualizada', 'success');
        bootstrap.Modal.getInstance(document.getElementById('editPostModal')).hide();
      } else {
        crunevoFeedManager.showToast('Error al editar publicación', 'error');
      }
    } catch (error) {
      crunevoFeedManager.showToast('Error de conexión', 'error');
    }
  });
}
