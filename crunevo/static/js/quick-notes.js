(function () {
  const portal = document.getElementById('ps-portals') || document.body;
  const modalEl = document.getElementById('quickNotesModal');
  if (modalEl && modalEl.parentElement !== portal) {
    portal.appendChild(modalEl);
  }

  const modal = modalEl ? new bootstrap.Modal(modalEl, { backdrop: 'static', keyboard: true }) : null;

  document.getElementById('btn-quick-notes')?.addEventListener('click', (e) => {
    e.preventDefault?.();
    modal?.show();
    setTimeout(() => document.getElementById('qn-text')?.focus(), 100);
  });

  const save = async () => {
    const payload = {
      content: document.getElementById('qn-text')?.value.trim() || '',
      tags: (document.getElementById('qn-tags')?.value || '')
        .split(',')
        .map(s => s.trim())
        .filter(Boolean),
      show_on_login: document.getElementById('qn-show-on-login')?.checked || false
    };
    if (!payload.content) {
      return;
    }

    const res = await fetch('/api/personal-space/quick-notes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      console.error('QuickNotes save failed', err);
      return alert(err.error || 'No se pudo guardar la nota');
    }

    modal?.hide();
    if (window.showNotification) {
      window.showNotification('Nota guardada', 'success');
    } else {
      alert('Nota guardada');
    }
  };

  document.getElementById('qn-save')?.addEventListener('click', save);
  document.getElementById('qn-text')?.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
      save();
    }
  });
})();

