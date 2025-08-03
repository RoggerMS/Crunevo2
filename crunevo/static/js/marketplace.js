/**
 * Marketplace JavaScript
 * This file contains all the interactive functionality for the Crunevo Marketplace
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize marketplace components
    initializeFilters();
    initializeProductGallery();
    initializeQuantityControls();
    initializeProductTabs();
    initializeTooltips();
    initializeInfiniteScroll();
});

/**
 * Initialize filter functionality
 */
function initializeFilters() {
    // Price range slider
    const priceRangeSlider = document.getElementById('price-range-slider');
    if (priceRangeSlider) {
        const minPriceInput = document.getElementById('min-price');
        const maxPriceInput = document.getElementById('max-price');
        
        // Initialize noUiSlider if the library is available
        if (window.noUiSlider) {
            noUiSlider.create(priceRangeSlider, {
                start: [parseInt(minPriceInput.value) || 0, parseInt(maxPriceInput.value) || 1000],
                connect: true,
                step: 10,
                range: {
                    'min': 0,
                    'max': 1000
                },
                format: {
                    to: function(value) {
                        return Math.round(value);
                    },
                    from: function(value) {
                        return Math.round(value);
                    }
                }
            });
            
            // Update inputs when slider changes
            priceRangeSlider.noUiSlider.on('update', function(values, handle) {
                if (handle === 0) {
                    minPriceInput.value = values[0];
                } else {
                    maxPriceInput.value = values[1];
                }
            });
            
            // Update slider when inputs change
            minPriceInput.addEventListener('change', function() {
                priceRangeSlider.noUiSlider.set([this.value, null]);
            });
            
            maxPriceInput.addEventListener('change', function() {
                priceRangeSlider.noUiSlider.set([null, this.value]);
            });
        }
    }
    
    // Filter toggles
    const filterToggles = document.querySelectorAll('.filter-section-title .toggle-icon');
    filterToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const content = this.closest('.filter-section').querySelector('.filter-section-content');
            if (content) {
                content.classList.toggle('d-none');
                this.classList.toggle('collapsed');
            }
        });
    });
    
    // Filter form submission
    const filterForm = document.getElementById('marketplace-filter-form');
    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            applyFilters();
        });
        
        // Apply filters when checkboxes change
        const filterCheckboxes = filterForm.querySelectorAll('input[type="checkbox"]');
        filterCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                applyFilters();
            });
        });
        
        // Apply filters when select elements change
        const filterSelects = filterForm.querySelectorAll('select');
        filterSelects.forEach(select => {
            select.addEventListener('change', function() {
                applyFilters();
            });
        });
        
        // Clear filters button
        const clearFiltersBtn = document.getElementById('clear-filters-btn');
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', function(e) {
                e.preventDefault();
                clearFilters();
            });
        }
    }
}

/**
 * Apply filters and update product list
 */
function applyFilters() {
    const filterForm = document.getElementById('marketplace-filter-form');
    if (!filterForm) return;
    
    // Get form data
    const formData = new FormData(filterForm);
    
    // Convert to URL parameters
    const params = new URLSearchParams();
    for (const [key, value] of formData.entries()) {
        if (value) {
            params.append(key, value);
        }
    }
    
    // Get current URL and update query parameters
    const url = new URL(window.location.href);
    const baseUrl = url.origin + url.pathname;
    window.location.href = baseUrl + '?' + params.toString();
}

/**
 * Clear all filters
 */
function clearFilters() {
    const filterForm = document.getElementById('marketplace-filter-form');
    if (!filterForm) return;
    
    // Reset form
    filterForm.reset();
    
    // Reset price range slider if exists
    const priceRangeSlider = document.getElementById('price-range-slider');
    if (priceRangeSlider && priceRangeSlider.noUiSlider) {
        priceRangeSlider.noUiSlider.set([0, 1000]);
    }
    
    // Apply empty filters
    const url = new URL(window.location.href);
    window.location.href = url.origin + url.pathname;
}

/**
 * Initialize product gallery functionality
 */
function initializeProductGallery() {
    const mainImage = document.getElementById('product-main-image');
    const thumbnails = document.querySelectorAll('.product-thumbnail');
    
    if (mainImage && thumbnails.length > 0) {
        thumbnails.forEach(thumbnail => {
            thumbnail.addEventListener('click', function() {
                // Update main image
                mainImage.src = this.src;
                
                // Update active thumbnail
                thumbnails.forEach(thumb => thumb.classList.remove('active'));
                this.classList.add('active');
            });
        });
    }
}

/**
 * Initialize quantity controls
 */
function initializeQuantityControls() {
    const quantityControls = document.querySelectorAll('.product-quantity-control');
    
    quantityControls.forEach(control => {
        const minusBtn = control.querySelector('.product-quantity-btn:first-child');
        const plusBtn = control.querySelector('.product-quantity-btn:last-child');
        const input = control.querySelector('.product-quantity-input');
        
        if (minusBtn && plusBtn && input) {
            minusBtn.addEventListener('click', function() {
                const currentValue = parseInt(input.value);
                if (currentValue > 1) {
                    input.value = currentValue - 1;
                    // Trigger change event
                    input.dispatchEvent(new Event('change'));
                }
            });
            
            plusBtn.addEventListener('click', function() {
                const currentValue = parseInt(input.value);
                const maxStock = parseInt(input.dataset.maxStock || 999);
                if (currentValue < maxStock) {
                    input.value = currentValue + 1;
                    // Trigger change event
                    input.dispatchEvent(new Event('change'));
                }
            });
            
            input.addEventListener('change', function() {
                const currentValue = parseInt(this.value);
                const maxStock = parseInt(this.dataset.maxStock || 999);
                
                // Validate input
                if (isNaN(currentValue) || currentValue < 1) {
                    this.value = 1;
                } else if (currentValue > maxStock) {
                    this.value = maxStock;
                }
                
                // Update any related elements (like total price)
                updateProductTotal();
            });
        }
    });
}

/**
 * Update product total price based on quantity
 */
function updateProductTotal() {
    const quantityInput = document.querySelector('.product-quantity-input');
    const productPrice = document.querySelector('.product-price-value');
    const totalElement = document.querySelector('.product-total-price');
    
    if (quantityInput && productPrice && totalElement) {
        const quantity = parseInt(quantityInput.value);
        const price = parseFloat(productPrice.dataset.price);
        const total = quantity * price;
        
        totalElement.textContent = `S/. ${total.toFixed(2)}`;
    }
}

/**
 * Initialize product tabs
 */
function initializeProductTabs() {
    const tabLinks = document.querySelectorAll('.product-tab-link');
    const tabContents = document.querySelectorAll('.product-tab-content');
    
    if (tabLinks.length > 0 && tabContents.length > 0) {
        tabLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Get target tab
                const target = this.getAttribute('href');
                
                // Hide all tab contents
                tabContents.forEach(content => {
                    content.classList.add('d-none');
                });
                
                // Remove active class from all tabs
                tabLinks.forEach(tab => {
                    tab.classList.remove('active');
                });
                
                // Show target tab content
                document.querySelector(target).classList.remove('d-none');
                
                // Add active class to clicked tab
                this.classList.add('active');
            });
        });
    }
}

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltips.forEach(tooltip => {
            new bootstrap.Tooltip(tooltip);
        });
    }
}

/**
 * Initialize infinite scroll for product grid
 */
function initializeInfiniteScroll() {
    const productGrid = document.querySelector('.product-grid');
    const loadMoreBtn = document.getElementById('load-more-btn');
    
    if (productGrid && loadMoreBtn) {
        let page = 1;
        let loading = false;
        
        loadMoreBtn.addEventListener('click', function() {
            if (!loading) {
                loading = true;
                loadMoreBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Cargando...';
                loadMoreProducts();
            }
        });
        
        function loadMoreProducts() {
            // Get current URL and parameters
            const url = new URL(window.location.href);
            const params = url.searchParams;
            
            // Increment page
            page++;
            params.set('page', page);
            params.set('ajax', '1');
            
            // Fetch more products
            fetch(url.pathname + '?' + params.toString())
                .then(response => response.json())
                .then(data => {
                    if (data.html) {
                        // Append new products
                        const tempDiv = document.createElement('div');
                        tempDiv.innerHTML = data.html;
                        const newProducts = tempDiv.querySelectorAll('.product-card');
                        
                        newProducts.forEach(product => {
                            productGrid.appendChild(product);
                        });
                        
                        // Check if there are more products
                        if (data.has_more) {
                            loadMoreBtn.innerHTML = 'Cargar más productos';
                        } else {
                            loadMoreBtn.remove();
                        }
                    } else {
                        loadMoreBtn.remove();
                    }
                    
                    loading = false;
                })
                .catch(error => {
                    console.error('Error loading more products:', error);
                    loadMoreBtn.innerHTML = 'Cargar más productos';
                    loading = false;
                });
        }
    }
}

/**
 * Add product to cart
 * @param {number} productId - The ID of the product to add
 * @param {number} quantity - The quantity to add
 */
function addToCart(productId, quantity = 1) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    fetch('/store/cart/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            product_id: productId,
            quantity: quantity
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success message
            showNotification('Producto añadido al carrito', 'success');
            
            // Update cart count
            updateCartCount(data.cart_count);
        } else {
            showNotification(data.message || 'Error al añadir al carrito', 'error');
        }
    })
    .catch(error => {
        console.error('Error adding to cart:', error);
        showNotification('Error al añadir al carrito', 'error');
    });
}

/**
 * Add product to favorites
 * @param {number} productId - The ID of the product to add to favorites
 * @param {Element} button - The button element that was clicked
 */
function toggleFavorite(productId, button) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    fetch('/store/favorite/toggle', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            product_id: productId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update button appearance
            if (data.is_favorite) {
                button.classList.add('active');
                button.innerHTML = '<i class="bi bi-heart-fill"></i>';
                showNotification('Producto añadido a favoritos', 'success');
            } else {
                button.classList.remove('active');
                button.innerHTML = '<i class="bi bi-heart"></i>';
                showNotification('Producto eliminado de favoritos', 'success');
            }
        } else {
            showNotification(data.message || 'Error al actualizar favoritos', 'error');
        }
    })
    .catch(error => {
        console.error('Error toggling favorite:', error);
        showNotification('Error al actualizar favoritos', 'error');
    });
}

/**
 * Update cart count in the navbar
 * @param {number} count - The new cart count
 */
function updateCartCount(count) {
    const cartCountElement = document.querySelector('.cart-count');
    if (cartCountElement) {
        cartCountElement.textContent = count;
        
        if (count > 0) {
            cartCountElement.classList.remove('d-none');
        } else {
            cartCountElement.classList.add('d-none');
        }
    }
}

/**
 * Show notification
 * @param {string} message - The message to display
 * @param {string} type - The type of notification (success, error, warning, info)
 */
function showNotification(message, type = 'info') {
    // Check if Toastify is available
    if (typeof Toastify !== 'undefined') {
        Toastify({
            text: message,
            duration: 3000,
            close: true,
            gravity: 'top',
            position: 'right',
            backgroundColor: type === 'success' ? '#2ecc71' : 
                            type === 'error' ? '#e74c3c' : 
                            type === 'warning' ? '#f39c12' : '#3498db'
        }).showToast();
    } else {
        // Fallback to alert
        alert(message);
    }
}

/**
 * Open contact seller modal and set product ID
 * @param {number} productId - The ID of the product
 * @param {number} sellerId - The ID of the seller
 */
function openContactModal(productId, sellerId) {
    const modal = document.getElementById('contact-seller-modal');
    if (modal) {
        // Set product ID and seller ID in hidden inputs
        const productIdInput = modal.querySelector('input[name="product_id"]');
        const sellerIdInput = modal.querySelector('input[name="seller_id"]');
        
        if (productIdInput && sellerIdInput) {
            productIdInput.value = productId;
            sellerIdInput.value = sellerId;
        }
        
        // Show modal
        if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
            const modalInstance = new bootstrap.Modal(modal);
            modalInstance.show();
        }
    }
}

/**
 * Filter seller products by search term
 */
function filterSellerProducts() {
    const searchInput = document.getElementById('product-search');
    const productRows = document.querySelectorAll('.product-row');
    
    if (searchInput && productRows.length > 0) {
        const searchTerm = searchInput.value.toLowerCase().trim();
        
        productRows.forEach(row => {
            const productName = row.querySelector('.product-table-title').textContent.toLowerCase();
            const productCategory = row.querySelector('.product-table-category').textContent.toLowerCase();
            
            if (productName.includes(searchTerm) || productCategory.includes(searchTerm)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }
}

/**
 * Filter seller products by status
 * @param {string} status - The status to filter by (all, approved, pending, rejected)
 */
function filterProductsByStatus(status) {
    const productRows = document.querySelectorAll('.product-row');
    const statusButtons = document.querySelectorAll('.products-status-btn');
    
    if (productRows.length > 0) {
        // Update active button
        statusButtons.forEach(button => {
            if (button.dataset.status === status) {
                button.classList.add('active');
            } else {
                button.classList.remove('active');
            }
        });
        
        // Filter products
        productRows.forEach(row => {
            if (status === 'all') {
                row.style.display = '';
            } else {
                const productStatus = row.querySelector('.product-table-status').dataset.status;
                if (productStatus === status) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            }
        });
    }
}

/**
 * Confirm product deletion
 * @param {number} productId - The ID of the product to delete
 */
function confirmDeleteProduct(productId) {
    const modal = document.getElementById('delete-product-modal');
    if (modal) {
        // Set product ID in form action
        const form = modal.querySelector('form');
        if (form) {
            form.action = `/marketplace/seller/product/delete/${productId}`;
        }
        
        // Show modal
        if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
            const modalInstance = new bootstrap.Modal(modal);
            modalInstance.show();
        }
    }
}