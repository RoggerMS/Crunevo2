function initForumEditor(selector) {
  const container = document.querySelector(selector);
  if (!container) return null;
  const quill = new Quill(container, {
    theme: 'snow',
    modules: {
      toolbar: [
        ['bold', 'italic', 'underline'],
        [{ list: 'ordered' }, { list: 'bullet' }],
        ['link', 'image'],
        ['clean'],
      ],
    },
  });

  quill.getModule('toolbar').addHandler('image', () => selectLocalImage(quill));
  const form = container.closest('form');
  if (form) {
    const input = form.querySelector('input[name="content"]');
    form.addEventListener('submit', () => {
      if (input) input.value = quill.root.innerHTML;
    });
  }
  return quill;
}

function selectLocalImage(quill) {
  const input = document.createElement('input');
  input.setAttribute('type', 'file');
  input.setAttribute('accept', 'image/*');
  input.onchange = () => {
    const file = input.files[0];
    if (!file) return;
    if (file.size > 3 * 1024 * 1024) {
      alert('Imagen demasiado grande (máx 3MB)');
      return;
    }
    const fd = new FormData();
    fd.append('file', file);
    csrfFetch('/api/upload', { method: 'POST', body: fd })
      .then((r) => r.json())
      .then((data) => {
        if (data.url) {
          const range = quill.getSelection(true);
          quill.insertEmbed(range.index, 'image', data.url);
        }
      });
  };
  input.click();
}

// Initialization handled in main.js
window.initForumEditor = initForumEditor;
