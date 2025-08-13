/**
 * Enhanced Error Handling System
 * Provides comprehensive error management with user-friendly feedback
 */

class ErrorHandler {
    constructor() {
        this.errorQueue = [];
        this.errorHistory = [];
        this.maxHistorySize = 100;
        this.retryAttempts = new Map();
        this.maxRetries = 3;
        this.retryDelay = 1000;
        this.isOnline = navigator.onLine;
        this.initializeErrorHandling();
        this.setupNetworkMonitoring();
    }

    /**
     * Initialize global error handling
     */
    initializeErrorHandling() {
        // Handle uncaught JavaScript errors
        window.addEventListener('error', (event) => {
            this.handleJavaScriptError({
                message: event.message,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                error: event.error
            });
        });

        // Handle unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.handlePromiseRejection({
                reason: event.reason,
                promise: event.promise
            });
        });

        // Handle fetch errors globally
        this.interceptFetch();
    }

    /**
     * Setup network monitoring
     */
    setupNetworkMonitoring() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.showNotification('Conexión restaurada', 'success');
            this.retryFailedRequests();
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.showNotification('Sin conexión a internet', 'warning', { persistent: true });
        });
    }

    /**
     * Intercept fetch requests to handle errors globally
     */
    interceptFetch() {
        const originalFetch = window.fetch;
        
        window.fetch = async (...args) => {
            try {
                const response = await originalFetch(...args);
                
                if (!response.ok) {
                    await this.handleHttpError(response, args[0]);
                }
                
                return response;
            } catch (error) {
                return this.handleNetworkError(error, args[0]);
            }
        };
    }

    /**
     * Handle JavaScript runtime errors
     */
    handleJavaScriptError(errorInfo) {
        const error = {
            type: 'javascript',
            message: errorInfo.message,
            stack: errorInfo.error?.stack,
            location: `${errorInfo.filename}:${errorInfo.lineno}:${errorInfo.colno}`,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            url: window.location.href
        };

        this.logError(error);
        
        // Show user-friendly message for critical errors
        if (this.isCriticalError(error)) {
            this.showErrorDialog({
                title: 'Error inesperado',
                message: 'Ha ocurrido un error inesperado. La página se recargará automáticamente.',
                actions: [
                    {
                        label: 'Recargar ahora',
                        action: () => window.location.reload(),
                        primary: true
                    },
                    {
                        label: 'Reportar error',
                        action: () => this.reportError(error)
                    }
                ]
            });
        }
    }

    /**
     * Handle unhandled promise rejections
     */
    handlePromiseRejection(rejectionInfo) {
        const error = {
            type: 'promise_rejection',
            message: rejectionInfo.reason?.message || String(rejectionInfo.reason),
            stack: rejectionInfo.reason?.stack,
            timestamp: new Date().toISOString(),
            url: window.location.href
        };

        this.logError(error);
        
        // Show notification for promise rejections
        this.showNotification(
            'Error en operación asíncrona',
            'error',
            { 
                details: error.message,
                action: {
                    label: 'Reintentar',
                    callback: () => this.suggestRetry()
                }
            }
        );
    }

    /**
     * Handle HTTP errors
     */
    async handleHttpError(response, url) {
        let errorData;
        
        try {
            errorData = await response.json();
        } catch {
            errorData = { message: response.statusText };
        }

        const error = {
            type: 'http',
            status: response.status,
            statusText: response.statusText,
            url: url,
            message: errorData.message || 'Error en la solicitud',
            details: errorData.details || errorData.errors,
            timestamp: new Date().toISOString()
        };

        this.logError(error);
        
        // Handle specific HTTP status codes
        switch (response.status) {
            case 400:
                this.handleValidationError(error);
                break;
            case 401:
                this.handleAuthenticationError(error);
                break;
            case 403:
                this.handleAuthorizationError(error);
                break;
            case 404:
                this.handleNotFoundError(error);
                break;
            case 429:
                this.handleRateLimitError(error);
                break;
            case 500:
            case 502:
            case 503:
            case 504:
                this.handleServerError(error);
                break;
            default:
                this.handleGenericHttpError(error);
        }

        throw error; // Re-throw to allow caller to handle
    }

    /**
     * Handle network errors
     */
    handleNetworkError(error, url) {
        const networkError = {
            type: 'network',
            message: error.message,
            url: url,
            timestamp: new Date().toISOString(),
            isOnline: this.isOnline
        };

        this.logError(networkError);
        
        if (!this.isOnline) {
            this.showNotification(
                'Sin conexión a internet',
                'warning',
                {
                    persistent: true,
                    action: {
                        label: 'Reintentar cuando vuelva la conexión',
                        callback: () => this.queueForRetry(url)
                    }
                }
            );
        } else {
            this.showNotification(
                'Error de conexión',
                'error',
                {
                    details: 'No se pudo conectar con el servidor',
                    action: {
                        label: 'Reintentar',
                        callback: () => this.retryRequest(url)
                    }
                }
            );
        }

        throw networkError;
    }

    /**
     * Handle validation errors (400)
     */
    handleValidationError(error) {
        const message = Array.isArray(error.details) 
            ? error.details.map(e => e.message || e).join(', ')
            : error.message;

        this.showNotification(
            'Error de validación',
            'warning',
            {
                details: message,
                duration: 5000
            }
        );
    }

    /**
     * Handle authentication errors (401)
     */
    handleAuthenticationError(error) {
        this.showErrorDialog({
            title: 'Sesión expirada',
            message: 'Su sesión ha expirado. Por favor, inicie sesión nuevamente.',
            actions: [
                {
                    label: 'Iniciar sesión',
                    action: () => this.redirectToLogin(),
                    primary: true
                },
                {
                    label: 'Cancelar',
                    action: () => {}
                }
            ]
        });
    }

    /**
     * Handle authorization errors (403)
     */
    handleAuthorizationError(error) {
        this.showNotification(
            'Acceso denegado',
            'error',
            {
                details: 'No tiene permisos para realizar esta acción',
                duration: 5000
            }
        );
    }

    /**
     * Handle not found errors (404)
     */
    handleNotFoundError(error) {
        this.showNotification(
            'Recurso no encontrado',
            'warning',
            {
                details: 'El recurso solicitado no existe o ha sido movido',
                duration: 4000
            }
        );
    }

    /**
     * Handle rate limit errors (429)
     */
    handleRateLimitError(error) {
        this.showNotification(
            'Demasiadas solicitudes',
            'warning',
            {
                details: 'Por favor, espere un momento antes de intentar nuevamente',
                duration: 6000,
                action: {
                    label: 'Reintentar en 30s',
                    callback: () => setTimeout(() => this.retryRequest(error.url), 30000)
                }
            }
        );
    }

    /**
     * Handle server errors (5xx)
     */
    handleServerError(error) {
        const retryKey = error.url;
        const attempts = this.retryAttempts.get(retryKey) || 0;

        if (attempts < this.maxRetries) {
            this.retryAttempts.set(retryKey, attempts + 1);
            
            this.showNotification(
                'Error del servidor',
                'error',
                {
                    details: `Reintentando automáticamente... (${attempts + 1}/${this.maxRetries})`,
                    duration: 3000
                }
            );

            setTimeout(() => {
                this.retryRequest(error.url);
            }, this.retryDelay * Math.pow(2, attempts)); // Exponential backoff
        } else {
            this.showErrorDialog({
                title: 'Error del servidor',
                message: 'El servidor no está disponible en este momento. Por favor, inténtelo más tarde.',
                actions: [
                    {
                        label: 'Reintentar',
                        action: () => {
                            this.retryAttempts.delete(retryKey);
                            this.retryRequest(error.url);
                        },
                        primary: true
                    },
                    {
                        label: 'Reportar problema',
                        action: () => this.reportError(error)
                    }
                ]
            });
        }
    }

    /**
     * Handle generic HTTP errors
     */
    handleGenericHttpError(error) {
        this.showNotification(
            `Error HTTP ${error.status}`,
            'error',
            {
                details: error.message,
                duration: 4000
            }
        );
    }

    /**
     * Show error notification
     */
    showNotification(title, type = 'info', options = {}) {
        // Use toast library if available, otherwise create custom notification
        if (window.toast) {
            const toastOptions = {
                title,
                type,
                duration: options.duration || 4000,
                persistent: options.persistent || false
            };

            if (options.details) {
                toastOptions.description = options.details;
            }

            if (options.action) {
                toastOptions.action = {
                    label: options.action.label,
                    onClick: options.action.callback
                };
            }

            window.toast(toastOptions);
        } else {
            this.createCustomNotification(title, type, options);
        }
    }

    /**
     * Create custom notification when toast library is not available
     */
    createCustomNotification(title, type, options) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-title">${title}</div>
                ${options.details ? `<div class="notification-details">${options.details}</div>` : ''}
                ${options.action ? `<button class="notification-action">${options.action.label}</button>` : ''}
            </div>
            <button class="notification-close">&times;</button>
        `;

        // Add event listeners
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.addEventListener('click', () => notification.remove());

        if (options.action) {
            const actionBtn = notification.querySelector('.notification-action');
            actionBtn.addEventListener('click', () => {
                options.action.callback();
                notification.remove();
            });
        }

        // Add to page
        let container = document.querySelector('.notification-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'notification-container';
            document.body.appendChild(container);
        }

        container.appendChild(notification);

        // Auto-remove if not persistent
        if (!options.persistent) {
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, options.duration || 4000);
        }
    }

    /**
     * Show error dialog
     */
    showErrorDialog(config) {
        // Use modal library if available, otherwise create custom dialog
        if (window.showModal) {
            window.showModal({
                title: config.title,
                content: config.message,
                buttons: config.actions.map(action => ({
                    text: action.label,
                    onClick: action.action,
                    primary: action.primary
                }))
            });
        } else {
            this.createCustomDialog(config);
        }
    }

    /**
     * Create custom error dialog
     */
    createCustomDialog(config) {
        const overlay = document.createElement('div');
        overlay.className = 'error-dialog-overlay';
        
        const dialog = document.createElement('div');
        dialog.className = 'error-dialog';
        dialog.innerHTML = `
            <div class="error-dialog-header">
                <h3>${config.title}</h3>
            </div>
            <div class="error-dialog-body">
                <p>${config.message}</p>
            </div>
            <div class="error-dialog-footer">
                ${config.actions.map(action => 
                    `<button class="btn ${action.primary ? 'btn-primary' : 'btn-secondary'}" data-action="${action.label}">
                        ${action.label}
                    </button>`
                ).join('')}
            </div>
        `;

        overlay.appendChild(dialog);
        document.body.appendChild(overlay);

        // Add event listeners
        config.actions.forEach(action => {
            const button = dialog.querySelector(`[data-action="${action.label}"]`);
            button.addEventListener('click', () => {
                action.action();
                overlay.remove();
            });
        });

        // Close on overlay click
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                overlay.remove();
            }
        });
    }

    /**
     * Log error for debugging and analytics
     */
    logError(error) {
        // Add to history
        this.errorHistory.unshift(error);
        if (this.errorHistory.length > this.maxHistorySize) {
            this.errorHistory.pop();
        }

        // Console log for development
        if (process.env.NODE_ENV === 'development') {
            console.error('Error logged:', error);
        }

        // Send to analytics service if available
        if (window.analytics && typeof window.analytics.track === 'function') {
            window.analytics.track('Error Occurred', {
                errorType: error.type,
                errorMessage: error.message,
                errorUrl: error.url,
                timestamp: error.timestamp
            });
        }
    }

    /**
     * Check if error is critical
     */
    isCriticalError(error) {
        const criticalPatterns = [
            /Cannot read property.*of undefined/,
            /Cannot read properties.*of undefined/,
            /Script error/,
            /ChunkLoadError/,
            /Loading chunk \d+ failed/
        ];

        return criticalPatterns.some(pattern => pattern.test(error.message));
    }

    /**
     * Retry a failed request
     */
    async retryRequest(url) {
        try {
            const response = await fetch(url);
            if (response.ok) {
                this.showNotification('Operación completada', 'success');
                this.retryAttempts.delete(url);
            }
            return response;
        } catch (error) {
            // Error will be handled by the intercepted fetch
            throw error;
        }
    }

    /**
     * Queue request for retry when connection is restored
     */
    queueForRetry(url) {
        if (!this.errorQueue.includes(url)) {
            this.errorQueue.push(url);
        }
    }

    /**
     * Retry all failed requests
     */
    async retryFailedRequests() {
        const requests = [...this.errorQueue];
        this.errorQueue = [];

        for (const url of requests) {
            try {
                await this.retryRequest(url);
            } catch (error) {
                // Request will be re-queued if it fails again
            }
        }
    }

    /**
     * Redirect to login page
     */
    redirectToLogin() {
        const currentUrl = encodeURIComponent(window.location.href);
        window.location.href = `/login?redirect=${currentUrl}`;
    }

    /**
     * Report error to support
     */
    reportError(error) {
        // Implementation would depend on your error reporting service
        console.log('Reporting error:', error);
        
        this.showNotification(
            'Error reportado',
            'success',
            {
                details: 'Gracias por reportar este problema. Nuestro equipo lo revisará.',
                duration: 3000
            }
        );
    }

    /**
     * Suggest retry action
     */
    suggestRetry() {
        this.showNotification(
            'Sugerencia',
            'info',
            {
                details: 'Intente recargar la página o repetir la última acción',
                action: {
                    label: 'Recargar página',
                    callback: () => window.location.reload()
                }
            }
        );
    }

    /**
     * Get error statistics
     */
    getErrorStats() {
        const stats = {
            total: this.errorHistory.length,
            byType: {},
            recent: this.errorHistory.slice(0, 10)
        };

        this.errorHistory.forEach(error => {
            stats.byType[error.type] = (stats.byType[error.type] || 0) + 1;
        });

        return stats;
    }

    /**
     * Clear error history
     */
    clearErrorHistory() {
        this.errorHistory = [];
        this.retryAttempts.clear();
    }
}

// Global error handler instance
window.ErrorHandler = ErrorHandler;
window.errorHandler = new ErrorHandler();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ErrorHandler;
}