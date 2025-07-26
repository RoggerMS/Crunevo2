
// Sistema mejorado de notificaciones
class NotificationManager {
    constructor() {
        this.dropdown = document.querySelector('#notificationsDropdown');
        this.badge = document.querySelector('.notification-badge');
        this.container = document.querySelector('#notifications-list');
        this.init();
    }

    init() {
        this.loadNotifications();
        this.setupAutoRefresh();
    }

    async loadNotifications() {
        try {
            const response = await fetch('/api/notifications');
            const data = await response.json();
            const currentFirst = this.container?.querySelector('.notification-item')?.dataset.id;
            const newFirst = data.notifications[0]?.id?.toString();
            const updated = currentFirst !== newFirst;
            console.log('[NOTIF] unread:', data.unread_count, 'total:', data.notifications.length, updated ? '- updating dropdown' : '- preserving dropdown');
            this.updateBadge(data.unread_count);
            if (updated) {
                this.renderNotifications(data.notifications);
            }
        } catch (error) {
            console.error('Error loading notifications:', error);
            if (window.CRUNEVO_UI && window.CRUNEVO_UI.showErrorToast) {
                window.CRUNEVO_UI.showErrorToast('Error al cargar notificaciones');
            } else if (typeof showToast === 'function') {
                showToast('Error al cargar notificaciones');
            }
        }
    }

    updateBadge(count) {
        if (this.badge) {
            this.badge.textContent = count;
            this.badge.style.display = count > 0 ? 'inline' : 'none';
        }
    }

    renderNotifications(notifications) {
        if (!this.container) return;
        
        // Remove previous "no new" message if present
        const noNew = this.container.querySelector('.no-new-notifs');
        if (noNew) noNew.remove();

        if (notifications.length === 0) {
            if (this.container.querySelectorAll('.notification-item').length === 0) {
                this.container.innerHTML = '<div class="text-center text-muted p-3">No hay notificaciones</div>';
            } else {
                const msg = document.createElement('div');
                msg.className = 'text-center text-muted p-3 no-new-notifs';
                msg.textContent = 'No hay notificaciones nuevas';
                this.container.appendChild(msg);
            }
            return;
        }

        this.container.innerHTML = notifications.map(notif => `
            <div class="notification-item ${notif.read ? '' : 'unread'}" data-id="${notif.id}">
                <div class="d-flex align-items-start">
                    <i class="bi bi-${this.getIcon(notif.type)} me-2"></i>
                    <div class="flex-grow-1">
                        <p class="mb-1 small">${notif.message}</p>
                        <small class="text-muted">${this.formatTime(notif.timestamp)}</small>
                    </div>
                </div>
            </div>
        `).join('');
    }

    getIcon(type) {
        const icons = {
            'like': 'heart-fill',
            'comment': 'chat-fill',
            'achievement': 'trophy-fill',
            'system': 'bell-fill'
        };
        return icons[type] || 'bell';
    }

    formatTime(timestamp) {
        return new Date(timestamp).toLocaleDateString('es-ES', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    setupAutoRefresh() {
        setInterval(() => {
            if (!document.hidden) {
                this.loadNotifications();
            }
        }, 30000); // Cada 30 segundos si la pestaña está activa
    }
}

// Initialization handled in main.js
function initNotificationManager() {
    if (window.CURRENT_USER_ID) {
        new NotificationManager();
    }
}
window.initNotificationManager = initNotificationManager;
