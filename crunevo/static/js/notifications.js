
// Sistema mejorado de notificaciones
class NotificationManager {
    constructor() {
        this.dropdown = document.getElementById('notificationDropdown');
        this.badge = document.querySelector('.notification-badge');
        this.container = document.querySelector('.notification-container');
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
            this.updateBadge(data.unread_count);
            this.renderNotifications(data.notifications);
        } catch (error) {
            console.error('Error loading notifications:', error);
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
        
        if (notifications.length === 0) {
            this.container.innerHTML = '<div class="text-center text-muted p-3">No hay notificaciones</div>';
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
        setInterval(() => this.loadNotifications(), 30000); // Cada 30 segundos
    }
}

// Initialization handled in main.js
function initNotificationManager() {
    if (window.CURRENT_USER_ID) {
        new NotificationManager();
    }
}
window.initNotificationManager = initNotificationManager;
