// Comment modal utilities

function openCommentsModal(postId) {
  const modalElement = document.getElementById(`commentsModal-${postId}`);
  if (!modalElement) return;
  
  const modal = new bootstrap.Modal(modalElement);
  
  // Verificar si necesitamos actualizar los comentarios
  const commentsList = modalElement.querySelector(`#commentsList-${postId}`);
  if (commentsList) {
    // Opcionalmente, podemos cargar los comentarios más recientes desde el servidor
    // Solo si el modal no está ya abierto
    if (!modalElement.classList.contains('show')) {
      // Mostrar indicador de carga
      const loadingIndicator = document.createElement('div');
      loadingIndicator.className = 'text-center my-2';
      loadingIndicator.innerHTML = '<div class="spinner-border spinner-border-sm text-primary" role="status"><span class="visually-hidden">Cargando...</span></div> Actualizando comentarios...';
      
      // Si hay un botón de cargar más comentarios, insertamos antes de él
      const loadMoreBtn = commentsList.nextElementSibling?.querySelector('.load-more-comments');
      if (loadMoreBtn) {
        loadMoreBtn.parentNode.insertBefore(loadingIndicator, loadMoreBtn);
      } else {
        commentsList.insertAdjacentElement('afterend', loadingIndicator);
      }
      
      // Cargar comentarios actualizados
      fetch(`/feed/api/comments/${postId}`)
        .then(response => response.json())
        .then(data => {
          // Actualizar contador de comentarios en el modal
          const commentCountElement = modalElement.querySelector('.modal-stat-item:nth-child(2) span');
          if (commentCountElement) {
            commentCountElement.textContent = `${data.comments.length} comentarios`;
          }
          
          // Actualizar lista de comentarios si hay nuevos
          if (data.comments && data.comments.length > 0) {
            // Limpiar lista actual y agregar los nuevos comentarios
            commentsList.innerHTML = '';
            data.comments.forEach(comment => {
              const commentHTML = `
                <div class="comment-item">
                  <img src="${comment.author.avatar_url || '/static/img/default.png'}"
                       alt="${comment.author.username || 'Usuario'}"
                       class="comment-avatar">
                  <div class="comment-content">
                    <div class="comment-box">
                      <div class="comment-author">${comment.author.username || 'Usuario eliminado'}</div>
                      <div class="comment-text">${comment.body}</div>
                    </div>
                    <div class="comment-meta">
                      <small class="text-muted">${comment.timestamp_text || 'ahora'}</small>
                      <button class="btn btn-link btn-sm p-0 ms-2 text-muted">Responder</button>
                    </div>
                  </div>
                </div>
              `;
              commentsList.insertAdjacentHTML('beforeend', commentHTML);
            });
          }
        })
        .catch(error => {
          console.error('Error al cargar comentarios:', error);
        })
        .finally(() => {
          // Eliminar indicador de carga
          loadingIndicator.remove();
        });
    }
  }
  
  // Mostrar el modal
  modal.show();

  // Focus en el campo de comentario después de abrir el modal
  setTimeout(() => {
    const commentInput = modalElement.querySelector('.comment-input');
    if (commentInput) {
      commentInput.focus();
    }
  }, 300);
}

function submitModalComment(event, postId) {
  event.preventDefault();
  const form = event.target;
  const input = form.querySelector('.comment-input');
  const submitBtn = form.querySelector('button[type="submit"]');
  const body = input.value.trim();

  if (!body) return;

  // Disable submit button
  submitBtn.disabled = true;

  const formData = new FormData();
  formData.append('body', body);
  formData.append('csrf_token', form.querySelector('[name="csrf_token"]').value);

  fetch(`/feed/comment/${postId}`, {
    method: 'POST',
    body: formData,
  })
    .then(async (response) => {
      if (response.status === 202) {
        window.modernFeedManager?.showToast(
          'Comentario pendiente de aprobación',
          'info'
        );
        input.value = '';
      } else if (response.ok) {
        return response.json();
      } else {
        const data = await response.json().catch(() => ({}));
        const msg =
          data.error ||
          (response.status === 403
            ? 'Comentarios deshabilitados'
            : 'Error al agregar comentario');
        throw new Error(msg);
      }
    })
    .then((data) => {
      if (data) {
        addCommentToModalUI(data, postId);
        input.value = '';
        input.style.height = 'auto';
        window.modernFeedManager?.showToast('Comentario agregado', 'success');

        // Update comment count in main feed
        if (typeof updateCommentCount === 'function') {
          updateCommentCount(postId, 1);
        }
      }
    })
    .catch((error) => {
      console.error('Error submitting comment:', error);
      window.modernFeedManager?.showToast(
        error.message || 'Error al agregar comentario',
        'error'
      );
    })
    .finally(() => {
      submitBtn.disabled = false;
    });
}

function addCommentToModalUI(comment, postId) {
  const commentsList = document.getElementById(`commentsList-${postId}`);
  if (!commentsList) return;

  // Check if we're in the new Facebook-style modal
  const isNewModal = document.getElementById('facebookModal') || document.querySelector('.facebook-modal-container');
  
  let commentHTML;
  if (isNewModal) {
    // New Facebook-style comment structure
    commentHTML = `
      <div class="comment-item">
        <img src="${comment.avatar || '/static/img/default.png'}"
             alt="${comment.author}"
             class="comment-avatar">
        <div class="comment-content">
          <div class="comment-box">
            <div class="comment-author">${comment.author}</div>
            <div class="comment-text">${comment.body}</div>
          </div>
          <div class="comment-meta">
            <small class="text-muted">ahora</small>
            <button class="btn btn-link btn-sm p-0 ms-2 text-muted">Responder</button>
          </div>
        </div>
      </div>
    `;
  } else {
    // Old Bootstrap modal structure
    commentHTML = `
      <div class="comment-item d-flex mb-3">
        <img src="${comment.avatar || '/static/img/default.png'}"
             alt="${comment.author}"
             class="rounded-circle me-2"
             style="width: 32px; height: 32px; object-fit: cover;">
        <div class="flex-grow-1">
          <div class="comment-bubble bg-light rounded-3 p-2">
            <div class="comment-author fw-semibold small">${comment.author}</div>
            <div class="comment-text">${comment.body}</div>
          </div>
          <div class="comment-meta mt-1">
            <small class="text-muted">ahora</small>
            <button class="btn btn-link btn-sm p-0 ms-2 text-muted">Responder</button>
          </div>
        </div>
      </div>
    `;
  }

  // Remove empty comments message if it exists
  const emptyComments = commentsList.querySelector('.empty-comments');
  if (emptyComments) {
    emptyComments.remove();
  }

  commentsList.insertAdjacentHTML('beforeend', commentHTML);

  // Scroll to bottom within the modal's scrollable area
  const scrollContainer = commentsList.closest('.modal-scrollable-content');
  if (scrollContainer) {
    scrollContainer.scrollTop = scrollContainer.scrollHeight;
  }
}

let commentsInitialized = false;
function initCommentModals() {
  if (commentsInitialized) return;
  commentsInitialized = true;
  document.addEventListener('input', (e) => {
    if (
      e.target.classList.contains('comment-input') &&
      e.target.closest('[id^="commentsModal-"]')
    ) {
      const form = e.target.closest('.comment-form');
      const submitBtn = form?.querySelector('button[type="submit"]');
      if (submitBtn) {
        submitBtn.disabled = !e.target.value.trim();
      }
      e.target.style.height = 'auto';
      e.target.style.height = `${e.target.scrollHeight}px`;
    }
  });
}

// Expose globally
window.openCommentsModal = openCommentsModal;
window.submitModalComment = submitModalComment;
window.addCommentToModalUI = addCommentToModalUI;
window.initCommentModals = initCommentModals;
