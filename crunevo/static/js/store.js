// Extracted store script
function updateCartCount() {
    fetch('/store/api/cart_count')
        .then(response => response.json())
        .then(data => {
            const counts = document.querySelectorAll('#cartCount, #mobileCartCount');
            counts.forEach(el => (el.textContent = data.count));
        });
}

function addToCart(form) {
    const formData = new FormData(form);

    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        },
    })
        .then(response => response.json())
        .then(() => {
            updateCartCount();
            showToast('cartToast');
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

function toggleFavorite(form) {
    const button = form.querySelector('.favorite-btn');
    const icon = button.querySelector('i');

    fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
    }).then(response => {
        if (response.ok) {
            button.classList.toggle('active');
            icon.className = button.classList.contains('active')
                ? 'bi bi-heart-fill'
                : 'bi bi-heart';
        }
    });
}


function sortProducts(sortBy) {
    const grid = document.getElementById('productsGrid');
    const products = Array.from(grid.querySelectorAll('.product-card'));

    products.sort((a, b) => {
        switch (sortBy) {
            case 'price-low':
                return parseFloat(a.dataset.price) - parseFloat(b.dataset.price);
            case 'price-high':
                return parseFloat(b.dataset.price) - parseFloat(a.dataset.price);
            case 'newest':
                return b.querySelector('.badge-new') ? 1 : -1;
            case 'popular':
                return b.querySelector('.badge-popular') ? 1 : -1;
            default:
                return 0;
        }
    });

    products.forEach(product => grid.appendChild(product));
}

function showToast(toastId) {
    const toast = new bootstrap.Toast(document.getElementById(toastId));
    toast.show();
}


function attachFormListeners(root = document) {
    root.querySelectorAll('.action-form').forEach(form => {
        form.addEventListener('submit', function (e) {
            if (this.action.includes('add_to_cart')) {
                e.preventDefault();
                addToCart(this);
            }
        });
    });

    root.querySelectorAll('.favorite-form').forEach(form => {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            toggleFavorite(this);
        });
    });
}

let searchPage = 1;
let isLoading = false;
let currentQuery = '';
let observer;
const productsGrid = document.getElementById('productsGrid');
const productEnd = document.getElementById('productEnd');
const initialHTML = productsGrid ? productsGrid.innerHTML : '';

function loadResults(reset = false) {
    if (isLoading) return;
    isLoading = true;
    productEnd?.classList.remove('d-none');

    const params = new URLSearchParams({ q: currentQuery, page: searchPage });
    fetch(`/store/api/search?${params.toString()}`)
        .then(r => r.json())
        .then(data => {
            if (reset) productsGrid.innerHTML = '';
            productsGrid.insertAdjacentHTML('beforeend', data.html);
            attachFormListeners(productsGrid);
            if (data.has_next) {
                searchPage += 1;
            } else {
                observer?.disconnect();
                productEnd.classList.add('d-none');
            }
        })
        .catch(err => console.error(err))
        .finally(() => {
            isLoading = false;
        });
}

function startSearch(query) {
    currentQuery = query.trim();
    searchPage = 1;
    if (!currentQuery) {
        productsGrid.innerHTML = initialHTML;
        attachFormListeners(productsGrid);
        observer?.disconnect();
        productEnd?.classList.add('d-none');
        return;
    }
    loadResults(true);
    observer?.disconnect();
    if (productEnd) {
        observer = new IntersectionObserver(entries => {
            if (entries[0].isIntersecting) {
                loadResults();
            }
        }, { rootMargin: '100px' });
        observer.observe(productEnd);
    }
}

(function initStore() {
    updateCartCount();

    const searchInput = document.getElementById('productSearch');
    if (searchInput) {
        let debounce;
        searchInput.addEventListener('input', () => {
            clearTimeout(debounce);
            debounce = setTimeout(() => startSearch(searchInput.value), 300);
        });
    }

    const sortSelect = document.getElementById('sortSelect');
    if (sortSelect) {
        sortSelect.addEventListener('change', function () {
            sortProducts(this.value);
        });
    }

    attachFormListeners();

    const openBtn = document.getElementById('openFilterBtn');
    const closeBtn = document.getElementById('closeFilterBtn');
    const offcanvas = document.getElementById('filterOffcanvas');

    function closeFilters() {
        if (!offcanvas) return;
        offcanvas.classList.remove('open');
        offcanvas.addEventListener(
            'transitionend',
            () => offcanvas.classList.add('d-none'),
            { once: true }
        );
    }

    if (openBtn && offcanvas) {
        openBtn.addEventListener('click', () => {
            offcanvas.classList.remove('d-none');
            requestAnimationFrame(() => offcanvas.classList.add('open'));
        });
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', closeFilters);
    }

    const filtersForm = document.getElementById('filtersForm');
    if (filtersForm) {
        const precioRange = document.getElementById('precioRange');
        const precioValue = document.getElementById('precioValue');
        if (precioRange && precioValue) {
            precioRange.addEventListener('input', () => {
                precioValue.textContent = precioRange.value;
            });
        }
        filtersForm.addEventListener('submit', e => {
            e.preventDefault();
            const params = new URLSearchParams(new FormData(filtersForm));
            fetch(`/store?${params.toString()}`, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
            })
                .then(r => r.text())
                .then(html => {
                    document.getElementById('productsGrid').innerHTML = html;
                    closeFilters();
                });
        });
    }
})();
