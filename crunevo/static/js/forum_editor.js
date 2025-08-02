function initForumEditor(selector) {
  const container = document.querySelector(selector);
  if (!container) return null;
  if (container._quill) return container._quill;
  const quill = new Quill(container, {
    theme: 'snow',
    modules: {
      toolbar: [
        ['bold', 'italic', 'underline'],
        [{ header: [1, 2, 3, false] }],
        [{ list: 'ordered' }, { list: 'bullet' }],
        ['link', 'image'],
        ['clean'],
      ],
    },
  });
  container._quill = quill;

  quill.getModule('toolbar').addHandler('image', () => selectLocalImage(quill));
  quill.root.addEventListener('drop', (e) => handleDrop(e, quill));
  quill.root.addEventListener('paste', (e) => handlePaste(e, quill));
  quill.root.addEventListener('click', (e) => {
    if (e.target && e.target.tagName === 'IMG') {
      e.target.classList.toggle('img-expanded');
    }
  });
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
    uploadImageFile(file, quill);
  };
  input.click();
}

function uploadImageFile(file, quill) {
  if (!file || !file.type.startsWith('image/')) return;
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
        quill.setSelection(range.index + 1);
        const img = quill.root.querySelector(`img[src="${data.url}"]`);
        if (img) {
          img.classList.add('resizable-image');
          img.setAttribute('data-bs-toggle', 'tooltip');
          img.setAttribute('data-bs-placement', 'top');
          img.setAttribute(
            'title',
            'Puedes hacer clic para ajustar el tamaño o mover esta imagen'
          );
          if (typeof bootstrap !== 'undefined') {
            const tip = bootstrap.Tooltip.getOrCreateInstance(img);
            tip.show();
            setTimeout(() => tip.hide(), 3000);
          }
        }
      }
    });
}

function handleDrop(e, quill) {
  e.preventDefault();
  if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length) {
    uploadImageFile(e.dataTransfer.files[0], quill);
  }
}

function handlePaste(e, quill) {
  const items = e.clipboardData.items;
  for (const item of items) {
    if (item.kind === 'file') {
      e.preventDefault();
      const file = item.getAsFile();
      uploadImageFile(file, quill);
    }
  }
}

// Initialization handled in main.js
window.initForumEditor = initForumEditor;
