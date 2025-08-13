/**
 * Micro-Interactions System
 * Handles smooth animations, transitions, and user feedback
 */

class MicroInteractions {
    constructor() {
        this.observers = new Map();
        this.animationQueue = [];
        this.isProcessingQueue = false;
        this.reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        
        this.init();
    }

    init() {
        this.setupIntersectionObserver();
        this.setupHoverEffects();
        this.setupClickEffects();
        this.setupFormInteractions();
        this.setupScrollAnimations();
        this.setupLoadingAnimations();
        this.setupToastAnimations();
        this.setupModalAnimations();
        this.setupDragAnimations();
        this.bindEvents();
    }

    // ===== INTERSECTION OBSERVER FOR SCROLL ANIMATIONS =====
    setupIntersectionObserver() {
        if ('IntersectionObserver' in window && !this.reducedMotion) {
            const observer = new IntersectionObserver(
                (entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            this.animateOnScroll(entry.target);
                            observer.unobserve(entry.target);
                        }
                    });
                },
                {
                    threshold: 0.1,
                    rootMargin: '0px 0px -50px 0px'
                }
            );

            // Observe elements with animate-on-scroll class
            document.querySelectorAll('.animate-on-scroll').forEach(el => {
                observer.observe(el);
            });

            this.observers.set('scroll', observer);
        }
    }

    // ===== HOVER EFFECTS =====
    setupHoverEffects() {
        if (this.reducedMotion) return;

        // Enhanced hover effects for blocks
        this.addHoverEffect('.block', {
            enter: (el) => {
                el.style.transform = 'translateY(-2px)';
                el.style.boxShadow = '0 8px 25px rgba(0, 0, 0, 0.15)';
                el.style.transition = 'all 0.25s cubic-bezier(0.25, 1, 0.5, 1)';
            },
            leave: (el) => {
                el.style.transform = '';
                el.style.boxShadow = '';
            }
        });

        // Button hover effects
        this.addHoverEffect('.btn', {
            enter: (el) => {
                if (!el.disabled) {
                    el.style.transform = 'translateY(-1px)';
                    el.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
                }
            },
            leave: (el) => {
                el.style.transform = '';
                el.style.boxShadow = '';
            }
        });

        // Card hover effects
        this.addHoverEffect('.card', {
            enter: (el) => {
                el.style.transform = 'scale(1.02)';
                el.style.transition = 'transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)';
            },
            leave: (el) => {
                el.style.transform = '';
            }
        });
    }

    addHoverEffect(selector, effects) {
        document.addEventListener('mouseover', (e) => {
            if (e.target.matches(selector) || e.target.closest(selector)) {
                const element = e.target.matches(selector) ? e.target : e.target.closest(selector);
                effects.enter(element);
            }
        });

        document.addEventListener('mouseout', (e) => {
            if (e.target.matches(selector) || e.target.closest(selector)) {
                const element = e.target.matches(selector) ? e.target : e.target.closest(selector);
                effects.leave(element);
            }
        });
    }

    // ===== CLICK EFFECTS =====
    setupClickEffects() {
        if (this.reducedMotion) return;

        // Ripple effect for buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('.btn') || e.target.closest('.btn')) {
                const button = e.target.matches('.btn') ? e.target : e.target.closest('.btn');
                this.createRipple(button, e);
            }
        });

        // Press effect for interactive elements
        document.addEventListener('mousedown', (e) => {
            if (e.target.matches('.btn, .block, .card') || e.target.closest('.btn, .block, .card')) {
                const element = e.target.matches('.btn, .block, .card') ? e.target : e.target.closest('.btn, .block, .card');
                this.addPressEffect(element);
            }
        });

        document.addEventListener('mouseup', (e) => {
            if (e.target.matches('.btn, .block, .card') || e.target.closest('.btn, .block, .card')) {
                const element = e.target.matches('.btn, .block, .card') ? e.target : e.target.closest('.btn, .block, .card');
                this.removePressEffect(element);
            }
        });
    }

    createRipple(element, event) {
        const rect = element.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;

        const ripple = document.createElement('span');
        ripple.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            background: rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            transform: scale(0);
            animation: ripple 0.6s linear;
            pointer-events: none;
            z-index: 1;
        `;

        // Ensure button has relative positioning
        if (getComputedStyle(element).position === 'static') {
            element.style.position = 'relative';
        }
        element.style.overflow = 'hidden';

        element.appendChild(ripple);

        // Remove ripple after animation
        setTimeout(() => {
            if (ripple.parentNode) {
                ripple.parentNode.removeChild(ripple);
            }
        }, 600);
    }

    addPressEffect(element) {
        element.style.transform = 'scale(0.98)';
        element.style.transition = 'transform 0.1s ease-out';
    }

    removePressEffect(element) {
        setTimeout(() => {
            element.style.transform = '';
        }, 100);
    }

    // ===== FORM INTERACTIONS =====
    setupFormInteractions() {
        if (this.reducedMotion) return;

        // Focus animations for form controls
        document.addEventListener('focusin', (e) => {
            if (e.target.matches('.form-control, input, textarea, select')) {
                this.animateFormFocus(e.target, true);
            }
        });

        document.addEventListener('focusout', (e) => {
            if (e.target.matches('.form-control, input, textarea, select')) {
                this.animateFormFocus(e.target, false);
            }
        });

        // Input validation animations
        document.addEventListener('input', (e) => {
            if (e.target.matches('.form-control, input, textarea')) {
                this.validateInput(e.target);
            }
        });
    }

    animateFormFocus(element, isFocused) {
        if (isFocused) {
            element.style.transform = 'scale(1.02)';
            element.style.boxShadow = '0 0 0 3px rgba(var(--primary-rgb, 59, 130, 246), 0.1)';
            element.style.transition = 'all 0.2s cubic-bezier(0.25, 1, 0.5, 1)';
        } else {
            element.style.transform = '';
            element.style.boxShadow = '';
        }
    }

    validateInput(element) {
        const isValid = element.checkValidity();
        
        if (!isValid && element.value.length > 0) {
            this.shakeElement(element);
            element.classList.add('is-invalid');
        } else {
            element.classList.remove('is-invalid');
        }
    }

    shakeElement(element) {
        if (this.reducedMotion) return;
        
        element.style.animation = 'shake 0.5s cubic-bezier(0.36, 0.07, 0.19, 0.97)';
        setTimeout(() => {
            element.style.animation = '';
        }, 500);
    }

    // ===== SCROLL ANIMATIONS =====
    setupScrollAnimations() {
        if (this.reducedMotion) return;

        // Parallax effect for hero sections
        window.addEventListener('scroll', this.throttle(() => {
            this.updateParallax();
            this.updateScrollProgress();
        }, 16));
    }

    animateOnScroll(element) {
        if (this.reducedMotion) return;

        element.classList.add('in-view');
        
        // Add stagger effect for children
        if (element.classList.contains('stagger-children')) {
            const children = element.children;
            Array.from(children).forEach((child, index) => {
                setTimeout(() => {
                    child.style.opacity = '1';
                    child.style.transform = 'translateY(0)';
                }, index * 100);
            });
        }
    }

    updateParallax() {
        const scrolled = window.pageYOffset;
        const parallaxElements = document.querySelectorAll('.parallax');
        
        parallaxElements.forEach(element => {
            const speed = element.dataset.speed || 0.5;
            const yPos = -(scrolled * speed);
            element.style.transform = `translateY(${yPos}px)`;
        });
    }

    updateScrollProgress() {
        const progressBars = document.querySelectorAll('.scroll-progress');
        const scrollTop = window.pageYOffset;
        const docHeight = document.documentElement.scrollHeight - window.innerHeight;
        const scrollPercent = (scrollTop / docHeight) * 100;
        
        progressBars.forEach(bar => {
            bar.style.width = `${scrollPercent}%`;
        });
    }

    // ===== LOADING ANIMATIONS =====
    setupLoadingAnimations() {
        // Skeleton loading animation
        this.animateSkeletons();
        
        // Progress bar animations
        this.animateProgressBars();
    }

    animateSkeletons() {
        const skeletons = document.querySelectorAll('.skeleton');
        skeletons.forEach(skeleton => {
            if (!this.reducedMotion) {
                skeleton.style.backgroundSize = '200% 100%';
                skeleton.style.animation = 'shimmer 1.5s infinite';
            }
        });
    }

    animateProgressBars() {
        const progressBars = document.querySelectorAll('.progress-bar[data-progress]');
        progressBars.forEach(bar => {
            const progress = bar.dataset.progress;
            if (!this.reducedMotion) {
                bar.style.width = '0%';
                setTimeout(() => {
                    bar.style.transition = 'width 1s cubic-bezier(0.25, 1, 0.5, 1)';
                    bar.style.width = `${progress}%`;
                }, 100);
            } else {
                bar.style.width = `${progress}%`;
            }
        });
    }

    // ===== TOAST ANIMATIONS =====
    setupToastAnimations() {
        // Observer for toast elements
        const toastObserver = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1 && node.classList.contains('toast')) {
                        this.animateToast(node, 'in');
                    }
                });
            });
        });

        const toastContainer = document.querySelector('.toast-container');
        if (toastContainer) {
            toastObserver.observe(toastContainer, { childList: true });
        }
    }

    animateToast(toast, direction) {
        if (this.reducedMotion) {
            toast.classList.add('show');
            return;
        }

        if (direction === 'in') {
            toast.style.transform = 'translateX(100%)';
            toast.style.opacity = '0';
            
            requestAnimationFrame(() => {
                toast.style.transition = 'all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)';
                toast.style.transform = 'translateX(0)';
                toast.style.opacity = '1';
                toast.classList.add('show');
            });
        } else {
            toast.style.transition = 'all 0.3s cubic-bezier(0.25, 1, 0.5, 1)';
            toast.style.transform = 'translateX(100%)';
            toast.style.opacity = '0';
            
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }
    }

    // ===== MODAL ANIMATIONS =====
    setupModalAnimations() {
        document.addEventListener('show.bs.modal', (e) => {
            this.animateModal(e.target, 'in');
        });

        document.addEventListener('hide.bs.modal', (e) => {
            this.animateModal(e.target, 'out');
        });
    }

    animateModal(modal, direction) {
        if (this.reducedMotion) return;

        const modalDialog = modal.querySelector('.modal-dialog');
        if (!modalDialog) return;

        if (direction === 'in') {
            modalDialog.style.transform = 'scale(0.9) translateY(-50px)';
            modalDialog.style.opacity = '0';
            
            requestAnimationFrame(() => {
                modalDialog.style.transition = 'all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)';
                modalDialog.style.transform = 'scale(1) translateY(0)';
                modalDialog.style.opacity = '1';
            });
        } else {
            modalDialog.style.transition = 'all 0.2s cubic-bezier(0.25, 1, 0.5, 1)';
            modalDialog.style.transform = 'scale(0.9) translateY(-50px)';
            modalDialog.style.opacity = '0';
        }
    }

    // ===== DRAG ANIMATIONS =====
    setupDragAnimations() {
        document.addEventListener('dragstart', (e) => {
            if (e.target.classList.contains('block')) {
                this.animateDragStart(e.target);
            }
        });

        document.addEventListener('dragend', (e) => {
            if (e.target.classList.contains('block')) {
                this.animateDragEnd(e.target);
            }
        });

        document.addEventListener('dragover', (e) => {
            const dropTarget = e.target.closest('.drop-zone');
            if (dropTarget) {
                this.animateDropTarget(dropTarget, true);
            }
        });

        document.addEventListener('dragleave', (e) => {
            const dropTarget = e.target.closest('.drop-zone');
            if (dropTarget) {
                this.animateDropTarget(dropTarget, false);
            }
        });
    }

    animateDragStart(element) {
        if (this.reducedMotion) return;
        
        element.style.transform = 'rotate(5deg) scale(1.05)';
        element.style.opacity = '0.8';
        element.style.zIndex = '1000';
        element.style.transition = 'all 0.2s cubic-bezier(0.25, 1, 0.5, 1)';
        element.classList.add('dragging');
    }

    animateDragEnd(element) {
        element.style.transform = '';
        element.style.opacity = '';
        element.style.zIndex = '';
        element.classList.remove('dragging');
    }

    animateDropTarget(element, isActive) {
        if (this.reducedMotion) return;
        
        if (isActive) {
            element.style.transform = 'scale(1.02)';
            element.style.boxShadow = '0 0 0 2px rgba(var(--primary-rgb, 59, 130, 246), 0.5)';
            element.style.backgroundColor = 'rgba(var(--primary-rgb, 59, 130, 246), 0.05)';
            element.classList.add('drop-target');
        } else {
            element.style.transform = '';
            element.style.boxShadow = '';
            element.style.backgroundColor = '';
            element.classList.remove('drop-target');
        }
    }

    // ===== UTILITY METHODS =====
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // ===== PUBLIC API =====
    
    // Add custom animation to queue
    queueAnimation(element, animation, options = {}) {
        this.animationQueue.push({
            element,
            animation,
            options,
            timestamp: Date.now()
        });
        
        if (!this.isProcessingQueue) {
            this.processAnimationQueue();
        }
    }

    async processAnimationQueue() {
        this.isProcessingQueue = true;
        
        while (this.animationQueue.length > 0) {
            const { element, animation, options } = this.animationQueue.shift();
            await this.executeAnimation(element, animation, options);
        }
        
        this.isProcessingQueue = false;
    }

    executeAnimation(element, animation, options) {
        return new Promise((resolve) => {
            if (this.reducedMotion) {
                resolve();
                return;
            }

            const duration = options.duration || 300;
            const easing = options.easing || 'cubic-bezier(0.25, 1, 0.5, 1)';
            
            element.style.transition = `all ${duration}ms ${easing}`;
            
            // Apply animation styles
            Object.assign(element.style, animation);
            
            setTimeout(() => {
                if (options.reset) {
                    Object.keys(animation).forEach(key => {
                        element.style[key] = '';
                    });
                }
                resolve();
            }, duration);
        });
    }

    // Show notification with animation
    showNotification(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        const container = document.querySelector('.notification-container') || document.body;
        container.appendChild(notification);
        
        this.animateToast(notification, 'in');
        
        setTimeout(() => {
            this.animateToast(notification, 'out');
        }, duration);
    }

    // Animate element entrance
    animateIn(element, animation = 'fadeInUp') {
        if (this.reducedMotion) {
            element.style.opacity = '1';
            return;
        }
        
        element.classList.add(animation);
        element.addEventListener('animationend', () => {
            element.classList.remove(animation);
        }, { once: true });
    }

    // Animate element exit
    animateOut(element, animation = 'fadeOut') {
        return new Promise((resolve) => {
            if (this.reducedMotion) {
                resolve();
                return;
            }
            
            element.classList.add(animation);
            element.addEventListener('animationend', () => {
                element.classList.remove(animation);
                resolve();
            }, { once: true });
        });
    }

    // Pulse animation for attention
    pulse(element, duration = 1000) {
        if (this.reducedMotion) return;
        
        element.style.animation = `pulse ${duration}ms cubic-bezier(0.4, 0, 0.6, 1)`;
        setTimeout(() => {
            element.style.animation = '';
        }, duration);
    }

    // Highlight element temporarily
    highlight(element, color = 'rgba(255, 235, 59, 0.3)', duration = 2000) {
        if (this.reducedMotion) return;
        
        const originalBackground = element.style.backgroundColor;
        element.style.transition = 'background-color 0.3s ease';
        element.style.backgroundColor = color;
        
        setTimeout(() => {
            element.style.backgroundColor = originalBackground;
            setTimeout(() => {
                element.style.transition = '';
            }, 300);
        }, duration);
    }

    // Cleanup method
    destroy() {
        this.observers.forEach(observer => observer.disconnect());
        this.observers.clear();
        this.animationQueue = [];
    }

    // Event binding
    bindEvents() {
        // Handle reduced motion preference changes
        const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
        mediaQuery.addListener((e) => {
            this.reducedMotion = e.matches;
        });

        // Handle visibility change
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                // Pause animations when tab is not visible
                document.body.style.animationPlayState = 'paused';
            } else {
                document.body.style.animationPlayState = 'running';
            }
        });
    }
}

// CSS for ripple effect
const rippleCSS = `
@keyframes ripple {
    to {
        transform: scale(4);
        opacity: 0;
    }
}
`;

// Add CSS to document
if (!document.querySelector('#micro-interactions-css')) {
    const style = document.createElement('style');
    style.id = 'micro-interactions-css';
    style.textContent = rippleCSS;
    document.head.appendChild(style);
}

// Initialize micro-interactions when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.microInteractions = new MicroInteractions();
    });
} else {
    window.microInteractions = new MicroInteractions();
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MicroInteractions;
}