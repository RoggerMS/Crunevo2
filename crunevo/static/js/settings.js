function initSettingsPage() {
  document.querySelectorAll('.settings-form').forEach((form) => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const resp = await csrfFetch(form.action, {
        method: 'POST',
        body: new FormData(form),
      });
      if (resp.ok) {
        let data = {};
        try {
          data = await resp.clone().json();
        } catch {
          // ignore
        }
        showToast('Cambios guardados');
        if (data.changed_username) {
          window.location.reload();
        }
      } else {
        let msg = 'Error al guardar';
        try {
          const data = await resp.json();
          if (data.error) msg = data.error;
        } catch {
          // ignore
        }
        showToast(msg, { delay: 5000 });
      }
    });
  });

  const usernameInput = document.getElementById('username');
  const feedback = document.getElementById('usernameFeedback');
  if (usernameInput && feedback) {
    usernameInput.addEventListener('input', async () => {
      const value = usernameInput.value.trim();
      if (!value || value === usernameInput.dataset.current) {
        feedback.textContent = '';
        feedback.classList.remove('text-success', 'text-danger');
        return;
      }
      const resp = await fetch(
        `/api/check_username?username=${encodeURIComponent(value)}`
      );
      if (resp.ok) {
        const data = await resp.json();
        if (data.available) {
          feedback.textContent = '✅ Nombre disponible';
          feedback.classList.remove('text-danger');
          feedback.classList.add('text-success');
        } else {
          feedback.textContent = '❌ No disponible';
          feedback.classList.remove('text-success');
          feedback.classList.add('text-danger');
        }
      } else {
        feedback.textContent = 'Error al verificar';
        feedback.classList.remove('text-success');
        feedback.classList.add('text-danger');
      }
    });
  }

  const toggle = document.getElementById('notifSoundToggle');
  if (toggle) {
    toggle.checked = localStorage.getItem('notifSound') !== 'off';
    toggle.addEventListener('change', () => {
      const on = toggle.checked;
      localStorage.setItem('notifSound', on ? 'on' : 'off');
      if (window.CRUNEVO_CONFIG) {
        window.CRUNEVO_CONFIG.soundEnabled = on;
      }
    });
  }
}
window.initSettingsPage = initSettingsPage;

