function initNoteViewer() {
  const container = document.getElementById('noteViewer');
  if (!container) return;
  const type = container.dataset.type;
  const url = container.dataset.url;
  if (type === 'pdf' && typeof pdfjsLib !== 'undefined') {
    let pdfDoc = null;
    let pageNum = 1;
    let scale = 1;
    const canvas = document.createElement('canvas');
    canvas.className = 'border rounded w-100 mb-2';
    const ctx = canvas.getContext('2d');
    const controls = document.createElement('div');
    controls.className = 'd-flex justify-content-between align-items-center mb-2';
    controls.innerHTML = `
      <div>
        <button class="btn btn-outline-secondary btn-sm me-1" id="prevPage">&#x25C0;</button>
        <button class="btn btn-outline-secondary btn-sm" id="nextPage">&#x25B6;</button>
      </div>
      <div>
        <button class="btn btn-outline-secondary btn-sm me-1" id="zoomOut">-</button>
        <button class="btn btn-outline-secondary btn-sm" id="zoomIn">+</button>
      </div>
    `;
    container.appendChild(controls);
    container.appendChild(canvas);
    function renderPage(num) {
      pdfDoc.getPage(num).then((page) => {
        const viewport = page.getViewport({ scale });
        canvas.height = viewport.height;
        canvas.width = viewport.width;
        page.render({ canvasContext: ctx, viewport });
      });
    }
    pdfjsLib.getDocument(url).promise.then((pdf) => {
      pdfDoc = pdf;
      renderPage(pageNum);
    });
    container.addEventListener('click', (e) => {
      if (e.target.id === 'prevPage' && pageNum > 1) {
        pageNum--;
        renderPage(pageNum);
      } else if (e.target.id === 'nextPage' && pdfDoc && pageNum < pdfDoc.numPages) {
        pageNum++;
        renderPage(pageNum);
      } else if (e.target.id === 'zoomIn') {
        scale = Math.min(scale + 0.25, 3);
        renderPage(pageNum);
      } else if (e.target.id === 'zoomOut') {
        scale = Math.max(scale - 0.25, 0.5);
        renderPage(pageNum);
      }
    });
  } else if (type === 'image') {
    const img = document.createElement('img');
    img.src = url;
    img.className = 'img-fluid rounded shadow-sm';
    container.appendChild(img);
  } else {
    const p = document.createElement('p');
    p.className = 'alert alert-info';
    p.textContent = 'Este archivo no tiene vista previa. Desc\u00e1rgalo para revisarlo.';
    container.appendChild(p);
  }
}
