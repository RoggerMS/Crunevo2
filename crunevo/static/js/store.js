/**
 * CRUNEVO Store - Advanced E-commerce Functionality
 * Handles filtering, search, infinite scroll, and user interactions
 */

class CrunevoStore {
    constructor() {
        this.currentPage = 1;
        this.isLoading = false;
        this.hasMore = true;
        this.searchTimeout = null;
        this.activeFilters = {
            category: 'all',
            maxPrice: 500,
            availability: 'all',
            search: '',
            sort: 'featured'
        };

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupInfiniteScroll();
        this.updateCartCount();
        this.cloneSidebarForMobile();
        this.initializeFilters();

        // Initialize view toggle
        this.initViewToggle();

        console.log('🛍️ CRUNEVO Store initialized successfully!');
    }

    setupEventListeners() {
        // Search functionality
        const searchInput = document.getElementById('productSearch');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.handleSearch(e.target.value);
            });
        }

        // Price range slider
        const priceRange = document.getElementById('priceRange');
        if (priceRange) {
            priceRange.addEventListener('input', (e) => {
                this.handlePriceChange(e.target.value);
            });
        }

        // Category filters
        document.querySelectorAll('.category-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleCategoryChange(item.dataset.category);
            });
        });

        // Availability filters
        document.querySelectorAll('.availability-option').forEach(option => {
            option.addEventListener('click', () => {
                this.handleAvailabilityChange(option.dataset.availability);
            });
        });

        // Sort functionality
        const sortSelect = document.getElementById('sortSelect');
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                this.handleSortChange(e.target.value);
            });
        }

        // Add to cart buttons
        document.addEventListener('click', (e) => {
            if (e.target.closest('.btn-secondary-action')) {
                this.handleAddToCart(e);
            }
        });

        // Favorite buttons
        document.addEventListener('submit', (e) => {
            if (e.target.classList.contains('favorite-form')) {
                this.handleFavoriteToggle(e);
            }
        });

        // Mobile filter toggle
        const mobileToggle = document.querySelector('.mobile-filter-toggle');
        if (mobileToggle) {
            mobileToggle.addEventListener('click', () => {
                this.toggleMobileFilters();
            });
        }

        const sidebarToggle = document.getElementById('toggleSidebarBtn');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => {
                this.toggleSidebar();
            });
        }
    }

    setupInfiniteScroll() {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting && !this.isLoading && this.hasMore) {
                        this.loadMoreProducts();
                    }
                });
            },
            {
                rootMargin: '100px'
            }
        );

        const loadMoreSection = document.getElementById('loadMoreSection');
        if (loadMoreSection) {
            observer.observe(loadMoreSection);
        }
    }

    initializeFilters() {
        // Initialize price range display
        const priceRange = document.getElementById('priceRange');
        const maxPriceDisplay = document.getElementById('maxPriceDisplay');

        if (priceRange && maxPriceDisplay) {
            maxPriceDisplay.textContent = `S/ ${priceRange.value}`;
            this.activeFilters.maxPrice = parseInt(priceRange.value);
        }

        // Set initial active states
        document.querySelector('.category-item[data-category="all"]')?.classList.add('active');
        document.querySelector('.availability-option[data-availability="all"]')?.classList.add('active');
    }

    initViewToggle() {
        const viewToggleButtons = document.querySelectorAll('.view-toggle button');
        const productsGrid = document.getElementById('productsGrid');

        viewToggleButtons.forEach(button => {
            button.addEventListener('click', () => {
                const viewType = button.dataset.view;

                // Update button states
                viewToggleButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');

                // Update grid view
                if (productsGrid) {
                    productsGrid.classList.remove('list-view');
                    if (viewType === 'list') {
                        productsGrid.classList.add('list-view');
                    }
                }
            });
        });
    }

    handleSearch(query) {
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
            this.activeFilters.search = query.trim();
            this.refreshProducts();
        }, 300);
    }

    handlePriceChange(value) {
        const maxPriceDisplay = document.getElementById('maxPriceDisplay');
        if (maxPriceDisplay) {
            maxPriceDisplay.textContent = `S/ ${value}`;
        }

        this.activeFilters.maxPrice = parseInt(value);
        this.refreshProducts();
    }

    handleCategoryChange(category) {
        // Update active state
        document.querySelectorAll('.category-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-category="${category}"]`).classList.add('active');

        this.activeFilters.category = category;
        this.refreshProducts();
    }

    handleAvailabilityChange(availability) {
        // Update active state
        document.querySelectorAll('.availability-option').forEach(option => {
            option.classList.remove('active');
        });
        document.querySelector(`[data-availability="${availability}"]`).classList.add('active');

        this.activeFilters.availability = availability;
        this.refreshProducts();
    }

    handleSortChange(sortValue) {
        this.activeFilters.sort = sortValue;
        this.refreshProducts();
    }

    async handleAddToCart(e) {
        e.preventDefault();

        const form = e.target.closest('form');
        if (!form) return;

        const button = e.target.closest('.btn-secondary-action');
        const originalText = button.innerHTML;

        // Show loading state
        button.innerHTML = '<div class="spinner-border spinner-border-sm me-2" role="status"></div>Agregando...';
        button.disabled = true;

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            const data = await response.json();

            if (data.count !== undefined) {
                this.updateCartCount(data.count);
                this.showToast('cartToast');

                // Add success animation
                button.classList.add('btn-success');
                button.innerHTML = '<i class="bi bi-check"></i> ¡Agregado!';

                setTimeout(() => {
                    button.classList.remove('btn-success');
                    button.innerHTML = originalText;
                    button.disabled = false;
                }, 2000);
            } else {
                throw new Error('Error adding to cart');
            }
        } catch (error) {
            console.error('Error adding to cart:', error);
            this.showToast('errorToast', 'Error al agregar al carrito');

            button.innerHTML = originalText;
            button.disabled = false;
        }
    }

    async handleFavoriteToggle(e) {
        e.preventDefault();

        const form = e.target;
        const button = form.querySelector('.favorite-btn');

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (response.ok) {
                // Toggle button state
                button.classList.toggle('active');
                const icon = button.querySelector('i');

                if (button.classList.contains('active')) {
                    icon.classList.remove('bi-heart');
                    icon.classList.add('bi-heart-fill');
                    this.showToast('favoriteToast', 'Producto agregado a favoritos');
                } else {
                    icon.classList.remove('bi-heart-fill');
                    icon.classList.add('bi-heart');
                    this.showToast('favoriteToast', 'Producto eliminado de favoritos');
                }

                // Add animation
                button.style.transform = 'scale(1.2)';
                setTimeout(() => {
                    button.style.transform = 'scale(1)';
                }, 200);
            }
        } catch (error) {
            console.error('Error toggling favorite:', error);
        }
    }

    async refreshProducts() {
        this.currentPage = 1;
        this.hasMore = true;

        const productsGrid = document.getElementById('productsGrid');
        const loadingSpinner = document.getElementById('loadingSpinner');

        if (loadingSpinner) {
            loadingSpinner.style.display = 'block';
        }

        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                q: this.activeFilters.search,
                categoria: this.activeFilters.category !== 'all' ? this.activeFilters.category : '',
                precio_max: this.activeFilters.maxPrice,
                stock: this.activeFilters.availability === 'in-stock' ? 1 : '',
                free: this.activeFilters.availability === 'free' ? 1 : '',
                sort: this.activeFilters.sort
            });

            const response = await fetch(`/store/api/search?${params}`);
            const data = await response.json();

            if (productsGrid) {
                productsGrid.innerHTML = data.html;

                // Add fade-in animation
                const cards = productsGrid.querySelectorAll('.product-card');
                cards.forEach((card, index) => {
                    card.style.opacity = '0';
                    card.style.transform = 'translateY(20px)';
                    setTimeout(() => {
                        card.style.transition = 'all 0.5s ease';
                        card.style.opacity = '1';
                        card.style.transform = 'translateY(0)';
                    }, index * 100);
                });
            }

            this.hasMore = data.has_next;
            this.updateResultsCount();
            this.updateActiveFilters();

        } catch (error) {
            console.error('Error refreshing products:', error);
        } finally {
            if (loadingSpinner) {
                loadingSpinner.style.display = 'none';
            }
        }
    }

    async loadMoreProducts() {
        if (this.isLoading || !this.hasMore) return;

        this.isLoading = true;
        this.currentPage++;

        const loadingSpinner = document.getElementById('loadingSpinner');
        if (loadingSpinner) {
            loadingSpinner.style.display = 'block';
        }

        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                q: this.activeFilters.search,
                categoria: this.activeFilters.category !== 'all' ? this.activeFilters.category : '',
                precio_max: this.activeFilters.maxPrice,
                stock: this.activeFilters.availability === 'in-stock' ? 1 : '',
                free: this.activeFilters.availability === 'free' ? 1 : '',
                sort: this.activeFilters.sort
            });

            const response = await fetch(`/store/api/search?${params}`);
            const data = await response.json();

            const productsGrid = document.getElementById('productsGrid');
            if (productsGrid && data.html) {
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = data.html;

                const newCards = tempDiv.querySelectorAll('.product-card');
                newCards.forEach((card, index) => {
                    card.style.opacity = '0';
                    card.style.transform = 'translateY(20px)';
                    productsGrid.appendChild(card);

                    setTimeout(() => {
                        card.style.transition = 'all 0.5s ease';
                        card.style.opacity = '1';
                        card.style.transform = 'translateY(0)';
                    }, index * 100);
                });
            }

            this.hasMore = data.has_next;

        } catch (error) {
            console.error('Error loading more products:', error);
        } finally {
            this.isLoading = false;
            if (loadingSpinner) {
                loadingSpinner.style.display = 'none';
            }
        }
    }

    updateResultsCount() {
        const resultsCount = document.getElementById('resultsCount');
        const productsGrid = document.getElementById('productsGrid');

        if (resultsCount && productsGrid) {
            const count = productsGrid.querySelectorAll('.product-card').length;
            resultsCount.textContent = `${count} productos encontrados`;
        }

        const resultsTitle = document.getElementById('resultsTitle');
        if (resultsTitle) {
            let title = 'Todos los productos';
            if (this.activeFilters.search) {
                title = `Resultados para "${this.activeFilters.search}"`;
            } else if (this.activeFilters.category !== 'all') {
                title = `Categoría: ${this.activeFilters.category}`;
            }
            resultsTitle.textContent = title;
        }
    }

    updateActiveFilters() {
        const activeFiltersContainer = document.getElementById('activeFilters');
        if (!activeFiltersContainer) return;

        activeFiltersContainer.innerHTML = '';

        // Add filter tags
        if (this.activeFilters.search) {
            this.addFilterTag(activeFiltersContainer, 'Búsqueda', this.activeFilters.search, 'search');
        }

        if (this.activeFilters.category !== 'all') {
            this.addFilterTag(activeFiltersContainer, 'Categoría', this.activeFilters.category, 'category');
        }

        if (this.activeFilters.maxPrice < 500) {
            this.addFilterTag(activeFiltersContainer, 'Precio máximo', `S/ ${this.activeFilters.maxPrice}`, 'price');
        }

        if (this.activeFilters.availability !== 'all') {
            const availabilityText = this.activeFilters.availability === 'in-stock' ? 'En stock' : 
                                    this.activeFilters.availability === 'free' ? 'Gratis' : this.activeFilters.availability;
            this.addFilterTag(activeFiltersContainer, 'Disponibilidad', availabilityText, 'availability');
        }
    }

    addFilterTag(container, label, value, type) {
        const tag = document.createElement('div');
        tag.className = 'filter-tag';
        tag.innerHTML = `
            <span>${label}: ${value}</span>
            <button type="button" onclick="window.store.removeFilter('${type}')">&times;</button>
        `;
        container.appendChild(tag);
    }

    removeFilter(type) {
        switch (type) {
            case 'search':
                this.activeFilters.search = '';
                const searchInput = document.getElementById('productSearch');
                if (searchInput) searchInput.value = '';
                break;
            case 'category':
                this.activeFilters.category = 'all';
                this.handleCategoryChange('all');
                return; // handleCategoryChange will call refreshProducts
            case 'price':
                this.activeFilters.maxPrice = 500;
                const priceRange = document.getElementById('priceRange');
                if (priceRange) priceRange.value = 500;
                this.handlePriceChange(500);
                return; // handlePriceChange will call refreshProducts
            case 'availability':
                this.activeFilters.availability = 'all';
                this.handleAvailabilityChange('all');
                return; // handleAvailabilityChange will call refreshProducts
        }

        this.refreshProducts();
    }

    clearAllFilters() {
        // Reset all filters
        this.activeFilters = {
            category: 'all',
            maxPrice: 500,
            availability: 'all',
            search: '',
            sort: 'featured'
        };

        // Reset UI elements
        const searchInput = document.getElementById('productSearch');
        if (searchInput) searchInput.value = '';

        const priceRange = document.getElementById('priceRange');
        if (priceRange) {
            priceRange.value = 500;
            this.handlePriceChange(500);
        }

        const sortSelect = document.getElementById('sortSelect');
        if (sortSelect) sortSelect.value = 'featured';

        // Reset active states
        document.querySelectorAll('.category-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector('[data-category="all"]')?.classList.add('active');

        document.querySelectorAll('.availability-option').forEach(option => {
            option.classList.remove('active');
        });
        document.querySelector('[data-availability="all"]')?.classList.add('active');

        this.refreshProducts();
    }

    async updateCartCount(count = null) {
        try {
            if (count === null) {
                const response = await fetch('/store/api/cart_count');
                const data = await response.json();
                count = data.count;
            }

            const cartCount = document.getElementById('cartCount');
            const floatingCartCount = document.getElementById('floatingCartCount');

            if (cartCount) {
                cartCount.textContent = count === 1 ? '1 producto' : `${count} productos`;
            }

            if (floatingCartCount) {
                floatingCartCount.textContent = count;
                floatingCartCount.style.display = count > 0 ? 'block' : 'none';
            }
        } catch (error) {
            console.error('Error updating cart count:', error);
        }
    }

    toggleMobileFilters() {
        const overlay = document.getElementById('offcanvasOverlay');
        const filters = document.getElementById('offcanvasFilters');

        if (overlay && filters) {
            overlay.classList.add('active');
            filters.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    }

    toggleSidebar() {
        const sidebar = document.querySelector('.store-sidebar');
        const layout = document.querySelector('.store-layout');
        const btn = document.getElementById('toggleSidebarBtn');

        if (sidebar && layout && btn) {
            sidebar.classList.toggle('collapsed');
            layout.classList.toggle('sidebar-collapsed');

            if (sidebar.classList.contains('collapsed')) {
                btn.innerHTML = '<i class="bi bi-sliders"></i>';
            } else {
                btn.innerHTML = '<i class="bi bi-sliders"></i> Filtros';
            }
        }
    }

    closeMobileFilters() {
        const overlay = document.getElementById('offcanvasOverlay');
        const filters = document.getElementById('offcanvasFilters');

        if (overlay && filters) {
            overlay.classList.remove('active');
            filters.classList.remove('active');
            document.body.style.overflow = 'auto';
        }
    }

    cloneSidebarForMobile() {
        const sidebar = document.querySelector('.filters-container');
        const offcanvasBody = document.querySelector('.offcanvas-body');

        if (sidebar && offcanvasBody) {
            offcanvasBody.innerHTML = sidebar.innerHTML;
        }
    }

    showToast(toastId, message = null) {
        const toast = document.getElementById(toastId);
        if (toast) {
            if (message) {
                const toastBody = toast.querySelector('.toast-body');
                if (toastBody) {
                    toastBody.textContent = message;
                }
            }

            const bsToast = new bootstrap.Toast(toast);
            bsToast.show();
        }
    }

    getCSRFToken() {
        const token = document.querySelector('meta[name="csrf-token"]');
        return token ? token.getAttribute('content') : '';
    }
}

// Global functions for template access
function toggleMobileFilters() {
    if (window.store) {
        window.store.toggleMobileFilters();
    }
}

function closeMobileFilters() {
    if (window.store) {
        window.store.closeMobileFilters();
    }
}

function toggleSidebar() {
    if (window.store) {
        window.store.toggleSidebar();
    }
}

function clearAllFilters() {
    if (window.store) {
        window.store.clearAllFilters();
    }
}


function openPublishProductModal() {
    const modal = new bootstrap.Modal(
        document.getElementById('publishProductModal')
    );
    modal.show();
}

// Expose functions for inline event handlers
window.clearAllFilters = clearAllFilters;
window.openPublishProductModal = openPublishProductModal;
window.toggleSidebar = toggleSidebar;

// Initialize store when DOM is loaded
function initCrunevoStore() {
    window.store = new CrunevoStore();

    // Publish product form handler
    const publishForm = document.getElementById('publishProductForm');
    if (publishForm) {
        publishForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const submitBtn = this.querySelector('button[type="submit"]');
            const originalHTML = submitBtn.innerHTML;

            submitBtn.innerHTML = '<div class="spinner-border spinner-border-sm me-2" role="status"></div>Publicando...';
            submitBtn.disabled = true;

            try {
                const formData = new FormData(this);
                const response = await fetch('/store/publicar-producto', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': window.store.getCSRFToken()
                    }
                });

                if (response.ok) {
                    window.store.showToast('publishToast');
                    const modal = bootstrap.Modal.getInstance(document.getElementById('publishProductModal'));
                    modal.hide();
                    this.reset();
                } else {
                    throw new Error('Error submitting product');
                }
            } catch (error) {
                console.error('Error publishing product:', error);
                window.store.showToast('errorToast', 'Error al publicar el producto');
            } finally {
                submitBtn.innerHTML = originalHTML;
                submitBtn.disabled = false;
            }
        });
    }

    // Close mobile filters when clicking overlay
    const overlay = document.getElementById('offcanvasOverlay');
    if (overlay) {
        overlay.addEventListener('click', closeMobileFilters);
    }

    // Close mobile filters button
    const closeBtn = document.querySelector('.offcanvas-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeMobileFilters);
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCrunevoStore);
} else {
    initCrunevoStore();
}
