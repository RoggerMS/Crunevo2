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

  // hide search suggestions on blur
  input.addEventListener('blur', function(){
    setTimeout(() => { box.innerHTML = ''; }, 100);
  });
});

// close mobile menu when a link is clicked
document.addEventListener('DOMContentLoaded', function(){
  document.querySelectorAll('.navbar-crunevo .navbar-nav .nav-link').forEach(el => {
    el.addEventListener('click', () => {
      const collapse = document.getElementById('navbarNav');
      const bsCollapse = bootstrap.Collapse.getInstance(collapse);
      if(bsCollapse) bsCollapse.hide();
    });
  });
});
