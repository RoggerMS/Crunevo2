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

  window.deleteComment = deleteComment;
  window.initPhotoComments = initPhotoComments; // Initialization handled in main.js
})();
