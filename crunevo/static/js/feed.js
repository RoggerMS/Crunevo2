// CRUNEVO Modern Feed System - Facebook-style functionality
class ModernFeedManager {
  constructor() {
    this.currentPage = 1;
    this.isLoading = false;
    this.reachedEnd = false;
    this.currentFilter = 'recientes';
    this.posts = new Map();
    this.imageFiles = [];
    this.currentImageIndex = 0;
    this.imageList = [];
    this.currentPostId = null;
    this.currentScale = 1;
    this.modalImageEl = null;
    this.touchStartX = 0;
    this.touchEndX = 0;
    this.commentEventsBound = false;
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
    this.initStreakClaim();
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

  // Initialize streak claim button
  initStreakClaim() {
    const btn = document.getElementById('claimStreakBtn');
    if (!btn) return;

    btn.addEventListener('click', async () => {
      const original = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
      try {
        const resp = await this.fetchWithCSRF('/api/reclamar-racha', {
          method: 'POST'
        });
        const data = await resp.json();
        if (data.success) {
          this.showToast(`\uD83C\uDF89 \u00A1D\u00EDa ${data.day}! Has ganado ${data.credits} crolars`, 'success');
          const banner = document.getElementById('streakBanner');
          if (banner) banner.remove();
          if (typeof updateCreditsDisplay === 'function') {
            updateCreditsDisplay(data.balance);
          } else if (window.CRUNEVO_UI?.updateUserCredits) {
            window.CRUNEVO_UI.updateUserCredits(data.balance);
          }
        } else {
          this.showToast(data.message || 'Error al reclamar', 'error');
          btn.disabled = false;
          btn.innerHTML = original;
        }
      } catch (err) {
        console.error('Error claiming streak:', err);
        this.showToast('Error de conexi\u00F3n', 'error');
        btn.disabled = false;
        btn.innerHTML = original;
      }
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
      this.imageFiles.forEach(file => {
        formData.append('files', file);
      });
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
    if (this.commentEventsBound) return;
    const container = document.getElementById('feedContainer');
    if (!container) return;

    container.addEventListener('click', (e) => {
      if (e.target.matches('.comment-btn') || e.target.closest('.comment-btn')) {
        const btn = e.target.closest('.comment-btn');
        const postId = btn.dataset.postId;
        this.toggleComments(postId);
      }
    });

    container.addEventListener('submit', (e) => {
      if (e.target.matches('.comment-form')) {
        e.preventDefault();
        const form = e.target;
        const postId = form.dataset.postId;
        this.submitComment(form, postId);
      }
    });

    container.addEventListener('input', (e) => {
      if (e.target.matches('.comment-input')) {
        const form = e.target.closest('.comment-form');
        const submitBtn = form?.querySelector('.comment-submit-btn');
        if (submitBtn) {
          submitBtn.disabled = !e.target.value.trim();
        }
      }
    });

    this.commentEventsBound = true;
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

    if (!input || !submitBtn) return;

    const body = input.value.trim();

    if (!body) return;

    try {
      if (submitBtn) submitBtn.disabled = true;

      const formData = new FormData();
      formData.append('body', body);
      formData.append('csrf_token', this.getCSRFToken());

      const response = await fetch(`/feed/comment/${postId}`, {
        method: 'POST',
        body: formData
      });

      if (response.status === 202) {
        this.showToast('Comentario pendiente de aprobación', 'info');
        if (input) input.value = '';
      } else if (response.ok) {
        const comment = await response.json();
        this.addCommentToUI(comment, postId);
        if (input) input.value = '';
        this.showToast('Comentario agregado', 'success');
      } else {
        const data = await response.json().catch(() => ({}));
        const msg = data.error ||
          (response.status === 403 ? 'Comentarios deshabilitados' : 'Error al agregar comentario');
        this.showToast(msg, 'error');
      }
    } catch (error) {
      console.error('Error submitting comment:', error);
      this.showToast('Error de conexión', 'error');
    } finally {
      if (submitBtn) submitBtn.disabled = false;
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
        if (!btn._longPress) {
          this.handleLike(btn);
        }
      }
    });

    // Reaction buttons
    document.addEventListener('click', (e) => {
      if (e.target.matches('.reaction-btn')) {
        const btn = e.target;
        const container = btn.closest('.reaction-container');
        const likeBtn = container.querySelector('.like-btn');
        likeBtn.dataset.reaction = btn.dataset.reaction;
        this.handleLike(likeBtn);
        container.querySelector('.reaction-panel')?.classList.add('d-none');
      }
    });

    // Long press for mobile/desktop
    document.addEventListener('touchstart', (e) => {
      const btn = e.target.closest('.like-btn');
      if (!btn) return;
      btn._longPress = false;
      btn._pressTimer = setTimeout(() => {
        btn._longPress = true;
        this.showReactionPanel(btn);
      }, 500);
    });

    document.addEventListener('touchend', (e) => {
      const btn = e.target.closest('.like-btn');
      if (!btn) return;
      clearTimeout(btn._pressTimer);
      if (!btn._longPress) {
        this.handleLike(btn);
      }
    });

    document.addEventListener('mousedown', (e) => {
      const btn = e.target.closest('.like-btn');
      if (!btn) return;
      btn._longPress = false;
      btn._pressTimer = setTimeout(() => {
        btn._longPress = true;
        this.showReactionPanel(btn);
      }, 500);
    });

    document.addEventListener('mouseup', (e) => {
      const btn = e.target.closest('.like-btn');
      if (!btn) return;
      clearTimeout(btn._pressTimer);
      if (!btn._longPress) {
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

    // Click on reactions count
    document.addEventListener('click', async (e) => {
      const target = e.target.closest('.post-reactions-count');
      if (!target) return;
      const postId = target.dataset.postId;
      if (!postId) return;

      const modalEl = document.getElementById(`reactionsModal-${postId}`);
      if (!modalEl) return;
      const listEl = modalEl.querySelector(`#reactionsList-${postId}`);
      if (!listEl) return;

      listEl.innerHTML = '<div class="text-center my-2">Cargando...</div>';
      try {
        const response = await fetch(`/feed/api/reactions/${postId}`);
        const data = await response.json();
        listEl.innerHTML = '';
        for (const [reaction, users] of Object.entries(data)) {
          users.forEach(u => {
            const item = document.createElement('div');
            item.className = 'list-group-item d-flex align-items-center';
            item.innerHTML = `
              <img src="${u.avatar}" alt="${u.username}" class="rounded-circle me-2" style="width:32px;height:32px;object-fit:cover;">
              <span class="flex-grow-1">${u.username}</span>
              <span class="ms-2">${reaction}</span>`;
            listEl.appendChild(item);
          });
        }
      } catch {
        listEl.innerHTML = '<div class="text-danger text-center">Error al cargar</div>';
      }

      const modal = new bootstrap.Modal(modalEl);
      modal.show();
    });
  }

  // Handle like button
  async handleLike(btn) {
    const postId = btn.dataset.postId;
    const reaction = btn.dataset.reaction || '🔥';

    if (btn.disabled) return;

    const icon = btn.querySelector('i');
    const countSpan = btn.querySelector('.action-count');

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

      // Update reaction counts
      const postReactions = document.querySelector(`.post-reactions-count[data-post-id="${postId}"]`);
      if (postReactions) {
        const reactionsSummary = postReactions.querySelector('.reactions-summary');
        if (reactionsSummary) {
          const reactionIcons = reactionsSummary.querySelector('.reaction-icons');
          const reactionsText = reactionsSummary.querySelector('.reactions-text');
          if (reactionIcons && reactionsText) {
            reactionIcons.innerHTML = '';
            let totalReactions = 0;
            for (const [reaction_type, count] of Object.entries(data.counts)) {
              const reactionEmoji = document.createElement('span');
              reactionEmoji.className = 'reaction-emoji';
              reactionEmoji.textContent = reaction_type;
              reactionIcons.appendChild(reactionEmoji);
              totalReactions += count;
            }
            reactionsText.textContent = totalReactions;
          }
        }
      }


      // Update button state
      if (data.status === 'added' || data.status === 'changed') {
        btn.classList.add('active');
        if (icon) {
          icon.classList.remove('bi-fire');
          icon.classList.add('bi-fire-fill');
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

      if (countSpan) {
        countSpan.textContent = data.total_reactions > 0 ? data.total_reactions : '';
      }


    } catch (error) {
      console.error('Error handling like:', error);
      this.showToast('Error al procesar reacción', 'error');
    } finally {
      btn.disabled = false;
      setTimeout(() => btn.classList.remove('like-animation'), 300);
    }
  }

  showReactionPanel(btn) {
    const panel = btn.parentElement.querySelector('.reaction-panel');
    if (!panel) return;
    panel.classList.remove('d-none');
    clearTimeout(panel._hideTimer);
    panel._hideTimer = setTimeout(() => {
      panel.classList.add('d-none');
    }, 4000);
    panel.addEventListener(
      'mouseleave',
      () => panel.classList.add('d-none'),
      { once: true }
    );
  }

  // Handle share button with graceful fallback
  handleShare(btn) {
    const postId = btn.dataset.postId;
    const shareUrl = `${window.location.origin}/feed/post/${postId}`;
    const shareTitle = 'Publicación en CRUNEVO';

    if (navigator.share) {
      navigator
        .share({ title: shareTitle, url: shareUrl })
        .catch(console.error);
    } else {
      this.copyToClipboard(shareUrl);
      this.showToast('¡Enlace copiado!', 'success');
    }
  }

  // Handle save button
  async handleSave(btn) {
    const postId = btn.dataset.postId;
    const icon = btn.querySelector('i');
    const wasSaved = btn.classList.contains('active');

    // Optimistic UI update
    btn.classList.toggle('active');
    if (icon) {
      icon.classList.toggle('bi-bookmark-fill');
      icon.classList.toggle('bi-bookmark');
    }

    try {
      btn.disabled = true;

      const response = await this.fetchWithCSRF(`/feed/save/${postId}`, {
        method: 'POST'
      });

      const data = await response.json();

      if (data.saved !== !wasSaved) {
        btn.classList.toggle('active', data.saved);
        if (icon) {
          icon.classList.toggle('bi-bookmark-fill', data.saved);
          icon.classList.toggle('bi-bookmark', !data.saved);
        }
      }

      this.showToast(
        data.saved ? 'Publicación guardada' : 'Publicación removida de guardados',
        data.saved ? 'success' : 'info'
      );
    } catch (error) {
      console.error('Error toggling save:', error);
      // revert optimistic update
      btn.classList.toggle('active', wasSaved);
      if (icon) {
        icon.classList.toggle('bi-bookmark-fill', wasSaved);
        icon.classList.toggle('bi-bookmark', !wasSaved);
      }
      this.showToast('Error al guardar', 'error');
    } finally {
      btn.disabled = false;
    }
  }

  // Initialize image modal
  initImageModal() {
    document.addEventListener('keydown', (e) => this.handleModalKeydown(e));
  }

  handleModalKeydown(e) {
    if (!this.currentPostId) return;
    if (e.key === 'Escape') {
      this.closeImageModal();
    } else if (e.key === 'ArrowRight') {
      this.nextImage();
    } else if (e.key === 'ArrowLeft') {
      this.prevImage();
    } else if (e.key === '+') {
      this.zoomIn();
    } else if (e.key === '-') {
      this.zoomOut();
    } else if (e.key === ' ') {
      e.preventDefault();
      this.resetZoom();
    }
  }

  // Open image modal
  openImageModal(src, index, postId, evt) {
    const container = evt?.currentTarget.closest('.facebook-gallery-container') ||
                     document.querySelector(`.facebook-gallery-container[data-post-id='${postId}']`) ||
                     document.querySelector(`[data-post-id='${postId}'] .facebook-gallery-container`);

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
    this.currentScale = 1;

    this.createImageModal(src, index);
    window.history.pushState({ photo: true }, '', `/feed/post/${postId}/photo/${index + 1}`);
  }

  // Create image modal
  createImageModal(src, index) {
    const modal = document.createElement('div');
    modal.id = 'imageModal';
    modal.className = 'image-modal hidden';
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.setAttribute('aria-labelledby', 'imageModalLabel');
    modal.setAttribute('tabindex', '-1');

    const hasMultiple = this.imageList.length > 1;
    modal.innerHTML = `
      <div class="modal-container" onclick="modernFeedManager.outsideImageClick(event)">
        <h2 id="imageModalLabel" class="visually-hidden">Visor de imagen</h2>
        <div class="modal-image-section">
          <img id="modalImage" src="${src}" alt="Imagen ${index + 1}">
          <div class="modal-top-controls">
            <button type="button" class="modal-control-btn" onclick="modernFeedManager.zoomOut()" title="Reducir zoom" aria-label="Reducir zoom"><i class="bi bi-dash"></i></button>
            <button type="button" class="modal-control-btn" onclick="modernFeedManager.zoomIn()" title="Aumentar zoom" aria-label="Aumentar zoom"><i class="bi bi-plus"></i></button>
            <button type="button" class="modal-control-btn" onclick="modernFeedManager.resetZoom()" title="Tamaño original" aria-label="Tamaño original"><i class="bi bi-arrows-fullscreen"></i></button>
            <a href="${src}" target="_blank" class="modal-control-btn" title="Abrir en nueva pestaña" aria-label="Abrir en nueva pestaña"><i class="bi bi-box-arrow-up-right"></i></a>
            <button type="button" class="modal-control-btn" onclick="modernFeedManager.closeImageModal()" title="Cerrar" aria-label="Cerrar"><i class="bi bi-x"></i></button>
          </div>
          ${hasMultiple ? `
            <button type="button" class="modal-nav prev" onclick="modernFeedManager.prevImage()" aria-label="Imagen anterior" ${index === 0 ? 'style="opacity:0.5"' : ''}><i class="bi bi-chevron-left"></i></button>
            <button type="button" class="modal-nav next" onclick="modernFeedManager.nextImage()" aria-label="Imagen siguiente" ${index === this.imageList.length - 1 ? 'style="opacity:0.5"' : ''}><i class="bi bi-chevron-right"></i></button>
          ` : ''}
          <div class="modal-counter" id="modalCounter">${index + 1} / ${this.imageList.length}</div>
        </div>
        <div class="modal-info-section" id="imageModalInfo">
          <div class="d-flex justify-content-center align-items-center h-100">
            <div class="spinner-border text-primary"></div>
          </div>
        </div>
      </div>`;

    document.body.appendChild(modal);
    modal.focus();
    document.body.classList.add('photo-modal-open');

    this.modalImageEl = modal.querySelector('#modalImage');
    this.modalImageEl.addEventListener('wheel', (e) => this.handleWheel(e), { passive: false });
    this.modalImageEl.addEventListener('touchstart', (e) => this.handleTouchStart(e));
    this.modalImageEl.addEventListener('touchend', (e) => this.handleTouchEnd(e));

    setTimeout(() => modal.classList.remove('hidden'), 10);
    this.loadPostDataForModal(this.currentPostId);
  }

  // Close image modal
  closeImageModal() {
    const modal = document.getElementById('imageModal');
    if (modal) {
      modal.classList.add('hidden');
      setTimeout(() => {
        modal.remove();
        document.body.classList.remove('photo-modal-open');
      }, 300);
    }

    if (this.modalImageEl) {
      this.modalImageEl.removeEventListener('wheel', this.handleWheel);
      this.modalImageEl.removeEventListener('touchstart', this.handleTouchStart);
      this.modalImageEl.removeEventListener('touchend', this.handleTouchEnd);
    }
    this.modalImageEl = null;
    this.currentScale = 1;

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

    const img = modal.querySelector('#modalImage');
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

  handleWheel(e) {
    e.preventDefault();
    if (e.deltaY < 0) {
      this.zoomIn();
    } else {
      this.zoomOut();
    }
  }

  handleTouchStart(e) {
    this.touchStartX = e.changedTouches[0].screenX;
  }

  handleTouchEnd(e) {
    this.touchEndX = e.changedTouches[0].screenX;
    this.handleSwipe();
  }

  handleSwipe() {
    const diff = this.touchStartX - this.touchEndX;
    if (Math.abs(diff) > 50) {
      if (diff > 0) {
        this.nextImage();
      } else {
        this.prevImage();
      }
    }
  }

  applyZoom() {
    if (this.modalImageEl) {
      this.modalImageEl.style.transform = `scale(${this.currentScale})`;
    }
  }

  zoomIn() {
    this.currentScale = Math.min(3, this.currentScale + 0.2);
    this.applyZoom();
  }

  zoomOut() {
    this.currentScale = Math.max(0.2, this.currentScale - 0.2);
    this.applyZoom();
  }

  resetZoom() {
    this.currentScale = 1;
    this.applyZoom();
  }

  outsideImageClick(e) {
    if (e.target.id === 'imageModal') {
      this.closeImageModal();
    }
  }

  loadPostDataForModal(postId) {
    fetch(`/feed/api/post/${postId}`)
      .then(r => r.json())
      .then(data => {
        const info = document.getElementById('imageModalInfo');
        if (info && data.html) {
          info.innerHTML = data.html;
          this.initPostInteractions();
          this.initCommentSystem();
        }
      })
      .catch(() => {
        const info = document.getElementById('imageModalInfo');
        if (info) info.innerHTML = '<div class="text-center text-muted p-3">Error al cargar información del post</div>';
      });
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
    console.log('loadFilteredFeed ACTIVADO');
    console.log('[DEBUG]', {
      currentPage: this.currentPage,
      currentFilter: this.currentFilter,
      isLoading: this.isLoading,
      reachedEnd: this.reachedEnd
    });

    const container = document.getElementById('feedContainer');
    if (!container) return;
    if (filter === "apuntes") {
      container.classList.add("feed-as-grid");
    } else {
      container.classList.remove("feed-as-grid");
    }

    const filterChanged = filter !== this.currentFilter;

    try {
      this.currentFilter = filter;
      this.currentPage = 1;
      this.reachedEnd = false;
      const loader = document.getElementById('feed-loader');
      if (loader) {
        loader.querySelector('.spinner-border')?.classList.remove('d-none');
        loader.style.display = '';
      }

      // Show loading state
      this.showSkeletonPosts();

      const response = await fetch(`/feed/api/quickfeed?filter=${filter}`);
      const data = await response.json();

      // Hide skeletons
      this.removeSkeletonPosts();

      // Update content
      if (typeof data.html === 'string' && data.html.trim() === '') {
        console.log('Empty HTML received for filter', filter);
        container.innerHTML = '<div class="text-center text-muted">No se encontraron publicaciones.</div>';
        this.reachedEnd = true;
      } else if (this.currentPage === 1 || filterChanged) {
        console.log('[FEED] Actualizando HTML del contenedor');
        container.innerHTML = data.html;
      }

      // Reinitialize interactions if posts were loaded
      if (typeof data.html === 'string' && data.html.trim() !== '') {
        this.initPostInteractions();
        this.initCommentSystem();
        if (typeof initNotePreviews !== 'undefined') {
          initNotePreviews();
        }
      }

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

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !this.isLoading && !this.reachedEnd) {
          this.loadMorePosts();
        }
      },
      {
        rootMargin: '100px',
      }
    );

    observer.observe(sentinel);
    this.infiniteObserver = observer;
  }

  // Load more posts
  async loadMorePosts() {
    console.log('[DEBUG]', {
      currentPage: this.currentPage,
      currentFilter: this.currentFilter,
      isLoading: this.isLoading,
      reachedEnd: this.reachedEnd
    });
    if (this.isLoading || this.reachedEnd) return;
    this.isLoading = true;
    setTimeout(() => {
      if (this.isLoading) this.isLoading = false;
    }, 1000);
    const loader = document.getElementById('feed-loader');
    if (loader) {
      loader.style.display = '';
      loader.querySelector('.spinner-border')?.classList.remove('d-none');
    }

    try {
      this.currentPage++;
      const response = await fetch(`/feed/load?page=${this.currentPage}&categoria=${this.currentFilter}`);
      const data = await response.text();
      console.log('[DEBUG] HTML recibido:', data);
      const container = document.getElementById('feedContainer');
      const temp = document.createElement('div');
      temp.innerHTML = data;

      if (data.trim() === '' || data.includes('no-more-posts')) {
        console.log('No more posts to load');
        if (loader) {
          loader.style.display = 'none';
        }
        if (!this.reachedEnd) {
          this.infiniteObserver?.unobserve(document.getElementById('feedEnd'));
        }
        this.reachedEnd = true;
        if (data.trim()) {
          container.insertAdjacentHTML('beforeend', data);
        } else {
          container.insertAdjacentHTML('beforeend', '<div class="text-center text-muted">No se encontraron más publicaciones.</div>');
        }
        return;
      }

      Array.from(temp.children).forEach(el => {
        console.log('[DEBUG] Elemento analizado:', el.outerHTML);
        const postId = el.getAttribute('data-post-id');
        if (!postId || !container.querySelector(`[data-post-id="${postId}"]`)) {
          el.classList.add('fade-in');
          container.appendChild(el);
        }
      });
      if (typeof initNotePreviews !== "undefined") {
        initNotePreviews();
      }

    } catch (error) {
      console.error('Error loading more posts:', error);
      this.showToast('Error al cargar más publicaciones', 'error');
      loader?.querySelector('.spinner-border')?.classList.add('d-none');
      if (!this.reachedEnd) {
        this.infiniteObserver?.unobserve(document.getElementById('feedEnd'));
      }
      this.reachedEnd = true;
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


// Post Interest Functions
function interestPost(postId) {
  fetch(`/feed/interest/${postId}`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': window.modernFeedManager?.getCSRFToken() || ''
    }
  })
  .then(response => response.json())
  .then(data => {
    if (data.status === 'success') {
      window.modernFeedManager?.showToast('✅ Marcado como interesante', 'success');
    }
  })
  .catch(error => {
    console.error('Error:', error);
    window.modernFeedManager?.showToast('Error al procesar', 'error');
  });
}

function notInterestedPost(postId) {
  if (confirm('¿No te interesa ver este tipo de contenido?')) {
    fetch(`/feed/not-interested/${postId}`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': window.modernFeedManager?.getCSRFToken() || ''
      }
    })
    .then(response => response.json())
    .then(data => {
      if (data.status === 'success') {
        // Hide the post with animation
        const postElement = document.querySelector(`[data-post-id="${postId}"]`);
        if (postElement) {
          postElement.style.opacity = '0.5';
          setTimeout(() => {
            postElement.style.display = 'none';
          }, 300);
        }
        window.modernFeedManager?.showToast('👍 Gracias por tu feedback', 'info');
      }
    })
    .catch(error => {
      console.error('Error:', error);
      window.modernFeedManager?.showToast('Error al procesar', 'error');
    });
  }
}

// Enhanced Share Function

// Comment input validation
document.addEventListener('input', (e) => {
  if (e.target.matches('.comment-input')) {
    const form = e.target.closest('.comment-form');
    const submitBtn = form?.querySelector('button[type="submit"]');
    if (submitBtn) {
      submitBtn.disabled = !e.target.value.trim();
    }
  }
});

// Enhanced share button functionality
document.addEventListener('click', (e) => {
  if (e.target.matches('.share-btn') || e.target.closest('.share-btn')) {
    e.preventDefault();
    const btn = e.target.closest('.share-btn');
    if (window.modernFeedManager?.handleShare) {
      window.modernFeedManager.handleShare(btn);
    }
  }
});

document.addEventListener('click', (e) => {
  if (e.target.matches('.load-more-comments')) {
    e.preventDefault();
    const btn = e.target;
    const postId = btn.dataset.postId;
    if (postId) {
      loadMoreComments(btn, postId);
    }
  }
});

// Comments Modal Functions provided by comment.js

function updateCommentCount(postId, increment) {
  const commentBtn = document.querySelector(`[data-post-id="${postId}"].comment-btn`);
  if (commentBtn) {
    const countSpan = commentBtn.querySelector('.action-count');
    if (countSpan) {
      const currentCount = parseInt(countSpan.textContent) || 0;
      const newCount = currentCount + increment;
      countSpan.textContent = newCount > 0 ? newCount : '';
    }
  }
}

function loadMoreComments(btn, postId) {
  const page = parseInt(btn.dataset.page || '1');
  btn.disabled = true;
  fetch(`/feed/api/comments/${postId}?page=${page}`)
    .then(async r => {
      if (!r.ok) {
        const data = await r.json().catch(() => ({}));
        const msg = data.error || 'Error al cargar comentarios';
        throw new Error(msg);
      }
      return r.json();
    })
    .then(comments => {
      if (comments.length) {
        comments.forEach(c => addCommentToModalUI(c, postId));
        btn.dataset.page = page + 1;
        btn.disabled = false;
        if (comments.length < 10) {
          btn.remove();
        }
      } else {
        btn.remove();
      }
    })
    .catch(err => {
      window.modernFeedManager?.showToast(err.message, 'error');
      btn.disabled = false;
    });
}

// Load comments for photo view
function initPhotoComments() {
  const section = document.getElementById('comment-section');
  if (!section) return;

  const postId = section.dataset.postId;

  fetch(`/feed/api/comments/${postId}`)
    .then((r) => r.json())
    .then((comments) => {
      const listId = `commentsList-${postId}`;
      const formHtml = `\n          <div class="comments-list" id="${listId}"></div>\n          <form class="comment-form d-flex align-items-center mt-3" data-post-id="${postId}" onsubmit="submitModalComment(event, '${postId}')">\n            <img src="${window.CURRENT_USER?.avatar || '/static/img/default.png'}" alt="avatar" class="rounded-circle me-2" style="width:32px;height:32px;object-fit:cover;">\n            <div class="flex-grow-1 position-relative">\n              <input type="text" class="form-control comment-input rounded-pill" placeholder="Escribe un comentario..." name="body" style="padding-right:40px;">\n              <button type="submit" class="btn position-absolute end-0 top-50 translate-middle-y me-2" style="border:none;background:none;color:#1877F2;" disabled>\n                <i class="bi bi-send-fill"></i>\n              </button>\n            </div>\n            <input type="hidden" name="csrf_token" value="${window.modernFeedManager?.getCSRFToken?.() || ''}">\n          </form>`;

      section.innerHTML = formHtml;
      const listEl = document.getElementById(listId);

      if (comments.length) {
        comments.forEach((c) => {
          addCommentToModalUI(c, postId);
        });
      } else {
        listEl.innerHTML = '<p class="text-muted" data-empty-msg>Sé el primero en comentar esta publicación.</p>';
      }
    })
    .catch(() => {
      section.innerHTML = '<p class="text-muted">Error al cargar comentarios</p>';
    });
}

function deleteComment(commentId, postId) {
  if (!confirm('¿Estás seguro de que quieres eliminar este comentario?')) return;
  fetch(`/feed/comment/delete/${commentId}`, {
    method: 'POST',
    headers: { 'X-CSRFToken': window.modernFeedManager?.getCSRFToken?.() || '' },
  })
    .then((r) => {
      if (r.ok) {
        const el = document.querySelector(`[data-comment-id="${commentId}"]`);
        if (el) el.remove();
        updateCommentCount(postId, -1);
        window.modernFeedManager?.showToast?.('Comentario eliminado', 'success');
      } else {
        window.modernFeedManager?.showToast?.('Error al eliminar comentario', 'error');
      }
    })
    .catch((err) => {
      console.error(err);
      window.modernFeedManager?.showToast?.('Error de conexión', 'error');
    });
}



// Handle modal gallery interactions
document.addEventListener('click', (e) => {
  if (e.target.matches('.modal-gallery-image')) {
    const container = e.target.closest('.facebook-gallery-modal');
    if (container) {
      const postId = container.dataset.postId;
      const images = JSON.parse(container.dataset.images);
      const clickedSrc = e.target.src;
      const index = images.findIndex(img => e.target.src.includes(img.split('/').pop()));
      
      if (window.modernFeedManager) {
        window.modernFeedManager.openImageModal(clickedSrc, index >= 0 ? index : 0, postId, e);
      }
    }
  }
});

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

function initFabButton() {
  const container = document.getElementById('fab-container');
  const mainBtn = document.getElementById('fab-main');
  if (!container || !mainBtn) return;

  mainBtn.addEventListener('click', function () {
    const isActive = container.classList.toggle('active');
    mainBtn.textContent = isActive ? '×' : '+';

    container.querySelectorAll('.fab-sub').forEach((btn, i) => {
      btn.style.transform = isActive
        ? `translateX(-${(i + 1) * 60}px)`
        : 'translateX(0)';
      btn.classList.toggle('d-none', !isActive);
    });
  });
}

// Initialize the modern feed manager
let modernFeedManager;

function initModernFeedManager() {
  modernFeedManager = new ModernFeedManager();
  window.modernFeedManager = modernFeedManager;
  initFabButton();
}

// Initialization handled in main.js
window.initModernFeedManager = initModernFeedManager;


// Export for global access
window.modernFeedManager = modernFeedManager;
window.openImageModal = openImageModal;
window.editPost = editPost;
window.deletePost = deletePost;
window.reportPost = reportPost;
window.copyPostLink = copyPostLink;
window.savePost = savePost;
window.initFabButton = initFabButton;
window.initPhotoComments = initPhotoComments;
window.deleteComment = deleteComment;
