function initFeedToggle() {
  const noteBtn = document.getElementById('toggleNote');
  const imageBtn = document.getElementById('toggleImage');
  const noteForm = document.getElementById('noteForm');
  const imageForm = document.getElementById('imageForm');
  if (!noteBtn || !imageBtn) return;

  noteBtn.addEventListener('click', () => {
    noteForm.classList.remove('tw-hidden');
    imageForm.classList.add('tw-hidden');
  });

  imageBtn.addEventListener('click', () => {
    imageForm.classList.remove('tw-hidden');
    noteForm.classList.add('tw-hidden');
  });
}
