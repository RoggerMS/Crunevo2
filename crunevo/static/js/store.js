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

function filterProducts() {
    const searchTerm = document
        .getElementById('productSearch')
        .value.toLowerCase();
    const products = document.querySelectorAll('.product-card');

    products.forEach(product => {
        const name = product
            .querySelector('.product-name')
            .textContent.toLowerCase();
        const description =
            product.querySelector('.product-description')?.textContent.toLowerCase() || '';

        if (name.includes(searchTerm) || description.includes(searchTerm)) {
            product.style.display = 'block';
        } else {
            product.style.display = 'none';
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

(function initStore() {
    updateCartCount();

    const searchInput = document.getElementById('productSearch');
    if (searchInput) {
        searchInput.addEventListener('input', filterProducts);
    }

    const sortSelect = document.getElementById('sortSelect');
    if (sortSelect) {
        sortSelect.addEventListener('change', function () {
            sortProducts(this.value);
        });
    }

    document.querySelectorAll('.action-form').forEach(form => {
        form.addEventListener('submit', function (e) {
            if (this.action.includes('add_to_cart')) {
                e.preventDefault();
                addToCart(this);
            }
        });
    });

    document.querySelectorAll('.favorite-form').forEach(form => {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            toggleFavorite(this);
        });
    });

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
})();
