// Comment modal utilities

function openCommentsModal(postId) {
  const modal = new bootstrap.Modal(
    document.getElementById(`commentsModal-${postId}`)
  );
  modal.show();

  // Focus on comment input after modal opens
  setTimeout(() => {
    const commentInput = document.querySelector(
      `#commentsModal-${postId} .comment-input`
    );
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
