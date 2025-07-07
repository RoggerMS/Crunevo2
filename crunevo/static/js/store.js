
/**
 * CRUNEVO Store - Advanced E-commerce Functionality
 * Handles filtering, search, infinite scroll, and user interactions
 */

class CrunevoStore {
    constructor() {
        this.products = [];
        this.filteredProducts = [];
        this.currentFilters = {
            search: '',
            category: 'all',
            availability: 'all',
            maxPrice: 500,
            sort: 'featured'
        };
        this.currentPage = 1;
        this.productsPerPage = 20;
        this.isLoading = false;
        this.hasMoreProducts = true;
        
        this.init();
    }

    init() {
        this.cacheElements();
        this.bindEvents();
        this.updateCartCount();
        this.initializeProducts();
        this.initializeMobileFilters();
        
        // Initialize infinite scroll
        this.initInfiniteScroll();
        
        console.log('CRUNEVO Store initialized successfully');
    }

    cacheElements() {
        // Search elements
        this.searchInput = document.getElementById('productSearch');
        this.priceRange = document.getElementById('priceRange');
        this.maxPriceDisplay = document.getElementById('maxPriceDisplay');
        this.sortSelect = document.getElementById('sortSelect');
        
        // Filter elements
        this.categoryItems = document.querySelectorAll('.category-item');
        this.availabilityOptions = document.querySelectorAll('.availability-option');
        
        // Product grid
        this.productsGrid = document.getElementById('productsGrid');
        this.productCards = document.querySelectorAll('.product-card');
        
        // Results elements
        this.resultsTitle = document.getElementById('resultsTitle');
        this.resultsCount = document.getElementById('resultsCount');
        this.activeFilters = document.getElementById('activeFilters');
        
        // Loading elements
        this.loadingSpinner = document.getElementById('loadingSpinner');
        this.loadMoreBtn = document.getElementById('loadMoreBtn');
        this.loadMoreSection = document.getElementById('loadMoreSection');
        
        // Cart elements
        this.cartCounts = document.querySelectorAll('#cartCount, #floatingCartCount');
        
        // Mobile elements
        this.mobileFilterToggle = document.querySelector('.mobile-filter-toggle');
        this.offcanvasFilters = document.getElementById('offcanvasFilters');
        this.offcanvasOverlay = document.getElementById('offcanvasOverlay');
    }

    bindEvents() {
        // Search functionality
        if (this.searchInput) {
            this.searchInput.addEventListener('input', 
                this.debounce(() => this.handleSearch(), 300)
            );
        }

        // Price range filter
        if (this.priceRange) {
            this.priceRange.addEventListener('input', () => this.handlePriceChange());
        }

        // Category filters
        this.categoryItems.forEach(item => {
            item.addEventListener('click', (e) => this.handleCategoryClick(e));
        });

        // Availability filters
        this.availabilityOptions.forEach(option => {
            option.addEventListener('click', (e) => this.handleAvailabilityClick(e));
        });

        // Sort functionality
        if (this.sortSelect) {
            this.sortSelect.addEventListener('change', () => this.handleSort());
        }

        // Product actions
        this.bindProductActions();

        // Load more button
        if (this.loadMoreBtn) {
            this.loadMoreBtn.addEventListener('click', () => this.loadMoreProducts());
        }

        // View toggle
        const viewToggleButtons = document.querySelectorAll('.view-toggle button');
        viewToggleButtons.forEach(btn => {
            btn.addEventListener('click', (e) => this.handleViewToggle(e));
        });
    }

    bindProductActions() {
        // Add to cart forms
        document.querySelectorAll('form[action*="add_to_cart"]').forEach(form => {
            form.addEventListener('submit', (e) => this.handleAddToCart(e));
        });

        // Favorite forms
        document.querySelectorAll('.favorite-form').forEach(form => {
            form.addEventListener('submit', (e) => this.handleToggleFavorite(e));
        });

        // Quick view links
        document.querySelectorAll('.btn-quick-view').forEach(link => {
            link.addEventListener('click', (e) => this.handleQuickView(e));
        });
    }

    initializeProducts() {
        this.products = Array.from(this.productCards).map(card => ({
            element: card,
            name: card.dataset.name || '',
            description: card.dataset.description || '',
            category: card.dataset.category || 'other',
            price: parseFloat(card.dataset.price) || 0,
            credits: parseInt(card.dataset.credits) || 0,
            stock: parseInt(card.dataset.stock) || 0,
            featured: card.dataset.featured === 'true',
            popular: card.dataset.popular === 'true',
            new: card.dataset.new === 'true'
        }));

        this.filteredProducts = [...this.products];
        this.updateResults();
    }

    initializeMobileFilters() {
        // Clone filters content to mobile offcanvas
        const filtersContainer = document.querySelector('.filters-container');
        const offcanvasBody = document.querySelector('.offcanvas-body');
        
        if (filtersContainer && offcanvasBody) {
            const filtersClone = filtersContainer.cloneNode(true);
            offcanvasBody.innerHTML = '';
            offcanvasBody.appendChild(filtersClone);
            
            // Re-bind events for mobile filters
            this.bindMobileFilterEvents();
        }
    }

    bindMobileFilterEvents() {
        const offcanvasBody = document.querySelector('.offcanvas-body');
        if (!offcanvasBody) return;

        // Search input
        const mobileSearch = offcanvasBody.querySelector('#productSearch');
        if (mobileSearch) {
            mobileSearch.addEventListener('input', 
                this.debounce(() => {
                    this.currentFilters.search = mobileSearch.value.toLowerCase();
                    this.applyFilters();
                }, 300)
            );
        }

        // Category items
        offcanvasBody.querySelectorAll('.category-item').forEach(item => {
            item.addEventListener('click', (e) => this.handleCategoryClick(e, true));
        });

        // Availability options
        offcanvasBody.querySelectorAll('.availability-option').forEach(option => {
            option.addEventListener('click', (e) => this.handleAvailabilityClick(e, true));
        });
    }

    initInfiniteScroll() {
        const options = {
            root: null,
            rootMargin: '100px',
            threshold: 0.1
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && this.hasMoreProducts && !this.isLoading) {
                    this.loadMoreProducts();
                }
            });
        }, options);

        // Observe the load more section
        if (this.loadMoreSection) {
            observer.observe(this.loadMoreSection);
        }
    }

    // Event Handlers
    handleSearch() {
        this.currentFilters.search = this.searchInput.value.toLowerCase();
        this.applyFilters();
        this.updateActiveFilters();
    }

    handlePriceChange() {
        this.currentFilters.maxPrice = parseInt(this.priceRange.value);
        this.maxPriceDisplay.textContent = `S/ ${this.currentFilters.maxPrice}`;
        this.applyFilters();
        this.updateActiveFilters();
    }

    handleCategoryClick(e, isMobile = false) {
        e.preventDefault();
        const category = e.currentTarget.dataset.category;
        
        this.currentFilters.category = category;
        
        // Update active state
        const container = isMobile ? 
            document.querySelector('.offcanvas-body') : 
            document.querySelector('.store-sidebar');
            
        container.querySelectorAll('.category-item').forEach(item => {
            item.classList.remove('active');
        });
        e.currentTarget.classList.add('active');
        
        // Sync with main filters if this is mobile
        if (isMobile) {
            this.syncMainFilters();
        }
        
        this.applyFilters();
        this.updateActiveFilters();
        this.updateResultsTitle();
    }

    handleAvailabilityClick(e, isMobile = false) {
        e.preventDefault();
        const availability = e.currentTarget.dataset.availability;
        
        this.currentFilters.availability = availability;
        
        // Update active state
        const container = isMobile ? 
            document.querySelector('.offcanvas-body') : 
            document.querySelector('.store-sidebar');
            
        container.querySelectorAll('.availability-option').forEach(option => {
            option.classList.remove('active');
        });
        e.currentTarget.classList.add('active');
        
        // Sync with main filters if this is mobile
        if (isMobile) {
            this.syncMainFilters();
        }
        
        this.applyFilters();
        this.updateActiveFilters();
    }

    handleSort() {
        this.currentFilters.sort = this.sortSelect.value;
        this.applyFilters();
    }

    handleViewToggle(e) {
        e.preventDefault();
        const viewType = e.currentTarget.dataset.view;
        
        // Update toggle state
        document.querySelectorAll('.view-toggle button').forEach(btn => {
            btn.classList.remove('active');
        });
        e.currentTarget.classList.add('active');
        
        // Apply view changes
        if (viewType === 'list') {
            this.productsGrid.classList.add('list-view');
        } else {
            this.productsGrid.classList.remove('list-view');
        }
    }

    async handleAddToCart(e) {
        e.preventDefault();
        
        const form = e.target;
        const formData = new FormData(form);
        
        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.updateCartCount();
                this.showToast('cartToast');
                
                // Add visual feedback
                const button = form.querySelector('button');
                this.addButtonFeedback(button, 'success');
            }
        } catch (error) {
            console.error('Error adding to cart:', error);
            this.showToast('errorToast', 'Error al agregar al carrito');
        }
    }

    async handleToggleFavorite(e) {
        e.preventDefault();
        
        const form = e.target;
        const button = form.querySelector('.favorite-btn');
        const icon = button.querySelector('i');
        
        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: new FormData(form)
            });
            
            if (response.ok) {
                button.classList.toggle('active');
                icon.className = button.classList.contains('active') ? 
                    'bi bi-heart-fill' : 'bi bi-heart';
                
                const toastBody = document.getElementById('favoriteToastBody');
                toastBody.textContent = button.classList.contains('active') ? 
                    'Producto agregado a favoritos' : 
                    'Producto eliminado de favoritos';
                
                this.showToast('favoriteToast');
            }
        } catch (error) {
            console.error('Error toggling favorite:', error);
        }
    }

    handleQuickView(e) {
        // Add loading state to quick view button
        const button = e.target.closest('.btn-quick-view');
        this.addButtonFeedback(button, 'loading');
    }

    // Filter Logic
    applyFilters() {
        this.showLoading();
        
        // Simulate API delay for better UX
        setTimeout(() => {
            this.filteredProducts = this.products.filter(product => {
                return this.matchesSearch(product) &&
                       this.matchesCategory(product) &&
                       this.matchesAvailability(product) &&
                       this.matchesPrice(product);
            });
            
            this.sortProducts();
            this.updateResults();
            this.hideLoading();
        }, 150);
    }

    matchesSearch(product) {
        if (!this.currentFilters.search) return true;
        
        const searchTerm = this.currentFilters.search.toLowerCase();
        return product.name.includes(searchTerm) || 
               product.description.includes(searchTerm);
    }

    matchesCategory(product) {
        if (this.currentFilters.category === 'all') return true;
        return product.category === this.currentFilters.category;
    }

    matchesAvailability(product) {
        switch (this.currentFilters.availability) {
            case 'all':
                return true;
            case 'in-stock':
                return product.stock > 5;
            case 'low-stock':
                return product.stock > 0 && product.stock <= 5;
            case 'free':
                return product.price === 0 && product.credits === 0;
            default:
                return true;
        }
    }

    matchesPrice(product) {
        return product.price <= this.currentFilters.maxPrice;
    }

    sortProducts() {
        this.filteredProducts.sort((a, b) => {
            switch (this.currentFilters.sort) {
                case 'price-low':
                    return a.price - b.price;
                case 'price-high':
                    return b.price - a.price;
                case 'newest':
                    return b.new - a.new;
                case 'popular':
                    return b.popular - a.popular;
                case 'name':
                    return a.name.localeCompare(b.name);
                case 'featured':
                default:
                    return b.featured - a.featured;
            }
        });
    }

    updateResults() {
        // Hide all products
        this.products.forEach(product => {
            product.element.style.display = 'none';
        });
        
        // Show filtered products
        this.filteredProducts.forEach((product, index) => {
            if (index < this.currentPage * this.productsPerPage) {
                product.element.style.display = 'block';
                product.element.style.animation = `fadeInUp 0.3s ease-out ${index * 0.05}s both`;
            }
        });
        
        // Update results count
        this.updateResultsCount();
        
        // Update load more visibility
        this.updateLoadMoreVisibility();
        
        // Show empty state if no results
        this.updateEmptyState();
    }

    updateResultsCount() {
        if (this.resultsCount) {
            const count = this.filteredProducts.length;
            this.resultsCount.textContent = `${count} producto${count !== 1 ? 's' : ''} encontrado${count !== 1 ? 's' : ''}`;
        }
    }

    updateResultsTitle() {
        if (!this.resultsTitle) return;
        
        let title = 'Todos los productos';
        
        if (this.currentFilters.category !== 'all') {
            const categoryItem = document.querySelector(`[data-category="${this.currentFilters.category}"]`);
            if (categoryItem) {
                title = categoryItem.querySelector('span').textContent;
            }
        }
        
        if (this.currentFilters.search) {
            title = `Resultados para "${this.currentFilters.search}"`;
        }
        
        this.resultsTitle.textContent = title;
    }

    updateActiveFilters() {
        if (!this.activeFilters) return;
        
        const filters = [];
        
        if (this.currentFilters.search) {
            filters.push({
                type: 'search',
                label: `Búsqueda: "${this.currentFilters.search}"`,
                value: this.currentFilters.search
            });
        }
        
        if (this.currentFilters.category !== 'all') {
            filters.push({
                type: 'category',
                label: `Categoría: ${this.currentFilters.category}`,
                value: this.currentFilters.category
            });
        }
        
        if (this.currentFilters.availability !== 'all') {
            filters.push({
                type: 'availability',
                label: `Disponibilidad: ${this.getAvailabilityLabel(this.currentFilters.availability)}`,
                value: this.currentFilters.availability
            });
        }
        
        if (this.currentFilters.maxPrice < 500) {
            filters.push({
                type: 'price',
                label: `Precio máx: S/ ${this.currentFilters.maxPrice}`,
                value: this.currentFilters.maxPrice
            });
        }
        
        this.activeFilters.innerHTML = filters.map(filter => `
            <span class="filter-tag">
                ${filter.label}
                <button type="button" onclick="store.removeFilter('${filter.type}', '${filter.value}')">
                    <i class="bi bi-x"></i>
                </button>
            </span>
        `).join('');
    }

    updateLoadMoreVisibility() {
        const visibleCount = Math.min(
            this.currentPage * this.productsPerPage,
            this.filteredProducts.length
        );
        
        this.hasMoreProducts = visibleCount < this.filteredProducts.length;
        
        if (this.loadMoreSection) {
            this.loadMoreSection.style.display = this.hasMoreProducts ? 'block' : 'none';
        }
    }

    updateEmptyState() {
        const emptyState = document.querySelector('.empty-state');
        if (!emptyState) return;
        
        emptyState.style.display = this.filteredProducts.length === 0 ? 'block' : 'none';
    }

    // Utility Methods
    async loadMoreProducts() {
        if (this.isLoading || !this.hasMoreProducts) return;
        
        this.isLoading = true;
        this.showLoadingButton();
        
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 500));
        
        this.currentPage++;
        this.updateResults();
        
        this.isLoading = false;
        this.hideLoadingButton();
    }

    showLoading() {
        if (this.loadingSpinner) {
            this.loadingSpinner.style.display = 'flex';
        }
    }

    hideLoading() {
        if (this.loadingSpinner) {
            this.loadingSpinner.style.display = 'none';
        }
    }

    showLoadingButton() {
        if (this.loadMoreBtn) {
            this.loadMoreBtn.disabled = true;
            this.loadMoreBtn.innerHTML = `
                <div class="spinner-border spinner-border-sm me-2" role="status"></div>
                Cargando...
            `;
        }
    }

    hideLoadingButton() {
        if (this.loadMoreBtn) {
            this.loadMoreBtn.disabled = false;
            this.loadMoreBtn.innerHTML = `
                <i class="bi bi-arrow-down-circle"></i>
                Cargar más productos
            `;
        }
    }

    async updateCartCount() {
        try {
            const response = await fetch('/store/api/cart_count');
            const data = await response.json();
            
            this.cartCounts.forEach(el => {
                el.textContent = data.count > 0 ? `${data.count} productos` : '0 productos';
            });
            
            // Update floating cart badge
            const floatingBadge = document.getElementById('floatingCartCount');
            if (floatingBadge) {
                floatingBadge.textContent = data.count;
                floatingBadge.style.display = data.count > 0 ? 'block' : 'none';
            }
        } catch (error) {
            console.error('Error updating cart count:', error);
        }
    }

    removeFilter(type, value) {
        switch (type) {
            case 'search':
                this.currentFilters.search = '';
                if (this.searchInput) this.searchInput.value = '';
                break;
            case 'category':
                this.currentFilters.category = 'all';
                this.updateCategoryActiveState('all');
                break;
            case 'availability':
                this.currentFilters.availability = 'all';
                this.updateAvailabilityActiveState('all');
                break;
            case 'price':
                this.currentFilters.maxPrice = 500;
                if (this.priceRange) this.priceRange.value = 500;
                if (this.maxPriceDisplay) this.maxPriceDisplay.textContent = 'S/ 500';
                break;
        }
        
        this.applyFilters();
        this.updateActiveFilters();
        this.updateResultsTitle();
    }

    clearAllFilters() {
        this.currentFilters = {
            search: '',
            category: 'all',
            availability: 'all',
            maxPrice: 500,
            sort: 'featured'
        };
        
        // Reset UI
        if (this.searchInput) this.searchInput.value = '';
        if (this.priceRange) this.priceRange.value = 500;
        if (this.maxPriceDisplay) this.maxPriceDisplay.textContent = 'S/ 500';
        if (this.sortSelect) this.sortSelect.value = 'featured';
        
        this.updateCategoryActiveState('all');
        this.updateAvailabilityActiveState('all');
        
        this.applyFilters();
        this.updateActiveFilters();
        this.updateResultsTitle();
    }

    updateCategoryActiveState(category) {
        document.querySelectorAll('.category-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.category === category) {
                item.classList.add('active');
            }
        });
    }

    updateAvailabilityActiveState(availability) {
        document.querySelectorAll('.availability-option').forEach(option => {
            option.classList.remove('active');
            if (option.dataset.availability === availability) {
                option.classList.add('active');
            }
        });
    }

    syncMainFilters() {
        // Sync mobile filters with main sidebar
        this.updateCategoryActiveState(this.currentFilters.category);
        this.updateAvailabilityActiveState(this.currentFilters.availability);
    }

    getAvailabilityLabel(availability) {
        const labels = {
            'all': 'Todos',
            'in-stock': 'En stock',
            'low-stock': 'Pocas unidades',
            'free': 'Gratis'
        };
        return labels[availability] || availability;
    }

    addButtonFeedback(button, type) {
        if (!button) return;
        
        const originalHTML = button.innerHTML;
        
        switch (type) {
            case 'success':
                button.innerHTML = '<i class="bi bi-check"></i> ¡Agregado!';
                button.classList.add('btn-success');
                setTimeout(() => {
                    button.innerHTML = originalHTML;
                    button.classList.remove('btn-success');
                }, 2000);
                break;
            case 'loading':
                button.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"></div>';
                break;
        }
    }

    showToast(toastId, message = null) {
        const toast = document.getElementById(toastId);
        if (!toast) return;
        
        if (message) {
            const toastBody = toast.querySelector('.toast-body');
            if (toastBody) toastBody.textContent = message;
        }
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
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
}

// Mobile Filter Functions
function toggleMobileFilters() {
    const offcanvasFilters = document.getElementById('offcanvasFilters');
    const offcanvasOverlay = document.getElementById('offcanvasOverlay');
    
    offcanvasFilters.classList.add('show');
    offcanvasOverlay.classList.add('show');
}

function closeMobileFilters() {
    const offcanvasFilters = document.getElementById('offcanvasFilters');
    const offcanvasOverlay = document.getElementById('offcanvasOverlay');
    
    offcanvasFilters.classList.remove('show');
    offcanvasOverlay.classList.remove('show');
}

// Product Request Modal
function openProductRequestModal() {
    const modal = new bootstrap.Modal(document.getElementById('productRequestModal'));
    modal.show();
}

// Global functions
function clearAllFilters() {
    if (window.store) {
        window.store.clearAllFilters();
    }
}

// Initialize store when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.store = new CrunevoStore();
    
    // Product request form handler
    const requestForm = document.getElementById('productRequestForm');
    if (requestForm) {
        requestForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalHTML = submitBtn.innerHTML;
            
            submitBtn.innerHTML = '<div class="spinner-border spinner-border-sm me-2" role="status"></div>Enviando...';
            submitBtn.disabled = true;
            
            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 1500));
            
            // Show success toast
            window.store.showToast('requestToast');
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('productRequestModal'));
            modal.hide();
            
            // Reset form
            this.reset();
            
            // Reset button
            submitBtn.innerHTML = originalHTML;
            submitBtn.disabled = false;
        });
    }
});
