(function() {
  function renderGrid(blocks) {
    const grid = document.getElementById('blocks-grid');
    if (!grid) return;
    grid.innerHTML = '';
    blocks.forEach(insertCard);
    if (blocks.length) {
      hideEmptyState();
    }
  }

  function insertCard(block) {
    const grid = document.getElementById('blocks-grid');
    if (!grid) return;
    const card = document.createElement('div');
    card.className = 'card mb-3';
    card.tabIndex = 0;
    const color = block?.metadata?.theme_color || 'primary';
    card.innerHTML = `<div class="card-body border-${color}">` +
      `<h5 class="card-title">${block.title || ''}</h5>` +
      `<p class="card-text text-muted">${block.type}</p>` +
      `</div>`;
    grid.appendChild(card);
  }

  function hideEmptyState() {
    const empty = document.querySelector('.empty-workspace');
    if (empty) empty.classList.add('d-none');
  }

  function updateFooter(n) {
    const el = document.querySelector('.workspace-info div:nth-child(2)');
    if (el) el.textContent = `${n} bloques`;
  }

  window.WorkspaceBlocks = {
    _blocks: [],
    async load() {
      const res = await fetch('/api/personal-space/blocks');
      const data = await res.json();
      this._blocks = Array.isArray(data.blocks) ? data.blocks : [];
      renderGrid(this._blocks);
      if (!this._blocks.length) {
        const empty = document.querySelector('.empty-workspace');
        if (empty) empty.classList.remove('d-none');
      }
      updateFooter(this._blocks.length);
    },
    addBlock(block) {
      const b = block && (block.block || block);
      if (!b) return;
      this._blocks.push(b);
      insertCard(b);
      hideEmptyState();
      updateFooter(this._blocks.length);
    }
  };

  document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('blocks-grid')) {
      window.WorkspaceBlocks.load().catch(console.error);
    }
  });

  window.WorkspaceLayout = {
    refreshBlocks() {
      window.WorkspaceBlocks.load();
    }
  };
})();
