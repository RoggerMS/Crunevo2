(function(){
  const WS = {
    isEditMode:false,
    container:null,
    init(){
      this.container = document.getElementById('grid-stack') || document.getElementById('blocks-grid');
      if(!this.container) return;
      this.restorePositions();
      document.getElementById('edit-mode-btn')?.addEventListener('click', ()=>this.toggleEditMode());
      this.makeBlocksDraggable();
    },
    makeBlocksDraggable(){
      this.blocks().forEach(block=>{
        block.style.position='absolute';
        const x = parseInt(block.dataset.x||0);
        const y = parseInt(block.dataset.y||0);
        block.style.left = x + 'px';
        block.style.top = y + 'px';
        this.attachDrag(block);
      });
    },
    blocks(){
      return Array.from(this.container.querySelectorAll('[data-block-id]'));
    },
    attachDrag(block){
      let startX,startY,offsetX,offsetY;
      const onMove = e => {
        block.style.left = (e.clientX - offsetX) + 'px';
        block.style.top = (e.clientY - offsetY) + 'px';
      };
      const onUp = e => {
        document.removeEventListener('pointermove',onMove);
        document.removeEventListener('pointerup',onUp);
        block.releasePointerCapture(e.pointerId);
        this.finishDrag(block,startX,startY);
      };
      block.addEventListener('pointerdown', e => {
        if(!this.isEditMode) return;
        startX=parseInt(block.style.left)||0;
        startY=parseInt(block.style.top)||0;
        offsetX=e.clientX-startX;
        offsetY=e.clientY-startY;
        block.setPointerCapture(e.pointerId);
        document.addEventListener('pointermove',onMove);
        document.addEventListener('pointerup',onUp);
      });
    },
    finishDrag(block,origX,origY){
      if(this.isColliding(block)){
        block.style.left = origX+'px';
        block.style.top = origY+'px';
      }
      block.dataset.x = parseInt(block.style.left)||0;
      block.dataset.y = parseInt(block.style.top)||0;
    },
    isColliding(block){
      const rect1 = block.getBoundingClientRect();
      return this.blocks().some(other=>{
        if(other===block) return false;
        const r = other.getBoundingClientRect();
        return !(rect1.right<=r.left || rect1.left>=r.right || rect1.bottom<=r.top || rect1.top>=r.bottom);
      });
    },
    toggleEditMode(){
      this.isEditMode=!this.isEditMode;
      const btn=document.getElementById('edit-mode-btn');
      if(btn){
        btn.innerHTML = this.isEditMode?'<i class="bi bi-check me-1"></i>Finalizar':'<i class="bi bi-pencil me-1"></i>Editar';
      }
      if(!this.isEditMode){
        this.savePositions();
      }
    },
    savePositions(){
      const data={};
      this.blocks().forEach(b=>{
        data[b.dataset.blockId]={x:parseInt(b.dataset.x)||0,y:parseInt(b.dataset.y)||0};
      });
      localStorage.setItem('workspacePositions',JSON.stringify(data));
    },
    restorePositions(){
      const data=JSON.parse(localStorage.getItem('workspacePositions')||'{}');
      this.blocks().forEach(b=>{
        const pos=data[b.dataset.blockId];
        if(pos){
          b.dataset.x=pos.x;
          b.dataset.y=pos.y;
          b.style.left=pos.x+'px';
          b.style.top=pos.y+'px';
        }
      });
    },
    addBlock(block){
      if(!this.container) return;
      const b = block && (block.block || block);
      if(!b) return;

      // Normalize block data using existing helpers when available
      let normalized = b;
      if (typeof convertBlock === 'function') {
        normalized = convertBlock(b);
      }

      let el;
      if (typeof createBlockElement === 'function') {
        el = createBlockElement(normalized);
      } else {
        el = document.createElement('div');
        el.className = 'grid-stack-item workspace-block';
        el.innerHTML = `<div class="grid-stack-item-content"><h4>${normalized.title||'Bloque'}</h4></div>`;
      }

      el.dataset.blockId = normalized.id;
      const posX = (b.position && b.position.x) || b.position_x || 0;
      const posY = (b.position && b.position.y) || b.position_y || 0;
      el.dataset.x = posX;
      el.dataset.y = posY;
      el.style.position = 'absolute';
      el.style.left = posX + 'px';
      el.style.top = posY + 'px';

      this.container.appendChild(el);
      this.attachDrag(el);

      // Hide empty state and update footer count
      const empty = document.querySelector('.empty-workspace');
      if (empty) empty.classList.add('d-none');
      const countEl = document.querySelector('.workspace-info div:nth-child(2)');
      if (countEl) countEl.textContent = `${this.blocks().length} bloques`;
    }
  };
  window.WorkspaceBlocks=WS;
  document.addEventListener('DOMContentLoaded',()=>WS.init());
})();
