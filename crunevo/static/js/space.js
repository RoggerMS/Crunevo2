const blocksKey = 'ps_blocks_v2';
let blocks = [];

document.addEventListener('DOMContentLoaded', () => {
  loadBlocks();
  renderBlocks();
  initTheme();
  new Sortable(document.getElementById('blocksContainer'), {
    animation: 150,
    onEnd: saveOrder
  });

  document.getElementById('darkModeToggle').addEventListener('click', toggleDark);
  document.getElementById('focusModeBtn').addEventListener('click', toggleFocus);
  document.getElementById('exitFocusBtn').addEventListener('click', toggleFocus);
  document.getElementById('addBlockBtn').addEventListener('click', () => {
    new bootstrap.Modal(document.getElementById('addBlockModal')).show();
  });
  document.querySelectorAll('.block-option').forEach(el => {
    el.addEventListener('click', () => {
      addBlock(el.dataset.type);
      bootstrap.Modal.getInstance(document.getElementById('addBlockModal')).hide();
    });
  });
  document.getElementById('startSpaceBtn')?.addEventListener('click', () => {
    addBlock('nota');
    document.getElementById('emptyState').classList.add('d-none');
  });

  document.getElementById('smartSuggestions').addEventListener('click', e => {
    if(e.target.classList.contains('suggestion-apply')){
      const card = e.target.closest('.suggestion-card');
      const type = card.dataset.type;
      if(!blocks.some(b => b.type === type)) addBlock(type);
      card.remove();
      if(!document.querySelector('#smartSuggestions .suggestion-card')){
        document.getElementById('smartSuggestions').classList.add('d-none');
      }
    }
  });

  document.getElementById('blocksContainer').addEventListener('click', e => {
    const card = e.target.closest('.ps-block');
    if(!card) return;
    const id = Number(card.dataset.id);
    if(e.target.closest('.delete-block')){ deleteBlock(id); }
    else if(e.target.closest('.edit-block')){ editBlock(id); }
  });
});

function initTheme(){
  const dark = localStorage.getItem('ps_dark') === '1';
  document.getElementById('psContainer').classList.toggle('dark', dark);
}
function toggleDark(){
  const cont = document.getElementById('psContainer');
  const dark = cont.classList.toggle('dark');
  localStorage.setItem('ps_dark', dark ? '1' : '0');
}
function toggleFocus(){
  const cont = document.getElementById('psContainer');
  const f = cont.classList.toggle('focus');
  document.querySelectorAll('.navbar,.sidebar-left,.sidebar-right,.mobile-bottom-nav')
    .forEach(el => el.classList.toggle('d-none', f));
  document.getElementById('exitFocusBtn').classList.toggle('d-none', !f);
  cont.style.background = f ? '#fff' : '';
}

function loadBlocks(){
  try { blocks = JSON.parse(localStorage.getItem(blocksKey) || '[]'); } catch(e) { blocks = []; }
}
function saveBlocks(){
  localStorage.setItem(blocksKey, JSON.stringify(blocks));
}
function saveOrder(){
  const ids = [...document.querySelectorAll('.ps-block')].map(el => Number(el.dataset.id));
  blocks.sort((a,b) => ids.indexOf(a.id) - ids.indexOf(b.id));
  saveBlocks();
}
function renderBlocks(){
  const container = document.getElementById('blocksContainer');
  container.innerHTML = '';
  if(blocks.length === 0){
    document.getElementById('emptyState').classList.remove('d-none');
    return;
  }
  document.getElementById('emptyState').classList.add('d-none');
  blocks.forEach(b => container.appendChild(createBlockEl(b)));
}
function createBlockEl(block){
  const div = document.createElement('div');
  div.className = 'ps-block';
  div.dataset.id = block.id;
  div.innerHTML = `<div class="d-flex justify-content-between align-items-start mb-2">
    <strong>${block.title}</strong>
    <div class="block-actions">
      <button class="btn btn-sm btn-outline-secondary edit-block"><i class="bi bi-pencil"></i></button>
      <button class="btn btn-sm btn-outline-danger delete-block"><i class="bi bi-trash"></i></button>
    </div>
  </div>
  <div class="block-content">${block.content || ''}</div>`;
  return div;
}
function addBlock(type){
  const block = { id: Date.now(), type, title: getTitle(type), content: '' };
  blocks.push(block);
  saveBlocks();
  renderBlocks();
}
function deleteBlock(id){
  blocks = blocks.filter(b => b.id !== id);
  saveBlocks();
  renderBlocks();
}
function editBlock(id){
  const block = blocks.find(b => b.id === id);
  if(!block) return;
  const title = prompt('Título', block.title) || block.title;
  const content = prompt('Contenido', block.content) || block.content;
  block.title = title;
  block.content = content;
  saveBlocks();
  renderBlocks();
}
function getTitle(type){
  switch(type){
    case 'nota': return 'Nueva nota';
    case 'kanban': return 'Tablero Kanban';
    case 'meta': return 'Meta académica';
    case 'enlace': return 'Acceso directo';
    default: return 'Bloque';
  }
}
