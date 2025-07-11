let annotationHandler = null;
function setAnnotationHook(fn) {
  annotationHandler = typeof fn === 'function' ? fn : null;
}

function initNoteViewer() {
  const container = document.getElementById('noteViewer');
  if (!container) return;
  const fullBtn = document.getElementById('fullscreenBtn');
  fullBtn?.addEventListener('click', () => {
    if (!document.fullscreenElement) {
      container.requestFullscreen?.();
    } else {
      document.exitFullscreen?.();
    }
  });
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
    canvas.addEventListener('dblclick', (ev) => {
      if (annotationHandler) {
        annotationHandler({ page: pageNum, x: ev.offsetX, y: ev.offsetY });
      }
    });
  } else if (type === 'docx' && typeof mammoth !== 'undefined') {
    const display = document.createElement('div');
    display.className = 'docx-preview';
    container.appendChild(display);
    fetch(url)
      .then((res) => res.arrayBuffer())
      .then((buf) => mammoth.convertToHtml({ arrayBuffer: buf }))
      .then((result) => {
        display.innerHTML = result.value;
      })
      .catch(() => {
        display.innerHTML = '<p class="alert alert-info">No se pudo mostrar el documento</p>';
      });
  } else if (type === 'pptx' && typeof pdfjsLib !== 'undefined') {
    // PowerPoint files are converted to PDF before viewing
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

window.setAnnotationHook = setAnnotationHook;

function initUploadPreview() {
  const fileInput = document.getElementById('file');
  if (!fileInput) return;
  const pdfPrev = document.getElementById('pdfPreview');
  const imgPrev = document.getElementById('imgPreview');
  const docxPrev = document.getElementById('docxPreview');
  const pptPrev = document.getElementById('pptPreview');

  function hideAll() {
    [pdfPrev, imgPrev, docxPrev, pptPrev].forEach((el) => el && el.classList.add('d-none'));
  }

  fileInput.addEventListener('change', () => {
    const file = fileInput.files[0];
    hideAll();
    if (!file) return;
    const name = file.name.toLowerCase();
    if ((file.type === 'application/pdf' || name.endsWith('.pdf')) && pdfPrev && typeof pdfjsLib !== 'undefined') {
      const reader = new FileReader();
      reader.onload = (e) => {
        const task = pdfjsLib.getDocument({ data: e.target.result });
        task.promise
          .then((pdf) => pdf.getPage(1))
          .then((page) => {
            const viewport = page.getViewport({ scale: 1.2 });
            const ctx = pdfPrev.getContext('2d');
            pdfPrev.width = viewport.width;
            pdfPrev.height = viewport.height;
            page.render({ canvasContext: ctx, viewport });
            pdfPrev.classList.remove('d-none');
          })
          .catch(() => pdfPrev.classList.add('d-none'));
      };
      reader.readAsArrayBuffer(file);
    } else if (file.type.startsWith('image/') && imgPrev) {
      imgPrev.src = URL.createObjectURL(file);
      imgPrev.onload = () => URL.revokeObjectURL(imgPrev.src);
      imgPrev.onerror = () => imgPrev.classList.add('d-none');
      imgPrev.classList.remove('d-none');
    } else if (name.endsWith('.docx') && docxPrev && typeof mammoth !== 'undefined') {
      const reader = new FileReader();
      reader.onload = (e) => {
        mammoth
          .convertToHtml({ arrayBuffer: e.target.result })
          .then((result) => {
            docxPrev.innerHTML = result.value;
            docxPrev.classList.remove('d-none');
          })
          .catch(() => {
            pptPrev.textContent = file.name;
            pptPrev.classList.remove('d-none');
          });
      };
      reader.readAsArrayBuffer(file);
    } else if (name.endsWith('.pptx') && pptPrev) {
      pptPrev.textContent = file.name;
      pptPrev.classList.remove('d-none');
    } else if (pptPrev) {
      pptPrev.textContent = file.name;
      pptPrev.classList.remove('d-none');
    }
  });
}

window.initUploadPreview = initUploadPreview;
