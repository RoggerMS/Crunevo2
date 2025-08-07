function initSettingsPage() {
  // Navegación entre secciones
  const navItems = document.querySelectorAll('.settings-nav-item');
  const sections = document.querySelectorAll('.settings-section');
  
  function showSection(targetSection) {
    // Ocultar todas las secciones
    sections.forEach(section => {
      section.style.display = 'none';
    });
    
    // Mostrar la sección objetivo
    const target = document.getElementById(targetSection);
    if (target) {
      target.style.display = 'block';
    }
    
    // Actualizar navegación activa
    navItems.forEach(item => {
      item.classList.remove('active');
      if (item.dataset.section === targetSection) {
        item.classList.add('active');
      }
    });
  }
  
  // Configurar navegación
  navItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const section = item.dataset.section;
      showSection(section);
      
      // Actualizar URL sin recargar
      history.pushState(null, null, `#${section}`);
    });
  });
  
  // Mostrar sección inicial basada en hash o mostrar la primera
  const initialSection = window.location.hash.slice(1) || 'personal';
  showSection(initialSection);
  
  // Manejar navegación del navegador
  window.addEventListener('popstate', () => {
    const section = window.location.hash.slice(1) || 'personal';
    showSection(section);
  });

  // Formularios de configuración
  document.querySelectorAll('.settings-form').forEach((form) => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const submitBtn = form.querySelector('button[type="submit"]');
      const originalText = submitBtn.innerHTML;
      
      // Mostrar estado de carga
      submitBtn.innerHTML = '<i class="bi bi-arrow-clockwise spin"></i> Guardando...';
      submitBtn.disabled = true;
      
      try {
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
          
          showToast('✅ Cambios guardados correctamente', { type: 'success' });
          
          if (data.changed_username) {
            setTimeout(() => window.location.reload(), 1500);
          }
        } else {
          let msg = 'Error al guardar los cambios';
          try {
            const data = await resp.json();
            if (data.error) msg = data.error;
          } catch {
            // ignore
          }
          showToast(`❌ ${msg}`, { type: 'error', delay: 5000 });
        }
      } catch (error) {
        showToast('❌ Error de conexión', { type: 'error', delay: 5000 });
      } finally {
        // Restaurar botón
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
      }
    });
  });

  // Validación de nombre de usuario en tiempo real
  const usernameInput = document.getElementById('username');
  const feedback = document.getElementById('usernameFeedback');
  if (usernameInput && feedback) {
    let debounceTimer;
    
    usernameInput.addEventListener('input', async () => {
      clearTimeout(debounceTimer);
      
      const value = usernameInput.value.trim();
      if (!value || value === usernameInput.dataset.current) {
        feedback.textContent = '';
        feedback.classList.remove('text-success', 'text-danger');
        return;
      }
      
      // Mostrar estado de verificación
      feedback.textContent = '🔍 Verificando...';
      feedback.classList.remove('text-success', 'text-danger');
      
      debounceTimer = setTimeout(async () => {
        try {
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
            feedback.textContent = '⚠️ Error al verificar';
            feedback.classList.remove('text-success');
            feedback.classList.add('text-danger');
          }
        } catch (error) {
          feedback.textContent = '⚠️ Error de conexión';
          feedback.classList.remove('text-success');
          feedback.classList.add('text-danger');
        }
      }, 500);
    });
  }

  // Toggle de notificaciones de sonido
  const toggle = document.getElementById('notifSoundToggle');
  if (toggle) {
    toggle.checked = localStorage.getItem('notifSound') !== 'off';
    toggle.addEventListener('change', () => {
      const on = toggle.checked;
      localStorage.setItem('notifSound', on ? 'on' : 'off');
      if (window.CRUNEVO_CONFIG) {
        window.CRUNEVO_CONFIG.soundEnabled = on;
      }
      
      showToast(on ? '🔊 Sonidos activados' : '🔇 Sonidos desactivados', { 
        type: 'info',
        delay: 2000 
      });
    });
  }
  
  // Validación de contraseñas
  const newPasswordInput = document.getElementById('new_password');
  const confirmPasswordInput = document.getElementById('confirm_new');
  
  if (newPasswordInput && confirmPasswordInput) {
    function validatePasswords() {
      const newPassword = newPasswordInput.value;
      const confirmPassword = confirmPasswordInput.value;
      
      // Limpiar estilos previos
      newPasswordInput.classList.remove('is-invalid', 'is-valid');
      confirmPasswordInput.classList.remove('is-invalid', 'is-valid');
      
      if (newPassword.length > 0) {
        if (newPassword.length >= 8) {
          newPasswordInput.classList.add('is-valid');
        } else {
          newPasswordInput.classList.add('is-invalid');
        }
      }
      
      if (confirmPassword.length > 0) {
        if (confirmPassword === newPassword && newPassword.length >= 8) {
          confirmPasswordInput.classList.add('is-valid');
        } else {
          confirmPasswordInput.classList.add('is-invalid');
        }
      }
    }
    
    newPasswordInput.addEventListener('input', validatePasswords);
    confirmPasswordInput.addEventListener('input', validatePasswords);
  }
}

// Agregar estilos para animaciones
const style = document.createElement('style');
style.textContent = `
  .spin {
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
  
  .settings-section {
    animation: fadeIn 0.3s ease-in-out;
  }
  
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }
`;
document.head.appendChild(style);

window.initSettingsPage = initSettingsPage;

