/**
 * Performance Optimization System
 * Handles resource loading, caching, and performance monitoring
 */

class PerformanceOptimizer {
    constructor() {
        this.cache = new Map();
        this.loadingStates = new Map();
        this.performanceMetrics = {
            pageLoadTime: 0,
            resourceLoadTimes: {},
            interactionTimes: {},
            memoryUsage: 0
        };
        this.observers = {
            intersection: null,
            mutation: null,
            performance: null
        };
        this.lazyLoadQueue = new Set();
        this.prefetchQueue = new Set();
        this.criticalResources = new Set();
        
        this.initializePerformanceMonitoring();
        this.setupLazyLoading();
        this.setupResourceOptimization();
        this.setupMemoryManagement();
    }

    /**
     * Initialize performance monitoring
     */
    initializePerformanceMonitoring() {
        // Monitor page load performance
        if (typeof PerformanceObserver !== 'undefined') {
            // Navigation timing
            this.observers.performance = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    this.recordPerformanceEntry(entry);
                }
            });
            
            this.observers.performance.observe({ 
                entryTypes: ['navigation', 'resource', 'measure', 'paint'] 
            });
        }

        // Monitor Core Web Vitals
        this.monitorCoreWebVitals();

        // Track page load time
        window.addEventListener('load', () => {
            this.performanceMetrics.pageLoadTime = performance.now();
            this.optimizeAfterLoad();
        });

        // Monitor memory usage
        if ('memory' in performance) {
            setInterval(() => {
                this.performanceMetrics.memoryUsage = performance.memory.usedJSHeapSize;
                this.checkMemoryUsage();
            }, 30000); // Check every 30 seconds
        }
    }

    /**
     * Monitor Core Web Vitals
     */
    monitorCoreWebVitals() {
        // Largest Contentful Paint (LCP)
        if (typeof PerformanceObserver !== 'undefined') {
            new PerformanceObserver((entryList) => {
                const entries = entryList.getEntries();
                const lastEntry = entries[entries.length - 1];
                this.performanceMetrics.lcp = lastEntry.startTime;
                
                if (lastEntry.startTime > 2500) {
                    this.optimizeLCP();
                }
            }).observe({ entryTypes: ['largest-contentful-paint'] });
        }

        // First Input Delay (FID)
        if (typeof PerformanceObserver !== 'undefined') {
            new PerformanceObserver((entryList) => {
                for (const entry of entryList.getEntries()) {
                    this.performanceMetrics.fid = entry.processingStart - entry.startTime;
                    
                    if (entry.processingStart - entry.startTime > 100) {
                        this.optimizeFID();
                    }
                }
            }).observe({ entryTypes: ['first-input'] });
        }

        // Cumulative Layout Shift (CLS)
        let clsValue = 0;
        if (typeof PerformanceObserver !== 'undefined') {
            new PerformanceObserver((entryList) => {
                for (const entry of entryList.getEntries()) {
                    if (!entry.hadRecentInput) {
                        clsValue += entry.value;
                        this.performanceMetrics.cls = clsValue;
                        
                        if (clsValue > 0.1) {
                            this.optimizeCLS();
                        }
                    }
                }
            }).observe({ entryTypes: ['layout-shift'] });
        }
    }

    /**
     * Setup lazy loading for images and content
     */
    setupLazyLoading() {
        // Intersection Observer for lazy loading
        if ('IntersectionObserver' in window) {
            this.observers.intersection = new IntersectionObserver(
                (entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            this.loadLazyElement(entry.target);
                            this.observers.intersection.unobserve(entry.target);
                        }
                    });
                },
                {
                    rootMargin: '50px 0px',
                    threshold: 0.01
                }
            );

            // Observe all lazy-loadable elements
            this.observeLazyElements();
        } else {
            // Fallback for browsers without Intersection Observer
            this.setupScrollBasedLazyLoading();
        }
    }

    /**
     * Observe elements for lazy loading
     */
    observeLazyElements() {
        const lazyElements = document.querySelectorAll(
            'img[data-src], [data-lazy], .lazy-load, .block-content[data-type]'
        );
        
        lazyElements.forEach(element => {
            this.observers.intersection.observe(element);
            this.lazyLoadQueue.add(element);
        });
    }

    /**
     * Load a lazy element
     */
    loadLazyElement(element) {
        const startTime = performance.now();
        
        if (element.tagName === 'IMG') {
            this.loadLazyImage(element);
        } else if (element.dataset.lazy) {
            this.loadLazyContent(element);
        } else if (element.classList.contains('block-content')) {
            this.loadLazyBlock(element);
        }

        // Record load time
        const loadTime = performance.now() - startTime;
        this.performanceMetrics.resourceLoadTimes[element.id || 'anonymous'] = loadTime;
        
        this.lazyLoadQueue.delete(element);
    }

    /**
     * Load lazy image
     */
    loadLazyImage(img) {
        const src = img.dataset.src;
        if (!src) return;

        // Create a new image to preload
        const newImg = new Image();
        
        newImg.onload = () => {
            img.src = src;
            img.classList.add('loaded');
            img.removeAttribute('data-src');
        };
        
        newImg.onerror = () => {
            img.classList.add('error');
            img.alt = 'Error al cargar imagen';
        };
        
        newImg.src = src;
    }

    /**
     * Load lazy content
     */
    async loadLazyContent(element) {
        const url = element.dataset.lazy;
        if (!url) return;

        try {
            element.classList.add('loading');
            
            const content = await this.fetchWithCache(url);
            element.innerHTML = content;
            element.classList.remove('loading');
            element.classList.add('loaded');
            
        } catch (error) {
            element.classList.remove('loading');
            element.classList.add('error');
            element.innerHTML = '<p>Error al cargar contenido</p>';
        }
    }

    /**
     * Load lazy block
     */
    async loadLazyBlock(element) {
        const blockType = element.dataset.type;
        const blockId = element.dataset.blockId;
        
        if (!blockType || !blockId) return;

        try {
            element.classList.add('loading');
            
            const blockData = await this.fetchWithCache(`/api/personal-space/blocks/${blockId}`);
            this.renderBlock(element, blockData);
            
            element.classList.remove('loading');
            element.classList.add('loaded');
            
        } catch (error) {
            element.classList.remove('loading');
            element.classList.add('error');
            element.innerHTML = '<p>Error al cargar bloque</p>';
        }
    }

    /**
     * Setup resource optimization
     */
    setupResourceOptimization() {
        // Preload critical resources
        this.preloadCriticalResources();
        
        // Setup resource hints
        this.setupResourceHints();
        
        // Optimize images
        this.optimizeImages();
        
        // Setup service worker for caching
        this.setupServiceWorker();
    }

    /**
     * Preload critical resources
     */
    preloadCriticalResources() {
        const criticalResources = [
            '/static/css/personal-space-performance.css',
            '/static/js/personal-space-enhanced.js',
            '/static/js/validation-system.js'
        ];

        criticalResources.forEach(resource => {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.href = resource;
            link.as = resource.endsWith('.css') ? 'style' : 'script';
            document.head.appendChild(link);
            
            this.criticalResources.add(resource);
        });
    }

    /**
     * Setup resource hints
     */
    setupResourceHints() {
        // DNS prefetch for external domains
        const externalDomains = ['fonts.googleapis.com', 'fonts.gstatic.com'];
        
        externalDomains.forEach(domain => {
            const link = document.createElement('link');
            link.rel = 'dns-prefetch';
            link.href = `//${domain}`;
            document.head.appendChild(link);
        });

        // Prefetch likely next pages
        this.setupPrefetching();
    }

    /**
     * Setup prefetching for likely next pages
     */
    setupPrefetching() {
        // Prefetch on hover with delay
        document.addEventListener('mouseover', (e) => {
            const link = e.target.closest('a[href]');
            if (link && this.shouldPrefetch(link.href)) {
                setTimeout(() => {
                    this.prefetchResource(link.href);
                }, 100);
            }
        });

        // Prefetch on touch start for mobile
        document.addEventListener('touchstart', (e) => {
            const link = e.target.closest('a[href]');
            if (link && this.shouldPrefetch(link.href)) {
                this.prefetchResource(link.href);
            }
        });
    }

    /**
     * Check if resource should be prefetched
     */
    shouldPrefetch(url) {
        // Don't prefetch external links or already prefetched resources
        return url.startsWith('/') && 
               !this.prefetchQueue.has(url) && 
               !url.includes('#') &&
               !url.includes('logout');
    }

    /**
     * Prefetch a resource
     */
    prefetchResource(url) {
        if (this.prefetchQueue.has(url)) return;
        
        const link = document.createElement('link');
        link.rel = 'prefetch';
        link.href = url;
        document.head.appendChild(link);
        
        this.prefetchQueue.add(url);
    }

    /**
     * Optimize images
     */
    optimizeImages() {
        const images = document.querySelectorAll('img');
        
        images.forEach(img => {
            // Add loading="lazy" for non-critical images
            if (!img.hasAttribute('loading') && !this.isCriticalImage(img)) {
                img.loading = 'lazy';
            }

            // Add proper sizing attributes
            if (!img.hasAttribute('width') || !img.hasAttribute('height')) {
                this.addImageDimensions(img);
            }

            // Optimize image format
            this.optimizeImageFormat(img);
        });
    }

    /**
     * Check if image is critical (above the fold)
     */
    isCriticalImage(img) {
        const rect = img.getBoundingClientRect();
        return rect.top < window.innerHeight;
    }

    /**
     * Add image dimensions to prevent layout shift
     */
    addImageDimensions(img) {
        img.onload = () => {
            if (!img.hasAttribute('width')) {
                img.setAttribute('width', img.naturalWidth);
            }
            if (!img.hasAttribute('height')) {
                img.setAttribute('height', img.naturalHeight);
            }
        };
    }

    /**
     * Optimize image format based on browser support
     */
    optimizeImageFormat(img) {
        if (!img.src) return;

        // Check for WebP support
        if (this.supportsWebP() && !img.src.includes('.webp')) {
            const webpSrc = img.src.replace(/\.(jpg|jpeg|png)$/i, '.webp');
            
            // Test if WebP version exists
            const testImg = new Image();
            testImg.onload = () => {
                img.src = webpSrc;
            };
            testImg.src = webpSrc;
        }
    }

    /**
     * Check WebP support
     */
    supportsWebP() {
        if (this._webpSupport !== undefined) {
            return this._webpSupport;
        }

        const canvas = document.createElement('canvas');
        canvas.width = 1;
        canvas.height = 1;
        
        this._webpSupport = canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0;
        return this._webpSupport;
    }

    /**
     * Setup service worker for caching
     */
    setupServiceWorker() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js')
                .then(registration => {
                    console.log('Service Worker registered:', registration);
                })
                .catch(error => {
                    console.log('Service Worker registration failed:', error);
                });
        }
    }

    /**
     * Fetch with caching
     */
    async fetchWithCache(url, options = {}) {
        const cacheKey = `${url}_${JSON.stringify(options)}`;
        
        // Check cache first
        if (this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            if (Date.now() - cached.timestamp < (options.cacheTime || 300000)) { // 5 minutes default
                return cached.data;
            }
        }

        // Fetch from network
        try {
            const response = await fetch(url, options);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.text();
            
            // Cache the result
            this.cache.set(cacheKey, {
                data,
                timestamp: Date.now()
            });
            
            return data;
            
        } catch (error) {
            // Return cached version if available, even if expired
            if (this.cache.has(cacheKey)) {
                return this.cache.get(cacheKey).data;
            }
            throw error;
        }
    }

    /**
     * Setup memory management
     */
    setupMemoryManagement() {
        // Clean up cache periodically
        setInterval(() => {
            this.cleanupCache();
        }, 600000); // Every 10 minutes

        // Clean up on page visibility change
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.cleanupCache();
            }
        });
    }

    /**
     * Clean up cache to free memory
     */
    cleanupCache() {
        const now = Date.now();
        const maxAge = 1800000; // 30 minutes
        
        for (const [key, value] of this.cache.entries()) {
            if (now - value.timestamp > maxAge) {
                this.cache.delete(key);
            }
        }

        // Force garbage collection if available
        if (window.gc) {
            window.gc();
        }
    }

    /**
     * Check memory usage and optimize if needed
     */
    checkMemoryUsage() {
        if ('memory' in performance) {
            const memoryInfo = performance.memory;
            const usageRatio = memoryInfo.usedJSHeapSize / memoryInfo.jsHeapSizeLimit;
            
            if (usageRatio > 0.8) {
                this.optimizeMemoryUsage();
            }
        }
    }

    /**
     * Optimize memory usage
     */
    optimizeMemoryUsage() {
        // Clear cache
        this.cache.clear();
        
        // Remove unused event listeners
        this.cleanupEventListeners();
        
        // Unload non-visible lazy elements
        this.unloadNonVisibleElements();
    }

    /**
     * Optimize after page load
     */
    optimizeAfterLoad() {
        // Defer non-critical scripts
        this.deferNonCriticalScripts();
        
        // Optimize animations
        this.optimizeAnimations();
        
        // Setup idle-time optimizations
        this.setupIdleOptimizations();
    }

    /**
     * Defer non-critical scripts
     */
    deferNonCriticalScripts() {
        const nonCriticalScripts = document.querySelectorAll('script[data-defer]');
        
        nonCriticalScripts.forEach(script => {
            if (script.src) {
                const newScript = document.createElement('script');
                newScript.src = script.src;
                newScript.async = true;
                document.head.appendChild(newScript);
                script.remove();
            }
        });
    }

    /**
     * Optimize animations for performance
     */
    optimizeAnimations() {
        // Reduce animations on low-end devices
        if (this.isLowEndDevice()) {
            document.body.classList.add('reduce-animations');
        }

        // Use will-change property for animating elements
        const animatingElements = document.querySelectorAll('.animate, [data-animate]');
        animatingElements.forEach(element => {
            element.style.willChange = 'transform, opacity';
        });
    }

    /**
     * Check if device is low-end
     */
    isLowEndDevice() {
        // Check for various indicators of low-end device
        const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
        const slowConnection = connection && (connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g');
        const lowMemory = 'memory' in performance && performance.memory.jsHeapSizeLimit < 1073741824; // < 1GB
        const lowCores = navigator.hardwareConcurrency && navigator.hardwareConcurrency < 4;
        
        return slowConnection || lowMemory || lowCores;
    }

    /**
     * Setup optimizations during idle time
     */
    setupIdleOptimizations() {
        if ('requestIdleCallback' in window) {
            requestIdleCallback(() => {
                this.performIdleOptimizations();
            });
        } else {
            setTimeout(() => {
                this.performIdleOptimizations();
            }, 1000);
        }
    }

    /**
     * Perform optimizations during idle time
     */
    performIdleOptimizations() {
        // Preload next likely resources
        this.preloadLikelyResources();
        
        // Optimize DOM
        this.optimizeDOM();
        
        // Prepare analytics data
        this.prepareAnalytics();
    }

    /**
     * Preload likely next resources
     */
    preloadLikelyResources() {
        const likelyResources = [
            '/personal-space/templates',
            '/personal-space/analytics'
        ];
        
        likelyResources.forEach(resource => {
            this.prefetchResource(resource);
        });
    }

    /**
     * Optimize DOM structure
     */
    optimizeDOM() {
        // Remove empty text nodes
        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            {
                acceptNode: (node) => {
                    return node.textContent.trim() === '' ? 
                        NodeFilter.FILTER_ACCEPT : 
                        NodeFilter.FILTER_REJECT;
                }
            }
        );
        
        const emptyNodes = [];
        let node;
        while (node = walker.nextNode()) {
            emptyNodes.push(node);
        }
        
        emptyNodes.forEach(node => node.remove());
    }

    /**
     * Record performance entry
     */
    recordPerformanceEntry(entry) {
        switch (entry.entryType) {
            case 'navigation':
                this.performanceMetrics.navigationTiming = {
                    domContentLoaded: entry.domContentLoadedEventEnd - entry.domContentLoadedEventStart,
                    loadComplete: entry.loadEventEnd - entry.loadEventStart,
                    firstByte: entry.responseStart - entry.requestStart
                };
                break;
                
            case 'resource':
                this.performanceMetrics.resourceLoadTimes[entry.name] = entry.duration;
                break;
                
            case 'paint':
                this.performanceMetrics[entry.name.replace('-', '_')] = entry.startTime;
                break;
        }
    }

    /**
     * Get performance report
     */
    getPerformanceReport() {
        return {
            ...this.performanceMetrics,
            cacheSize: this.cache.size,
            lazyLoadQueue: this.lazyLoadQueue.size,
            prefetchQueue: this.prefetchQueue.size,
            timestamp: Date.now()
        };
    }

    /**
     * Optimize LCP (Largest Contentful Paint)
     */
    optimizeLCP() {
        // Preload LCP element
        const lcpElements = document.querySelectorAll('img, video, [data-lcp]');
        lcpElements.forEach(element => {
            if (element.tagName === 'IMG' && element.src) {
                const link = document.createElement('link');
                link.rel = 'preload';
                link.href = element.src;
                link.as = 'image';
                document.head.appendChild(link);
            }
        });
    }

    /**
     * Optimize FID (First Input Delay)
     */
    optimizeFID() {
        // Break up long tasks
        this.breakUpLongTasks();
        
        // Defer non-essential JavaScript
        this.deferNonEssentialJS();
    }

    /**
     * Optimize CLS (Cumulative Layout Shift)
     */
    optimizeCLS() {
        // Add size attributes to images without them
        const images = document.querySelectorAll('img:not([width]):not([height])');
        images.forEach(img => this.addImageDimensions(img));
        
        // Reserve space for dynamic content
        this.reserveSpaceForDynamicContent();
    }

    /**
     * Break up long tasks
     */
    breakUpLongTasks() {
        // Use scheduler.postTask if available
        if ('scheduler' in window && 'postTask' in scheduler) {
            // Implementation would depend on specific long tasks
        }
    }

    /**
     * Reserve space for dynamic content
     */
    reserveSpaceForDynamicContent() {
        const dynamicElements = document.querySelectorAll('[data-dynamic]');
        dynamicElements.forEach(element => {
            if (!element.style.minHeight) {
                element.style.minHeight = '100px'; // Default minimum height
            }
        });
    }

    /**
     * Clean up event listeners
     */
    cleanupEventListeners() {
        // This would need to be implemented based on specific event listeners
        // For now, just log that cleanup is happening
        console.log('Cleaning up event listeners for memory optimization');
    }

    /**
     * Unload non-visible elements
     */
    unloadNonVisibleElements() {
        const elements = document.querySelectorAll('.loaded[data-src]');
        elements.forEach(element => {
            const rect = element.getBoundingClientRect();
            const isVisible = rect.top < window.innerHeight + 1000 && rect.bottom > -1000;
            
            if (!isVisible && element.classList.contains('loaded')) {
                // Unload the element to save memory
                element.classList.remove('loaded');
                if (element.tagName === 'IMG') {
                    element.src = element.dataset.placeholder || '';
                }
            }
        });
    }

    /**
     * Prepare analytics data
     */
    prepareAnalytics() {
        // Prepare performance data for analytics
        const analyticsData = {
            performance: this.getPerformanceReport(),
            userAgent: navigator.userAgent,
            viewport: {
                width: window.innerWidth,
                height: window.innerHeight
            },
            connection: navigator.connection ? {
                effectiveType: navigator.connection.effectiveType,
                downlink: navigator.connection.downlink
            } : null
        };
        
        // Store for later sending
        localStorage.setItem('performance_analytics', JSON.stringify(analyticsData));
    }

    /**
     * Setup scroll-based lazy loading fallback
     */
    setupScrollBasedLazyLoading() {
        let ticking = false;
        
        const checkLazyElements = () => {
            this.lazyLoadQueue.forEach(element => {
                if (this.isElementInViewport(element)) {
                    this.loadLazyElement(element);
                }
            });
            ticking = false;
        };
        
        const onScroll = () => {
            if (!ticking) {
                requestAnimationFrame(checkLazyElements);
                ticking = true;
            }
        };
        
        window.addEventListener('scroll', onScroll, { passive: true });
    }

    /**
     * Check if element is in viewport
     */
    isElementInViewport(element) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    }

    /**
     * Render block content
     */
    renderBlock(element, blockData) {
        // This would integrate with the existing block rendering system
        // For now, just set basic content
        element.innerHTML = `
            <div class="block-header">
                <h3>${blockData.title}</h3>
            </div>
            <div class="block-content">
                ${blockData.content}
            </div>
        `;
    }

    /**
     * Defer non-essential JavaScript
     */
    deferNonEssentialJS() {
        // Defer analytics and other non-essential scripts
        const nonEssentialScripts = document.querySelectorAll('script[data-non-essential]');
        nonEssentialScripts.forEach(script => {
            script.defer = true;
        });
    }
}

// Global performance optimizer instance
window.PerformanceOptimizer = PerformanceOptimizer;
window.performanceOptimizer = new PerformanceOptimizer();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PerformanceOptimizer;
}