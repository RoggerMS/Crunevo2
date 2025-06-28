
function shareContent(title, url) {
  if (navigator.share) {
    navigator.share({
      title: title,
      url: url
    }).catch(console.error);
  } else {
    // Fallback: copy to clipboard
    navigator.clipboard.writeText(url).then(() => {
      showToast('Enlace copiado al portapapeles', 'success');
    }).catch(() => {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = url;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      showToast('Enlace copiado al portapapeles', 'success');
    });
  }
}

function showToast(message, type = 'info') {
  const toastContainer = document.querySelector('.toast-container') || createToastContainer();
  
  const toast = document.createElement('div');
  toast.className = `toast align-items-center text-white bg-${type} border-0`;
  toast.setAttribute('role', 'alert');
  toast.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">${message}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>
  `;
  
  toastContainer.appendChild(toast);
  
  const bsToast = new bootstrap.Toast(toast);
  bsToast.show();
  
  toast.addEventListener('hidden.bs.toast', () => {
    toast.remove();
  });
}

function createToastContainer() {
  const container = document.createElement('div');
  container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
  container.style.zIndex = '1080';
  document.body.appendChild(container);
  return container;
}

// Add share buttons to posts and notes
document.addEventListener('DOMContentLoaded', function() {
  // Add share buttons to existing content
  addShareButtons();
});

function addShareButtons() {
  // Add to post cards
  document.querySelectorAll('.post-card').forEach(card => {
    if (!card.querySelector('.share-btn')) {
      const actionsDiv = card.querySelector('.card-footer') || card.querySelector('.d-flex.gap-2');
      if (actionsDiv) {
        const shareBtn = document.createElement('button');
        shareBtn.className = 'btn btn-outline-secondary btn-sm share-btn';
        shareBtn.innerHTML = '<i class="bi bi-share"></i>';
        shareBtn.title = 'Compartir';
        
        const postId = card.dataset.postId;
        const postTitle = card.querySelector('.card-title, h5, h6')?.textContent || 'Publicación en Crunevo';
        
        shareBtn.onclick = () => shareContent(postTitle, `${window.location.origin}/post/${postId}`);
        actionsDiv.appendChild(shareBtn);
      }
    }
  });
  
  // Add to note cards
  document.querySelectorAll('.note-card').forEach(card => {
    if (!card.querySelector('.share-btn')) {
      const actionsDiv = card.querySelector('.card-footer') || card.querySelector('.d-flex.gap-2');
      if (actionsDiv) {
        const shareBtn = document.createElement('button');
        shareBtn.className = 'btn btn-outline-secondary btn-sm share-btn';
        shareBtn.innerHTML = '<i class="bi bi-share"></i>';
        shareBtn.title = 'Compartir';
        
        const noteId = card.dataset.noteId;
        const noteTitle = card.querySelector('.card-title, h5, h6')?.textContent || 'Apunte en Crunevo';
        
        shareBtn.onclick = () => shareContent(noteTitle, `${window.location.origin}/notes/${noteId}`);
        actionsDiv.appendChild(shareBtn);
      }
    }
  });
}
