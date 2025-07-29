// CRUNEVO Admin UI - Funcionalidades Avanzadas
class CRUNEVOAdminUI {
    constructor() {
        this.currentTheme = localStorage.getItem('admin-theme') || 'light';
        this.autoRefresh = false;
        this.refreshInterval = null;
        this.notifications = [];
        this.init();
    }

    init() {
        this.setupThemeToggle();
        this.setupAutoRefresh();
        this.setupNotifications();
        this.setupRealTimeUpdates();
        this.setupKeyboardShortcuts();
        this.setupPerformanceMonitoring();
        this.setupErrorHandling();
    }

    setupThemeToggle() {
        const themeToggle = document.querySelector('[data-theme-toggle]');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => {
                this.toggleTheme();
            });
            this.updateThemeIcon();
        }
    }

    toggleTheme() {
        this.currentTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        localStorage.setItem('admin-theme', this.currentTheme);
        
        document.body.setAttribute('data-bs-theme', this.currentTheme);
        this.updateThemeIcon();
        
        // Notificar cambio
        this.showNotification('Tema cambiado a ' + (this.currentTheme === 'light' ? 'claro' : 'oscuro'), 'info');
    }

    updateThemeIcon() {
        const icon = document.querySelector('[data-theme-toggle] i');
        if (icon) {
            icon.className = this.currentTheme === 'light' ? 'bi bi-moon' : 'bi bi-sun';
        }
    }

    setupAutoRefresh() {
        const autoRefreshToggle = document.getElementById('autoRefreshToggle');
        if (autoRefreshToggle) {
            autoRefreshToggle.addEventListener('change', (e) => {
                this.autoRefresh = e.target.checked;
                if (this.autoRefresh) {
                    this.startAutoRefresh();
                } else {
                    this.stopAutoRefresh();
                }
            });
        }
    }

    startAutoRefresh() {
        this.refreshInterval = setInterval(() => {
            this.refreshDashboardData();
        }, 30000); // 30 segundos
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    async refreshDashboardData() {
        try {
            const response = await fetch('/admin/api/real-time');
            const data = await response.json();
            
            // Actualizar métricas en tiempo real
            this.updateRealTimeMetrics(data);
            
            // Mostrar notificación de actualización
            this.showNotification('Datos actualizados', 'success', 2000);
            
        } catch (error) {
            console.error('Error refreshing dashboard:', error);
            this.showNotification('Error al actualizar datos', 'error');
        }
    }

    updateRealTimeMetrics(data) {
        // Actualizar contadores en tiempo real
        const activeUsersEl = document.getElementById('activeUsers');
        if (activeUsersEl) {
            activeUsersEl.textContent = data.active_users;
        }
        
        const recentNotesEl = document.getElementById('recentNotes');
        if (recentNotesEl) {
            recentNotesEl.textContent = data.recent_notes;
        }
        
        const recentPostsEl = document.getElementById('recentPosts');
        if (recentPostsEl) {
            recentPostsEl.textContent = data.recent_posts;
        }
    }

    setupNotifications() {
        // Crear contenedor de notificaciones si no existe
        if (!document.getElementById('adminNotifications')) {
            const notificationContainer = document.createElement('div');
            notificationContainer.id = 'adminNotifications';
            notificationContainer.className = 'position-fixed top-0 end-0 p-3';
            notificationContainer.style.zIndex = '9999';
            document.body.appendChild(notificationContainer);
        }
    }

    showNotification(message, type = 'info', duration = 5000) {
        const notificationId = 'notification-' + Date.now();
        const notification = document.createElement('div');
        notification.id = notificationId;
        notification.className = `alert alert-${type} alert-dismissible fade show`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.getElementById('adminNotifications').appendChild(notification);
        
        // Auto-remover después del tiempo especificado
        setTimeout(() => {
            const notificationEl = document.getElementById(notificationId);
            if (notificationEl) {
                notificationEl.remove();
            }
        }, duration);
        
        // Guardar en historial
        this.notifications.push({
            message,
            type,
            timestamp: new Date()
        });
    }

    setupRealTimeUpdates() {
        // WebSocket para actualizaciones en tiempo real
        if (typeof io !== 'undefined') {
            const socket = io('/admin');
            
            socket.on('user_activity', (data) => {
                this.handleUserActivity(data);
            });
            
            socket.on('system_alert', (data) => {
                this.handleSystemAlert(data);
            });
            
            socket.on('error_log', (data) => {
                this.handleErrorLog(data);
            });
        }
    }

    handleUserActivity(data) {
        // Actualizar contadores de actividad
        this.updateActivityCounters(data);
        
        // Mostrar notificación si es actividad importante
        if (data.type === 'new_user' || data.type === 'new_note') {
            this.showNotification(`Nueva actividad: ${data.description}`, 'info');
        }
    }

    handleSystemAlert(data) {
        this.showNotification(`Alerta del sistema: ${data.message}`, data.severity);
        
        // Actualizar indicadores de estado
        this.updateSystemStatus(data);
    }

    handleErrorLog(data) {
        this.showNotification(`Error detectado: ${data.message}`, 'error');
        
        // Incrementar contador de errores
        const errorCounter = document.getElementById('errorCounter');
        if (errorCounter) {
            const currentCount = parseInt(errorCounter.textContent) || 0;
            errorCounter.textContent = currentCount + 1;
        }
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + R: Refrescar dashboard
            if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
                e.preventDefault();
                this.refreshDashboardData();
            }
            
            // Ctrl/Cmd + M: Toggle modo mantenimiento
            if ((e.ctrlKey || e.metaKey) && e.key === 'm') {
                e.preventDefault();
                this.toggleMaintenanceMode();
            }
            
            // Ctrl/Cmd + T: Toggle tema
            if ((e.ctrlKey || e.metaKey) && e.key === 't') {
                e.preventDefault();
                this.toggleTheme();
            }
            
            // Ctrl/Cmd + E: Exportar datos
            if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
                e.preventDefault();
                this.exportDashboardData();
            }
        });
    }

    async toggleMaintenanceMode() {
        try {
            const response = await fetch('/admin/toggle-maintenance', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(data.message, 'success');
                setTimeout(() => {
                    location.reload();
                }, 1000);
            } else {
                this.showNotification('Error al cambiar modo mantenimiento', 'error');
            }
            
        } catch (error) {
            console.error('Error toggling maintenance mode:', error);
            this.showNotification('Error al cambiar modo mantenimiento', 'error');
        }
    }

    async exportDashboardData() {
        try {
            this.showNotification('Exportando datos...', 'info');
            
            const response = await fetch('/admin/api/export-dashboard');
            const blob = await response.blob();
            
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `crunevo-dashboard-${new Date().toISOString().split('T')[0]}.xlsx`;
            a.click();
            
            this.showNotification('Datos exportados correctamente', 'success');
            
        } catch (error) {
            console.error('Error exporting data:', error);
            this.showNotification('Error al exportar datos', 'error');
        }
    }

    setupPerformanceMonitoring() {
        // Monitorear rendimiento de la página
        if ('performance' in window) {
            window.addEventListener('load', () => {
                const perfData = performance.getEntriesByType('navigation')[0];
                
                if (perfData) {
                    const loadTime = perfData.loadEventEnd - perfData.loadEventStart;
                    
                    if (loadTime > 3000) {
                        this.showNotification('Página cargada lentamente', 'warning');
                    }
                }
            });
        }
    }

    setupErrorHandling() {
        // Capturar errores globales
        window.addEventListener('error', (e) => {
            console.error('Global error:', e.error);
            this.showNotification('Error detectado en la aplicación', 'error');
        });
        
        // Capturar promesas rechazadas
        window.addEventListener('unhandledrejection', (e) => {
            console.error('Unhandled promise rejection:', e.reason);
            this.showNotification('Error en promesa no manejada', 'error');
        });
    }

    getCSRFToken() {
        const token = document.querySelector('meta[name="csrf-token"]');
        return token ? token.content : '';
    }

    updateActivityCounters(data) {
        // Actualizar contadores específicos según el tipo de actividad
        const counters = {
            'new_user': 'userCounter',
            'new_note': 'noteCounter',
            'new_post': 'postCounter',
            'new_purchase': 'purchaseCounter'
        };
        
        const counterId = counters[data.type];
        if (counterId) {
            const counter = document.getElementById(counterId);
            if (counter) {
                const currentValue = parseInt(counter.textContent) || 0;
                counter.textContent = currentValue + 1;
                
                // Animación de actualización
                counter.classList.add('text-success');
                setTimeout(() => {
                    counter.classList.remove('text-success');
                }, 1000);
            }
        }
    }

    updateSystemStatus(data) {
        // Actualizar indicadores de estado del sistema
        const statusIndicators = {
            'critical': 'danger',
            'warning': 'warning',
            'info': 'info',
            'success': 'success'
        };
        
        const indicator = document.getElementById('systemStatus');
        if (indicator) {
            indicator.className = `badge bg-${statusIndicators[data.severity] || 'secondary'}`;
            indicator.textContent = data.severity.toUpperCase();
        }
    }

    // Métodos de utilidad
    formatNumber(num) {
        return new Intl.NumberFormat('es-PE').format(num);
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat('es-PE', {
            style: 'currency',
            currency: 'PEN'
        }).format(amount);
    }

    formatDate(date) {
        return new Intl.DateTimeFormat('es-PE', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(new Date(date));
    }

    // Métodos para gráficos y visualizaciones
    createChart(canvasId, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;
        
        const ctx = canvas.getContext('2d');
        return new Chart(ctx, {
            type: options.type || 'line',
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                ...options
            }
        });
    }

    updateChart(chart, newData) {
        if (chart) {
            chart.data = newData;
            chart.update();
        }
    }

    // Métodos para tablas dinámicas
    createDataTable(tableId, data, columns) {
        const table = document.getElementById(tableId);
        if (!table) return;
        
        // Limpiar tabla
        const tbody = table.querySelector('tbody');
        if (tbody) {
            tbody.innerHTML = '';
        }
        
        // Agregar filas
        data.forEach(row => {
            const tr = document.createElement('tr');
            columns.forEach(col => {
                const td = document.createElement('td');
                td.textContent = row[col.key] || '';
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
    }

    // Métodos para filtros y búsqueda
    setupTableFilters(tableId, columns) {
        const table = document.getElementById(tableId);
        if (!table) return;
        
        // Crear filtros
        const filterRow = document.createElement('tr');
        columns.forEach(col => {
            const th = document.createElement('th');
            const input = document.createElement('input');
            input.type = 'text';
            input.className = 'form-control form-control-sm';
            input.placeholder = `Filtrar ${col.label}`;
            input.addEventListener('input', (e) => {
                this.filterTable(tableId, e.target.value, col.key);
            });
            th.appendChild(input);
            filterRow.appendChild(th);
        });
        
        table.querySelector('thead').appendChild(filterRow);
    }

    filterTable(tableId, searchTerm, columnKey) {
        const table = document.getElementById(tableId);
        const rows = table.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            const cell = row.querySelector(`td[data-column="${columnKey}"]`);
            if (cell) {
                const text = cell.textContent.toLowerCase();
                const match = text.includes(searchTerm.toLowerCase());
                row.style.display = match ? '' : 'none';
            }
        });
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.adminUI = new CRUNEVOAdminUI();
});

// Funciones globales para compatibilidad
function refreshStats() {
    if (window.adminUI) {
        window.adminUI.refreshDashboardData();
    }
}

function exportDashboardData() {
    if (window.adminUI) {
        window.adminUI.exportDashboardData();
    }
}

function toggleMaintenance() {
    if (window.adminUI) {
        window.adminUI.toggleMaintenanceMode();
    }
}

// Funciones para modales y detalles
function viewUserDetails(userId) {
    fetch(`/admin/api/user/${userId}`)
        .then(response => response.json())
        .then(data => {
            const modal = new bootstrap.Modal(document.getElementById('userDetailsModal'));
            document.getElementById('userDetailsContent').innerHTML = `
                <div class="row">
                    <div class="col-md-4 text-center">
                        <img src="${data.avatar_url}" class="rounded-circle mb-3" width="100" height="100">
                        <h5>${data.username}</h5>
                        <span class="badge bg-${data.role === 'admin' ? 'danger' : 'primary'}">${data.role}</span>
                    </div>
                    <div class="col-md-8">
                        <h6>Información del Usuario</h6>
                        <ul class="list-unstyled">
                            <li><strong>Email:</strong> ${data.email}</li>
                            <li><strong>Carrera:</strong> ${data.career || 'No especificada'}</li>
                            <li><strong>Puntos:</strong> ${data.points}</li>
                            <li><strong>Crolars:</strong> ${data.credits}</li>
                            <li><strong>Fecha de registro:</strong> ${window.adminUI.formatDate(data.created_at)}</li>
                            <li><strong>Estado:</strong> <span class="badge bg-${data.activated ? 'success' : 'warning'}">${data.activated ? 'Activado' : 'Pendiente'}</span></li>
                        </ul>
                    </div>
                </div>
            `;
            modal.show();
        })
        .catch(error => {
            console.error('Error loading user details:', error);
            if (window.adminUI) {
                window.adminUI.showNotification('Error al cargar detalles del usuario', 'error');
            }
        });
}

function viewClubDetails(clubId) {
    fetch(`/admin/api/club/${clubId}`)
        .then(response => response.json())
        .then(data => {
            const modal = new bootstrap.Modal(document.getElementById('clubDetailsModal'));
            document.getElementById('clubDetailsContent').innerHTML = `
                <div class="row">
                    <div class="col-md-4 text-center">
                        <div class="bg-primary rounded-circle d-flex align-items-center justify-content-center mx-auto mb-3" style="width: 100px; height: 100px;">
                            <i class="bi bi-people text-white" style="font-size: 2rem;"></i>
                        </div>
                        <h5>${data.name}</h5>
                        <span class="badge bg-primary">${data.category}</span>
                    </div>
                    <div class="col-md-8">
                        <h6>Información del Club</h6>
                        <ul class="list-unstyled">
                            <li><strong>Descripción:</strong> ${data.description || 'Sin descripción'}</li>
                            <li><strong>Miembros:</strong> ${data.member_count}</li>
                            <li><strong>Creado:</strong> ${window.adminUI.formatDate(data.created_at)}</li>
                            <li><strong>Estado:</strong> <span class="badge bg-${data.is_active ? 'success' : 'secondary'}">${data.is_active ? 'Activo' : 'Inactivo'}</span></li>
                        </ul>
                    </div>
                </div>
            `;
            modal.show();
        })
        .catch(error => {
            console.error('Error loading club details:', error);
            if (window.adminUI) {
                window.adminUI.showNotification('Error al cargar detalles del club', 'error');
            }
        });
}
