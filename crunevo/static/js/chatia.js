function initChatIA() {
  const form = document.getElementById('aiForm');
  const input = document.getElementById('aiInput');
  const history = document.getElementById('aiHistory');

  function append(author, text) {
    const div = document.createElement('div');
    div.innerHTML = `<strong>${author}:</strong> ${text}`;
    history.appendChild(div);
    history.scrollTop = history.scrollHeight;
  }

  function showTyping() {
    const span = document.createElement('div');
    span.id = 'typing';
    span.className = 'text-muted fst-italic';
    span.textContent = 'escribiendo...';
    history.appendChild(span);
    history.scrollTop = history.scrollHeight;
  }

  function hideTyping() {
    document.getElementById('typing')?.remove();
  }

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const msg = input.value.trim();
    if (!msg) return;
    append('Tú', msg);
    input.value = '';
    showTyping();
    csrfFetch('/ia/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg })
    })
      .then((r) => r.json())
      .then((data) => {
        hideTyping();
        if (data.answer) {
          append('ChatCrunevo', data.answer);
        } else {
          showToast('Error al recibir respuesta');
        }
      })
      .catch(() => {
        hideTyping();
        showToast('Error de conexión');
      });
  });
}
window.initChatIA = initChatIA;
