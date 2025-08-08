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
    this.prevUrlStack = [];
    this.handlePopState = this.handlePopState.bind(this);
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
    const selector = '.post-skeleton';
    document.querySelectorAll(selector).forEach(skeleton => {
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
        body: formData,
        headers: { 'Accept': 'application/json' }
      });
      const data = await response.json();

      if (response.ok) {
        this.showToast('¡Publicación creada exitosamente! 🎉', 'success');
        form.reset();
        this.clearImagePreview();
        this.updatePostButtonState();

        const modal = bootstrap.Modal.getInstance(document.getElementById('crearPublicacionModal'));
        if (modal) modal.hide();

        const container = document.getElementById('feedContainer');
        if (container && data.html) {
          container.insertAdjacentHTML('afterbegin', data.html);
          this.initPostInteractions();
          this.initCommentSystem();
        }
      } else {
        this.showToast('Error al publicar: ' + (data.error || 'Error desconocido'), 'error');
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
    
    // Copy link button in dropdown menu
    document.addEventListener('click', (e) => {
      if (e.target.matches('.copy-link-btn') || e.target.closest('.copy-link-btn')) {
        e.preventDefault();
        const btn = e.target.closest('.copy-link-btn');
        const postId = btn.dataset.postId;
        if (postId) {
          const shareUrl = `${window.location.origin}/feed/post/${postId}`;
          this.copyToClipboard(shareUrl);
          this.showToast('¡Enlace copiado!', 'success');
          // Cerrar el dropdown después de copiar
          const dropdown = btn.closest('.dropdown-menu');
          if (dropdown) {
            bootstrap.Dropdown.getInstance(dropdown)?.hide();
          }
        }
      }
    });
    
    // Save post button in dropdown menu
    document.addEventListener('click', (e) => {
      if (e.target.matches('.save-post-btn') || e.target.closest('.save-post-btn')) {
        e.preventDefault();
        const btn = e.target.closest('.save-post-btn');
        const postId = btn.dataset.postId;
        if (postId) {
          // Actualizar el estado visual inmediatamente (optimista)
          const isSaved = btn.classList.contains('active');
          btn.classList.toggle('active');
          const icon = btn.querySelector('i');
          if (icon) {
            icon.classList.toggle('bi-bookmark', isSaved);
            icon.classList.toggle('bi-bookmark-fill', !isSaved);
          }
          btn.textContent = isSaved ? ' Guardar publicación' : ' Guardado';
          btn.prepend(icon); // Volver a añadir el icono al principio
          
          // También actualizar el botón de guardar en la tarjeta de publicación si existe
          const saveBtn = document.querySelector(`.save-btn[data-post-id="${postId}"]`);
          if (saveBtn) {
            saveBtn.classList.toggle('active', !isSaved);
            const saveBtnIcon = saveBtn.querySelector('i');
            if (saveBtnIcon) {
              saveBtnIcon.classList.toggle('bi-bookmark', isSaved);
              saveBtnIcon.classList.toggle('bi-bookmark-fill', !isSaved);
            }
          }
          
          // Enviar la solicitud al servidor
          this.fetchWithCSRF(`/feed/save/${postId}`, {
            method: 'POST'
          })
          .then(response => response.json())
          .then(data => {
            this.showToast(
              data.saved ? 'Publicación guardada' : 'Publicación removida de guardados',
              data.saved ? 'success' : 'info'
            );
          })
          .catch(error => {
            console.error('Error al guardar/remover publicación:', error);
            // Revertir cambios visuales en caso de error
            btn.classList.toggle('active');
            if (icon) {
              icon.classList.toggle('bi-bookmark', !isSaved);
              icon.classList.toggle('bi-bookmark-fill', isSaved);
            }
            btn.textContent = !isSaved ? ' Guardar publicación' : ' Guardado';
            btn.prepend(icon);
            
            if (saveBtn) {
              saveBtn.classList.toggle('active', isSaved);
              const saveBtnIcon = saveBtn.querySelector('i');
              if (saveBtnIcon) {
                saveBtnIcon.classList.toggle('bi-bookmark', !isSaved);
                saveBtnIcon.classList.toggle('bi-bookmark-fill', isSaved);
              }
            }
            
            this.showToast('Error al procesar la solicitud', 'error');
          });
          
          // Cerrar el dropdown después de guardar
          const dropdown = btn.closest('.dropdown-menu');
          if (dropdown) {
            bootstrap.Dropdown.getInstance(dropdown)?.hide();
          }
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
        this.hideReactionPanel(likeBtn);
      }
    });

    // Long press for mobile/desktop
    document.addEventListener('touchstart', (e) => {
      const btn = e.target.closest('.like-btn');
      if (!btn) return;
      e.preventDefault();
      btn._longPress = false;
      btn._pressTimer = setTimeout(() => {
        btn._longPress = true;
        this.showReactionPanel(btn);
      }, 500);
    }, { passive: false });

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
      e.preventDefault();
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
      
      // Check if the click was specifically on the comments count
      const commentsCount = e.target.closest('.comments-count');
      if (commentsCount) {
        const postId = target.dataset.postId;
        if (postId) {
          // Open comments modal
          if (typeof openCommentsModal === 'function') {
            openCommentsModal(postId);
          }
        }
        return;
      }
      
      // Handle reactions count click (original functionality)
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
    
    // Direct click on comments count (outside of post-reactions-count)
    document.addEventListener('click', (e) => {
      const commentsCount = e.target.closest('.comments-count');
      if (!commentsCount) return;
      
      // If we're not inside a post-reactions-count, we need to get the postId differently
      const postCard = commentsCount.closest('.post-card');
      if (!postCard) return;
      
      const postId = postCard.dataset.postId;
      if (!postId) return;
      
      // Open comments modal
      if (typeof openCommentsModal === 'function') {
        openCommentsModal(postId);
      }
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
    window.showReactionPanel(btn);
  }

  hideReactionPanel(btn) {
    window.hideReactionPanel(btn);
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
  
  // Utility to copy text to clipboard
  copyToClipboard(text) {
    // Usar la API moderna del portapapeles si está disponible
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).catch(err => {
        console.error('Error al copiar al portapapeles:', err);
        this.fallbackCopyToClipboard(text);
      });
    } else {
      // Fallback para contextos no seguros o navegadores antiguos
      this.fallbackCopyToClipboard(text);
    }
  }
  
  // Método alternativo para copiar al portapapeles
  fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    
    // Hacer que el textarea esté fuera de la pantalla
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    
    // Preservar la posición de desplazamiento original
    const scrollPos = {
      top: window.pageYOffset || document.documentElement.scrollTop,
      left: window.pageXOffset || document.documentElement.scrollLeft
    };
    
    textArea.focus();
    textArea.select();
    
    let success = false;
    try {
      success = document.execCommand('copy');
    } catch (err) {
      console.error('Error al ejecutar comando de copia:', err);
    }
    
    document.body.removeChild(textArea);
    
    // Restaurar la posición de desplazamiento original
    window.scrollTo(scrollPos.left, scrollPos.top);
    
    return success;
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
    this.restoreFeedUrlIfPhotoPath();
  }

  handleModalKeydown(e) {
    if (!this.currentPostId) return;
    if (e.key === 'Escape') {
      this.closeModal();
    } else if (e.key === 'ArrowRight') {
      this.nextImage();
    } else if (e.key === 'ArrowLeft') {
      this.prevImage();
    }
  }

  restoreFeedUrlIfPhotoPath() {
    const path = window.location.pathname;
    if (/^\/feed\/post\/\d+\/photo\/\d+/.test(path)) {
      window.history.replaceState(null, '', '/feed');
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
    
    this.createImageModal(postId);
    this.prevUrlStack.push(window.location.href);
    setTimeout(() => this.updateModalImage(), 50);
    window.history.pushState({ modal: true }, '', `/feed/post/${postId}/photo/${index + 1}`);
    if (this.prevUrlStack.length === 1) {
      window.addEventListener('popstate', this.handlePopState);
    }
  }

  // Create full-screen image modal
  createImageModal(postId) {
    this.closeModal();

    const modalWrapper = document.createElement('div');
    modalWrapper.id = 'facebookModal';
    modalWrapper.className = 'image-modal hidden';
    modalWrapper.setAttribute('role', 'dialog');
    modalWrapper.setAttribute('tabindex', '-1');

    modalWrapper.addEventListener('click', (e) => {
      if (e.target.id === 'facebookModal') {
        this.closeModal();
      }
    });

    const modalContainer = document.createElement('div');
    modalContainer.className = 'facebook-modal-container image-with-comments';

    const hasMultiple = this.imageList && this.imageList.length > 1;
    const innerHTML = `
      <div class="facebook-modal-image-section">
        <div class="modal-image-container">
          <img id="modalMainImage" src="" alt="Imagen del post" class="modal-main-image">
        </div>

        <div class="modal-top-controls">
          <div class="dropdown">
            <button class="modal-control-btn" type="button" data-bs-toggle="dropdown" aria-expanded="false" title="Más opciones" aria-label="Más opciones">
              <i class="bi bi-three-dots"></i>
            </button>
            <ul class="dropdown-menu dropdown-menu-dark dropdown-menu-end">
              <li><a class="dropdown-item" href="#" onclick="interestPost('${postId}')"><i class="bi bi-heart me-2"></i> Me interesa</a></li>
              <li><a class="dropdown-item" href="#" onclick="notInterestedPost('${postId}')"><i class="bi bi-x-circle me-2"></i> No me interesa</a></li>
              <li><hr class="dropdown-divider"></li>
              <li><a class="dropdown-item" href="#" onclick="copyPostLink('${postId}')"><i class="bi bi-link-45deg me-2"></i> Copiar enlace</a></li>
            </ul>
          </div>
          <button class="modal-control-btn" onclick="modernFeedManager.zoomIn()" title="Aumentar" aria-label="Aumentar Zoom"><i class="bi bi-plus-lg"></i></button>
          <button class="modal-control-btn" onclick="modernFeedManager.zoomOut()" title="Reducir" aria-label="Reducir Zoom"><i class="bi bi-dash-lg"></i></button>
          <a id="modalDownloadLink" href="#" download class="modal-control-btn" title="Descargar" aria-label="Descargar Imagen"><i class="bi bi-download"></i></a>
          <button class="modal-control-btn" onclick="modernFeedManager.closeModal()" title="Cerrar (Esc)" aria-label="Cerrar"><i class="bi bi-x-lg"></i></button>
        </div>

        ${hasMultiple ? `
          <button type="button" class="modal-nav prev" onclick="modernFeedManager.prevImage()" title="Anterior (←)" aria-label="Anterior"><i class="bi bi-chevron-left"></i></button>
          <button type="button" class="modal-nav next" onclick="modernFeedManager.nextImage()" title="Siguiente (→)" aria-label="Siguiente"><i class="bi bi-chevron-right"></i></button>
        ` : ''}
      </div>
      <div class="facebook-modal-info-panel" id="facebookModalInfoPanel">
        <div class="modal-loading"><div class="spinner-border"></div></div>
      </div>
    `;

    modalContainer.innerHTML = innerHTML;
    modalWrapper.appendChild(modalContainer);
    document.body.appendChild(modalWrapper);
    document.body.classList.add('photo-modal-open');

    setTimeout(() => {
      modalWrapper.classList.remove('hidden');
      this.modalImageEl = document.getElementById('modalMainImage');
      if (this.modalImageEl) {
        this.modalImageEl.addEventListener('wheel', (e) => this.handleWheel(e), { passive: false });
        this.modalImageEl.addEventListener('touchstart', (e) => this.handleTouchStart(e));
        this.modalImageEl.addEventListener('touchend', (e) => this.handleTouchEnd(e));
      }
    }, 10);

    this.loadPostDataForModal(postId);
  }

  // Close image modal
  closeModal(fromPopState = false) {
    const modal = document.getElementById('facebookModal');
    if (modal) {
      modal.classList.add('hidden');
      setTimeout(() => {
        modal.remove();
        document.body.classList.remove('photo-modal-open');
      }, 300);
    }
    this.currentPostId = null;
    this.modalImageEl = null;
    this.currentScale = 1;
    this.popModalHistory(fromPopState);
  }

  handlePopState(e) {
    if (this.currentPostId) {
      this.closeModal(true);
    }
  }

  popModalHistory(fromPopState) {
    if (!fromPopState) {
      const prevUrl = this.prevUrlStack.pop() || '/feed';
      window.history.replaceState(null, '', prevUrl);
    } else {
      this.prevUrlStack.pop();
    }
    if (this.prevUrlStack.length === 0) {
      window.removeEventListener('popstate', this.handlePopState);
    }
  }

  // Image navigation and zoom controls
  nextImage() {
    if (this.currentImageIndex < this.imageList.length - 1) {
      this.currentImageIndex++;
      this.updateModalImage();
    }
  }

  prevImage() {
    if (this.currentImageIndex > 0) {
      this.currentImageIndex--;
      this.updateModalImage();
    }
  }

  updateModalImage() {
    if (!this.modalImageEl) return;
    const newSrc = this.imageList[this.currentImageIndex];
    this.modalImageEl.src = newSrc;

    const downloadLink = document.getElementById('modalDownloadLink');
    if (downloadLink) {
      downloadLink.href = newSrc;
    }

    const prevBtn = document.querySelector('.modal-nav.prev');
    const nextBtn = document.querySelector('.modal-nav.next');
    if (prevBtn) prevBtn.disabled = this.currentImageIndex === 0;
    if (nextBtn) nextBtn.disabled = this.currentImageIndex === this.imageList.length - 1;

    this.resetZoom();
  }

  handleWheel(e) {
    e.preventDefault();
    if (e.deltaY < 0) this.zoomIn();
    else this.zoomOut();
  }

  handleTouchStart(e) {
    this.touchStartX = e.touches[0].clientX;
  }

  handleTouchEnd(e) {
    this.touchEndX = e.changedTouches[0].clientX;
    this.handleSwipe();
  }

  handleSwipe() {
    const diff = this.touchEndX - this.touchStartX;
    if (diff > 50) this.prevImage();
    else if (diff < -50) this.nextImage();
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
    this.currentScale = Math.max(0.5, this.currentScale - 0.2);
    this.applyZoom();
  }

  resetZoom() {
    this.currentScale = 1;
    this.applyZoom();
  }

  loadPostDataForModal(postId) {
    fetch(`/feed/api/post/${postId}`)
      .then(r => r.json())
      .then(data => {
        const infoPanel = document.getElementById('facebookModalInfoPanel');
        if (infoPanel && data.html) {
          infoPanel.innerHTML = data.html;
          this.initCommentInput();
          this.initPostInteractions();
        }
      })
      .catch(error => {
        console.error('Error al cargar datos del modal:', error);
        const infoPanel = document.getElementById('facebookModalInfoPanel');
        if (infoPanel) {
          infoPanel.innerHTML = '<div class="text-center text-danger p-4">No se pudo cargar el contenido del post.</div>';
        }
      });
  }

  // Initialize comment input functionality
  initCommentInput() {
    const commentInputs = document.querySelectorAll('.comment-input');
    commentInputs.forEach(input => {
      const submitBtn = input.closest('.comment-form').querySelector('.comment-submit-btn');
      
      input.addEventListener('input', () => {
        if (submitBtn) {
          submitBtn.disabled = input.value.trim().length === 0;
        }
      });

      input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          const form = input.closest('.comment-form');
          if (form && input.value.trim()) {
            form.dispatchEvent(new Event('submit'));
          }
        }
      });
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

    const container = document.getElementById('feedContainer');
    if (!container) return;
    if (filter === "apuntes") {
      container.classList.add("feed-as-grid");
    } else {
      container.classList.remove("feed-as-grid");
    }

    const filterChanged = filter !== this.currentFilter;
    if (filterChanged) {
      container.innerHTML = '';
    }

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
      const text = await response.text();
      if (!response.ok) {
        console.error('Failed to load filtered feed:', response.status, text);
        throw new Error('Network response was not ok');
      }
      const data = JSON.parse(text);

      // Hide skeletons
      this.removeSkeletonPosts();

      // Update content only when HTML is not empty
      if (typeof data.html === 'string' && data.html.trim() !== '') {
        if (filterChanged) {
          container.innerHTML = data.html;
        } else {
        }

        // Reinitialize interactions
        this.initPostInteractions();
        this.initCommentSystem();
        if (typeof initNotePreviews !== 'undefined') {
          initNotePreviews();
        }

      } else {
        this.reachedEnd = true;
        this.showToast('No se encontraron publicaciones', 'info');
      }

      this.showToast(`Filtro "${filter}" aplicado`, 'info');
    } catch (error) {
      console.error('Error loading filtered feed:', error);
      this.showToast('Error al cargar contenido', 'error');
      this.removeSkeletonPosts();
      const loader = document.getElementById('feed-loader');
      if (loader) {
        loader.querySelector('.spinner-border')?.classList.add('d-none');
        loader.style.display = 'none';
      }
      const feedEnd = document.getElementById('feedEnd');
      if (feedEnd && !document.getElementById('load-error-alert')) {
        feedEnd.insertAdjacentHTML(
          'beforebegin',
          '<div id="load-error-alert" class="alert alert-danger mt-3">Error cargando publicaciones</div>'
        );
      }
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
      const container = document.getElementById('feedContainer');
      const temp = document.createElement('div');
      temp.innerHTML = data;

      if (data.trim() === '' || data.includes('no-more-posts')) {
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
        const postId = el.getAttribute('data-post-id');
        if (!postId || !container.querySelector(`[data-post-id="${postId}"]`)) {
          el.classList.add('fade-in');
          container.appendChild(el);
        }
      });
      if (typeof initNotePreviews !== "undefined") {
        initNotePreviews();
      }
      if (loader) loader.style.display = 'none';

    } catch (error) {
      console.error('Error loading more posts:', error);
      this.showToast('Error al cargar más publicaciones', 'error');
      loader?.querySelector('.spinner-border')?.classList.add('d-none');
      if (loader) loader.style.display = 'none';
      const feedEnd = document.getElementById('feedEnd');
      if (feedEnd && !document.getElementById('load-error-alert')) {
        feedEnd.insertAdjacentHTML(
          'beforebegin',
          '<div id="load-error-alert" class="alert alert-danger mt-3">Error cargando publicaciones</div>'
        );
      }
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

function setupLoadMoreComments() {
  document.body.addEventListener('click', function (event) {
    if (event.target.matches('.load-more-comments')) {
      event.preventDefault();
      const btn = event.target;
      const postId = btn.dataset.postId;
      const page = parseInt(btn.dataset.page || '1');

      btn.textContent = 'Cargando...';
      btn.disabled = true;

      fetch(`/feed/api/comments/${postId}?page=${page}`)
        .then((response) => response.json())
        .then((data) => {
          if (data.comments && data.comments.length > 0) {
            const commentsList = document.querySelector(`#commentsList-${postId}`);
            data.comments.forEach((comment) => {
              addCommentToModalUI(comment, postId);
            });

            btn.dataset.page = page + 1;
            btn.textContent = 'Ver más comentarios';
            btn.disabled = false;

            if (!data.has_more) {
              btn.remove();
            }
          } else {
            btn.remove();
          }
        })
        .catch((error) => {
          console.error('Error al cargar más comentarios:', error);
          btn.textContent = 'Error al cargar. Reintentar';
          btn.disabled = false;
        });
    }
  });
}

// Load comments for photo view
function initPhotoComments() {
  const section = document.getElementById('comment-section');
  if (!section) return;

  const postId = section.dataset.postId;

  fetch(`/feed/api/comments/${postId}`)
    .then((r) => r.json())
    .then((data) => {
      const comments = data.comments || [];
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

      if (data.has_more) {
        const loadBtn = document.createElement('button');
        loadBtn.className = 'btn btn-link btn-sm w-100 mb-3 load-more-comments';
        loadBtn.dataset.postId = postId;
        loadBtn.dataset.page = '2';
        loadBtn.textContent = 'Ver más comentarios';
        const form = section.querySelector('form');
        form.insertAdjacentElement('beforebegin', loadBtn);
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
      const selector = `[data-post-id="${postId}"]`;
      const postElement = document.querySelector(selector);
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
  setupLoadMoreComments();
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
