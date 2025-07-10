(function() {
  function initPhotoComments() {
    const section = document.getElementById('comment-section');
    if (!section) return;

    const postId = section.dataset.postId;
    const photoIndex = section.dataset.photoIndex;

    fetch(`/feed/api/comments/${postId}`)
      .then(r => r.json())
      .then(comments => {
        const listId = `commentsList-${postId}`;
        const formHtml = `\n          <div class="comments-list" id="${listId}"></div>\n          <form class="comment-form d-flex align-items-center mt-3" data-post-id="${postId}" onsubmit="submitComment(event, '${postId}')">\n            <img src="${window.CURRENT_USER?.avatar || '/static/img/default.png'}" alt="avatar" class="rounded-circle me-2" style="width:32px;height:32px;object-fit:cover;">\n            <div class="flex-grow-1 position-relative">\n              <input type="text" class="form-control comment-input rounded-pill" placeholder="Escribe un comentario..." name="body" style="padding-right:40px;">\n              <button type="submit" class="btn position-absolute end-0 top-50 translate-middle-y me-2" style="border:none;background:none;color:#1877F2;" disabled>\n                <i class="bi bi-send-fill"></i>\n              </button>\n            </div>\n            <input type="hidden" name="csrf_token" value="${window.modernFeedManager?.getCSRFToken?.() || ''}">\n          </form>`;

        section.innerHTML = formHtml;
        const listEl = document.getElementById(listId);

        if (comments.length) {
          comments.forEach(c => {
            addCommentToModal(c, postId);
          });
        } else {
          listEl.innerHTML = '<p class="text-muted" data-empty-msg>Sé el primero en comentar esta publicación.</p>';
        }
      })
      .catch(() => {
        section.innerHTML = '<p class="text-muted">Error al cargar comentarios</p>';
      });
  }
  function openCommentsModal(postId) {
    const modalEl = document.getElementById(`commentsModal-${postId}`);
    if (!modalEl) return;
    const modal = new bootstrap.Modal(modalEl, { backdrop: 'static', keyboard: true });
    modal.show();
    setTimeout(() => {
      const input = modalEl.querySelector('.comment-input');
      if (input) input.focus();
    }, 300);
  }

  function submitComment(event, postId) {
    event.preventDefault();
    const form = event.target;
    const input = form.querySelector('.comment-input');
    const submitBtn = form.querySelector('button[type="submit"]');
    const body = input.value.trim();
    if (!body) return;

    submitBtn.disabled = true;
    input.disabled = true;

    const formData = new FormData();
    formData.append('body', body);
    formData.append('csrf_token', window.modernFeedManager?.getCSRFToken?.() || '');

    fetch(`/feed/comment/${postId}`, {
      method: 'POST',
      body: formData
    })
    .then(r => {
      if (r.status === 202) {
        window.modernFeedManager?.showToast?.('Comentario pendiente de aprobación', 'info');
        input.value = '';
      } else if (r.ok) {
        return r.json();
      } else {
        throw new Error('Error al agregar comentario');
      }
    })
    .then(data => {
      if (data) {
        addCommentToModal(data, postId);
        input.value = '';
        updateCommentCount(postId, 1);
        window.modernFeedManager?.showToast?.('Comentario agregado', 'success');
      }
    })
    .catch(err => {
      console.error(err);
      window.modernFeedManager?.showToast?.('Error al agregar comentario', 'error');
    })
    .finally(() => {
      submitBtn.disabled = false;
      input.disabled = false;
    });
  }

  function addCommentToModal(comment, postId) {
    const list = document.getElementById(`commentsList-${postId}`);
    if (!list) return;
    const html = `
      <div class="comment-item mb-3" data-comment-id="${comment.id}">
        <div class="d-flex">
          <img src="${comment.avatar || '/static/img/default.png'}" alt="${comment.author}" class="rounded-circle me-2" style="width:32px;height:32px;object-fit:cover;">
          <div class="flex-grow-1">
            <div class="comment-bubble">
              <strong class="comment-author">${comment.author}</strong>
              <p class="comment-text mb-1">${comment.body}</p>
            </div>
            <div class="comment-meta d-flex align-items-center gap-3">
              <small class="text-muted">ahora</small>
              <button class="btn btn-link btn-sm p-0 text-muted">Responder</button>
              <button class="btn btn-link btn-sm p-0 text-danger" onclick="deleteComment('${comment.id}', '${postId}')">Eliminar</button>
            </div>
          </div>
        </div>
      </div>`;
    list.insertAdjacentHTML('beforeend', html);
  }

  function deleteComment(commentId, postId) {
    if (!confirm('¿Estás seguro de que quieres eliminar este comentario?')) return;
    fetch(`/feed/comment/delete/${commentId}`, {
      method: 'POST',
      headers: { 'X-CSRFToken': window.modernFeedManager?.getCSRFToken?.() || '' }
    })
    .then(r => {
      if (r.ok) {
        const el = document.querySelector(`[data-comment-id="${commentId}"]`);
        if (el) el.remove();
        updateCommentCount(postId, -1);
        window.modernFeedManager?.showToast?.('Comentario eliminado', 'success');
      } else {
        window.modernFeedManager?.showToast?.('Error al eliminar comentario', 'error');
      }
    })
    .catch(err => {
      console.error(err);
      window.modernFeedManager?.showToast?.('Error de conexión', 'error');
    });
  }

  function updateCommentCount(postId, inc) {
    const btn = document.querySelector(`[data-post-id="${postId}"].comment-btn`);
    if (!btn) return;
    const countSpan = btn.querySelector('.action-count');
    if (!countSpan) return;
    const current = parseInt(countSpan.textContent) || 0;
    const newVal = Math.max(0, current + inc);
    countSpan.textContent = newVal > 0 ? newVal : '';
  }

  window.openCommentsModal = openCommentsModal;
  window.submitComment = submitComment;
  window.deleteComment = deleteComment;

  document.addEventListener('DOMContentLoaded', initPhotoComments);
})();
