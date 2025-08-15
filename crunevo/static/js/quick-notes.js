/**
 * Quick Notes System - Modal-based note taking with tags and user preferences
 * Accessible via menu with Ctrl+Enter shortcut
 */

class QuickNotesSystem {
    constructor() {
        this.modal = null;
        this.textarea = null;
        this.tagsInput = null;
        this.saveButton = null;
        this.showOnLoginToggle = null;
        this.currentNote = null;
        this.userPreferences = {
            show_quick_note_on_login: false
        };
        
        this.init();
    }

    init() {
        this.createModal();
        this.bindEvents();
        this.loadUserPreferences();
        this.checkShowOnLogin();
    }

    createModal() {
        // Create modal HTML structure
        const modalHTML = `
            <div id="quick-notes-modal" class="fixed inset-0 bg-black bg-opacity-50 hidden z-50" role="dialog" aria-labelledby="quick-notes-title" aria-modal="true">
                <div class="flex items-center justify-center min-h-screen p-4">
                    <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
                        <div class="flex items-center justify-between p-6 border-b">
                            <h2 id="quick-notes-title" class="text-xl font-semibold text-gray-900">Notas Rápidas</h2>
                            <button id="close-quick-notes" class="text-gray-400 hover:text-gray-600 transition-colors" aria-label="Cerrar modal de notas rápidas">
                                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                                </svg>
                            </button>
                        </div>
                        
                        <div class="p-6">
                            <div class="mb-4">
                                <label for="quick-note-content" class="block text-sm font-medium text-gray-700 mb-2">Contenido</label>
                                <textarea 
                                    id="quick-note-content" 
                                    class="w-full h-40 p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                                    placeholder="Escribe tu nota aquí... (Ctrl+Enter para guardar)"
                                    aria-describedby="quick-note-help"
                                ></textarea>
                                <p id="quick-note-help" class="text-sm text-gray-500 mt-1">Usa Ctrl+Enter para guardar rápidamente</p>
                            </div>
                            
                            <div class="mb-4">
                                <label for="quick-note-tags" class="block text-sm font-medium text-gray-700 mb-2">Etiquetas</label>
                                <input 
                                    type="text" 
                                    id="quick-note-tags" 
                                    class="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    placeholder="Separar con comas: trabajo, personal, ideas"
                                    aria-describedby="tags-help"
                                >
                                <p id="tags-help" class="text-sm text-gray-500 mt-1">Separa las etiquetas con comas</p>
                            </div>
                            
                            <div class="mb-6">
                                <label class="flex items-center">
                                    <input type="checkbox" id="show-note-on-login" class="rounded border-gray-300 text-blue-600 focus:ring-blue-500">
                                    <span class="ml-2 text-sm text-gray-700">Mostrar última nota al iniciar sesión</span>
                                </label>
                            </div>
                        </div>
                        
                        <div class="flex items-center justify-between p-6 border-t bg-gray-50">
                            <div id="save-status" class="text-sm text-gray-600"></div>
                            <div class="flex space-x-3">
                                <button id="cancel-quick-note" class="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors">
                                    Cancelar
                                </button>
                                <button id="save-quick-note" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors" aria-label="Guardar nota rápida">
                                    Guardar
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Insert modal into DOM
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Get references
        this.modal = document.getElementById('quick-notes-modal');
        this.textarea = document.getElementById('quick-note-content');
        this.tagsInput = document.getElementById('quick-note-tags');
        this.saveButton = document.getElementById('save-quick-note');
        this.showOnLoginToggle = document.getElementById('show-note-on-login');
    }

    bindEvents() {
        // Close modal events
        document.getElementById('close-quick-notes').addEventListener('click', () => this.closeModal());
        document.getElementById('cancel-quick-note').addEventListener('click', () => this.closeModal());
        
        // Save events
        this.saveButton.addEventListener('click', () => this.saveNote());
        
        // Keyboard shortcuts
        this.textarea.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                this.saveNote();
            }
        });
        
        // Escape to close
        this.modal.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });
        
        // Preference toggle
        this.showOnLoginToggle.addEventListener('change', () => {
            this.updateUserPreference();
        });
        
        // Click outside to close
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.closeModal();
            }
        });
    }

    openModal(existingNote = null) {
        this.currentNote = existingNote;
        
        if (existingNote) {
            this.textarea.value = existingNote.content || '';
            this.tagsInput.value = existingNote.tags ? existingNote.tags.join(', ') : '';
        } else {
            this.textarea.value = '';
            this.tagsInput.value = '';
        }
        
        this.modal.classList.remove('hidden');
        this.textarea.focus();
        
        // Trap focus within modal
        this.trapFocus();
    }

    closeModal() {
        this.modal.classList.add('hidden');
        this.clearStatus();
    }

    async saveNote() {
        const content = this.textarea.value.trim();
        if (!content) {
            this.showStatus('Por favor escribe algo antes de guardar', 'error');
            return;
        }
        
        const tags = this.tagsInput.value
            .split(',')
            .map(tag => tag.trim())
            .filter(tag => tag.length > 0);
        
        const noteData = {
            content: content,
            tags: tags,
            type: 'quick_note'
        };
        
        try {
            this.showStatus('Guardando...', 'loading');
            
            const response = await fetch('/api/personal-space/quick-notes', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(noteData)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showStatus('¡Nota guardada exitosamente!', 'success');
                setTimeout(() => {
                    this.closeModal();
                }, 1500);
            } else {
                this.showStatus(result.error || 'Error al guardar la nota', 'error');
            }
        } catch (error) {
            console.error('Error saving quick note:', error);
            this.showStatus('Error de conexión al guardar', 'error');
        }
    }

    async loadUserPreferences() {
        try {
            const response = await fetch('/api/personal-space/user-preferences');
            if (response.ok) {
                const prefs = await response.json();
                this.userPreferences = { ...this.userPreferences, ...prefs };
                this.showOnLoginToggle.checked = this.userPreferences.show_quick_note_on_login;
            }
        } catch (error) {
            console.error('Error loading user preferences:', error);
        }
    }

    async updateUserPreference() {
        const newValue = this.showOnLoginToggle.checked;
        
        try {
            const response = await fetch('/api/personal-space/user-preferences', {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    show_quick_note_on_login: newValue
                })
            });
            
            if (response.ok) {
                this.userPreferences.show_quick_note_on_login = newValue;
            }
        } catch (error) {
            console.error('Error updating user preference:', error);
        }
    }

    async checkShowOnLogin() {
        if (this.userPreferences.show_quick_note_on_login) {
            try {
                const response = await fetch('/api/personal-space/quick-notes/latest');
                if (response.ok) {
                    const note = await response.json();
                    if (note && note.content) {
                        setTimeout(() => this.openModal(note), 1000);
                    }
                }
            } catch (error) {
                console.error('Error loading latest note:', error);
            }
        }
    }

    showStatus(message, type) {
        const statusEl = document.getElementById('save-status');
        statusEl.textContent = message;
        statusEl.className = `text-sm ${
            type === 'success' ? 'text-green-600' :
            type === 'error' ? 'text-red-600' :
            type === 'loading' ? 'text-blue-600' :
            'text-gray-600'
        }`;
    }

    clearStatus() {
        const statusEl = document.getElementById('save-status');
        statusEl.textContent = '';
    }

    trapFocus() {
        const focusableElements = this.modal.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        this.modal.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                if (e.shiftKey) {
                    if (document.activeElement === firstElement) {
                        e.preventDefault();
                        lastElement.focus();
                    }
                } else {
                    if (document.activeElement === lastElement) {
                        e.preventDefault();
                        firstElement.focus();
                    }
                }
            }
        });
    }

    getCSRFToken() {
        const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        if (!token) {
            console.warn('CSRF token not found');
        }
        return token || '';
    }
}

// Initialize Quick Notes System
let quickNotesSystem;

document.addEventListener('DOMContentLoaded', () => {
    quickNotesSystem = new QuickNotesSystem();
});

// Export for global access
window.QuickNotesSystem = QuickNotesSystem;
window.openQuickNotes = () => {
    if (quickNotesSystem) {
        quickNotesSystem.openModal();
    }
};