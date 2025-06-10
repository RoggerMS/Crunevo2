// dark mode toggle
(function(){
  const theme = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-bs-theme', theme);
  document.addEventListener('DOMContentLoaded', function(){
    const btn = document.getElementById('themeToggle');
    if(btn){
      btn.addEventListener('click', function(){
        const current = document.documentElement.getAttribute('data-bs-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-bs-theme', next);
        localStorage.setItem('theme', next);
      });
    }
  });
})();

// simple AJAX search suggestions
document.addEventListener('DOMContentLoaded', function(){
  const input = document.getElementById('globalSearchInput');
  const box = document.getElementById('searchSuggestions');
  if(!input) return;
  input.addEventListener('input', function(){
    const q = this.value.trim();
    if(q.length < 2){ box.innerHTML=''; return; }
    fetch(`/search?q=${encodeURIComponent(q)}`)
      .then(r => r.json())
      .then(data => {
        box.innerHTML = '';
        data.forEach(item => {
          const a = document.createElement('a');
          a.className = 'list-group-item list-group-item-action';
          a.href = item.url;
          a.textContent = item.title;
          box.appendChild(a);
        });
      });
  });
});
