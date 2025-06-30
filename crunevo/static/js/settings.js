function initSettingsPage() {
  document.querySelectorAll('.settings-form').forEach((form) => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const resp = await csrfFetch(form.action, {
        method: 'POST',
        body: new FormData(form),
      });
      if (resp.ok) {
        showToast('Cambios guardados');
      } else {
        showToast('Error al guardar', { delay: 5000 });
      }
    });
  });
}
window.initSettingsPage = initSettingsPage;

