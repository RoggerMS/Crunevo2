document.addEventListener('DOMContentLoaded', () => {
  const saved = localStorage.getItem('theme');
  if (saved) {
    document.documentElement.dataset.bsTheme = saved;
  }
  const toggle = document.getElementById('themeToggle');
  toggle?.addEventListener('click', () => {
    const html = document.documentElement;
    const next = html.dataset.bsTheme === 'dark' ? 'light' : 'dark';
    html.dataset.bsTheme = next;
    localStorage.setItem('theme', next);
  });
});

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
          a.className = 'block px-2 py-1 hover:bg-gray-100 dark:hover:bg-gray-700';
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

