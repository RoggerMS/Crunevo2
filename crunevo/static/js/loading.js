
// Sistema de loading states
class LoadingManager {
    static show(element, message = 'Cargando...') {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        
        if (!element) return;
        
        element.disabled = true;
        element.dataset.originalText = element.textContent;
        element.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2" role="status"></span>
            ${message}
        `;
    }
    
    static hide(element) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        
        if (!element) return;
        
        element.disabled = false;
        element.textContent = element.dataset.originalText || 'Enviar';
    }
    
    static showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        document.querySelector('.toast-container').appendChild(toast);
        new bootstrap.Toast(toast).show();
        
        setTimeout(() => toast.remove(), 5000);
    }
}

// Hacer disponible globalmente
window.LoadingManager = LoadingManager;
