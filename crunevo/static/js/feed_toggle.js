function initFeedToggle() {
  const noteBtn = document.getElementById('toggleNote');
  const imageBtn = document.getElementById('toggleImage');
  const noteForm = document.getElementById('noteForm');
  const imageForm = document.getElementById('imageForm');
  if (!noteBtn || !imageBtn) return;

  noteBtn.addEventListener('click', () => {
    noteForm.classList.remove('d-none');
    imageForm.classList.add('d-none');
  });

  imageBtn.addEventListener('click', () => {
    imageForm.classList.remove('d-none');
    noteForm.classList.add('d-none');
  });
}
