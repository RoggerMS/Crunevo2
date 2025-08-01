// ==================== GLOBAL VARIABLES ==================== //
let currentFilter = 'all';
let currentView = 'list';
let isLoading = false;

// ==================== DOM ELEMENTS ==================== //
const filterTabs = document.querySelectorAll('.filter-tab');
const viewToggleBtns = document.querySelectorAll('.view-toggle');
const timeFilter = document.querySelector('.time-filter');
const contentCards = document.querySelectorAll('.content-card');
const loadMoreBtn = document.querySelector('.load-more-btn');
const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
const nav = document.querySelector('.nav');
const searchBtn = document.querySelector('.search-btn');
const notificationBtn = document.querySelector('.notification-btn');
const statBtns = document.querySelectorAll('.stat-btn');
const followBtns = document.querySelectorAll('.follow-btn');

// ==================== UTILITY FUNCTIONS ==================== //
function debounce(func, wait) {
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

function showElement(element, animation = 'fadeIn') {
    element.style.display = 'block';
    element.classList.add('animate-' + animation);
    setTimeout(() => {
        element.classList.remove('animate-' + animation);
    }, 300);
}

function hideElement(element, animation = 'fadeOut') {
    element.classList.add('animate-' + animation);
    setTimeout(() => {
        element.style.display = 'none';
        element.classList.remove('animate-' + animation);
    }, 300);
}

function animateCounter(element, start, end, duration) {
    const range = end - start;
    const increment = range / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= end) {
            current = end;
            clearInterval(timer);
        }
        element.textContent = Math.floor(current).toLocaleString();
    }, 16);
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'times' : 'info'}-circle"></i>
        <span>${message}</span>
        <button class="notification-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Add notification styles if not already present
    if (!document.querySelector('#notification-styles')) {
        const styles = document.createElement('style');
        styles.id = 'notification-styles';
        styles.textContent = `
            .notification {
                position: fixed;
                top: 100px;
                right: 20px;
                background: var(--glass-bg);
                backdrop-filter: blur(10px);
                border: 1px solid var(--glass-border);
                border-radius: var(--radius-lg);
                padding: var(--space-4);
                box-shadow: var(--shadow-xl);
                z-index: 1001;
                display: flex;
                align-items: center;
                gap: var(--space-3);
                max-width: 400px;
                transform: translateX(100%);
                transition: transform 0.3s ease-in-out;
            }
            .notification.show {
                transform: translateX(0);
            }
            .notification-success { border-left: 4px solid var(--success-color); }
            .notification-error { border-left: 4px solid var(--danger-color); }
            .notification-info { border-left: 4px solid var(--primary-color); }
            .notification-close {
                background: none;
                border: none;
                color: var(--gray-500);
                cursor: pointer;
                margin-left: auto;
            }
        `;
        document.head.appendChild(styles);
    }
    
    document.body.appendChild(notification);
    setTimeout(() => notification.classList.add('show'), 100);
    setTimeout(() => notification.remove(), 5000);
}

// ==================== FILTER FUNCTIONALITY ==================== //
function filterContent(filterType) {
    currentFilter = filterType;
    
    // Update filter tabs
    filterTabs.forEach(tab => {
        tab.classList.remove('active');
        if (tab.dataset.filter === filterType) {
            tab.classList.add('active');
        }
    });
    
    // Filter content cards
    contentCards.forEach(card => {
        const cardType = card.dataset.type;
        if (filterType === 'all' || cardType === filterType) {
            card.style.display = 'block';
            card.style.animation = 'slideInUp 0.5s ease-out';
        } else {
            card.style.animation = 'slideOutDown 0.3s ease-in';
            setTimeout(() => {
                card.style.display = 'none';
            }, 300);
        }
    });
    
    // Update URL without page reload
    const url = new URL(window.location);
    url.searchParams.set('filter', filterType);
    window.history.pushState({}, '', url);
    
    showNotification(`Mostrando contenido: ${getFilterLabel(filterType)}`, 'info');
}

function getFilterLabel(filterType) {
    const labels = {
        'all': 'Todo',
        'posts': 'Publicaciones',
        'notes': 'Apuntes',
        'forum': 'Foro'
    };
    return labels[filterType] || 'Todo';
}

// ==================== VIEW TOGGLE FUNCTIONALITY ==================== //
function toggleView(viewType) {
    currentView = viewType;
    
    // Update view toggle buttons
    viewToggleBtns.forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.view === viewType) {
            btn.classList.add('active');
        }
    });
    
    // Apply view changes
    const contentArea = document.querySelector('.content-area');
    contentArea.className = `content-area view-${viewType}`;
    
    // Add grid view styles if needed
    if (viewType === 'grid' && !document.querySelector('#grid-styles')) {
        const styles = document.createElement('style');
        styles.id = 'grid-styles';
        styles.textContent = `
            .content-area.view-grid .trending-content {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                gap: var(--space-6);
            }
            .content-area.view-grid .content-card {
                margin-bottom: 0;
            }
            @media (max-width: 768px) {
                .content-area.view-grid .trending-content {
                    grid-template-columns: 1fr;
                }
            }
        `;
        document.head.appendChild(styles);
    }
}

// ==================== LOAD MORE FUNCTIONALITY ==================== //
function loadMoreContent() {
    if (isLoading) return;
    
    isLoading = true;
    loadMoreBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Cargando...';
    loadMoreBtn.disabled = true;
    
    // Simulate API call
    setTimeout(() => {
        // Create new content cards (simulated)
        const newCards = createMockContent(3);
        const trendingContent = document.querySelector('.trending-content');
        
        newCards.forEach((cardHTML, index) => {
            setTimeout(() => {
                const cardElement = document.createElement('article');
                cardElement.innerHTML = cardHTML;
                cardElement.className = 'content-card ' + getRandomCardType();
                cardElement.style.opacity = '0';
                cardElement.style.transform = 'translateY(20px)';
                
                trendingContent.insertBefore(cardElement, loadMoreBtn.parentElement);
                
                // Animate in
                setTimeout(() => {
                    cardElement.style.transition = 'all 0.5s ease-out';
                    cardElement.style.opacity = '1';
                    cardElement.style.transform = 'translateY(0)';
                }, 100);
                
                // Add event listeners to new content
                addCardEventListeners(cardElement);
            }, index * 200);
        });
        
        isLoading = false;
        loadMoreBtn.innerHTML = '<i class="fas fa-plus"></i> Cargar más contenido';
        loadMoreBtn.disabled = false;
        
        showNotification('Nuevo contenido cargado exitosamente', 'success');
    }, 2000);
}

function getRandomCardType() {
    const types = ['post-card', 'note-card', 'forum-card'];
    return types[Math.floor(Math.random() * types.length)];
}

function createMockContent(count) {
    const mockTitles = [
        'Nuevas tendencias en desarrollo web 2025',
        'Guía completa de algoritmos de ordenamiento',
        '¿Cuál es tu framework favorito y por qué?',
        'Optimización de rendimiento en React',
        'Machine Learning para principiantes'
    ];
    
    const mockAuthors = [
        { name: 'Alex Rivera', avatar: 'AR' },
        { name: 'Sara Chen', avatar: 'SC' },
        { name: 'Miguel Torres', avatar: 'MT' },
        { name: 'Elena Rodríguez', avatar: 'ER' }
    ];
    
    return Array.from({ length: count }, (_, i) => {
        const title = mockTitles[Math.floor(Math.random() * mockTitles.length)];
        const author = mockAuthors[Math.floor(Math.random() * mockAuthors.length)];
        const likes = Math.floor(Math.random() * 1000) + 100;
        const comments = Math.floor(Math.random() * 200) + 10;
        
        return `
            <div class="card-content">
                <div class="author-info">
                    <img src="https://via.placeholder.com/40x40/10B981/ffffff?text=${author.avatar}" alt="${author.name}" class="author-avatar">
                    <div class="author-details">
                        <h4 class="author-name">${author.name}</h4>
                        <span class="publish-time">hace ${Math.floor(Math.random() * 12) + 1} horas</span>
                    </div>
                    <button class="follow-btn">Seguir</button>
                </div>
                <h3 class="content-title">${title}</h3>
                <p class="content-excerpt">Este es contenido nuevo generado dinámicamente para demostrar la funcionalidad de carga...</p>
                <div class="content-tags">
                    <span class="tag">Nuevo</span>
                    <span class="tag">Trending</span>
                </div>
            </div>
            <div class="card-footer">
                <div class="engagement-stats">
                    <button class="stat-btn">
                        <i class="fas fa-heart"></i>
                        <span>${likes}</span>
                    </button>
                    <button class="stat-btn">
                        <i class="fas fa-comment"></i>
                        <span>${comments}</span>
                    </button>
                </div>
            </div>
        `;
    });
}

// ==================== MOBILE MENU FUNCTIONALITY ==================== //
function toggleMobileMenu() {
    nav.classList.toggle('mobile-active');
    const isActive = nav.classList.contains('mobile-active');
    
    mobileMenuBtn.innerHTML = isActive 
        ? '<i class="fas fa-times"></i>' 
        : '<i class="fas fa-bars"></i>';
    
    // Add mobile menu styles if not already present
    if (!document.querySelector('#mobile-menu-styles')) {
        const styles = document.createElement('style');
        styles.id = 'mobile-menu-styles';
        styles.textContent = `
            @media (max-width: 768px) {
                .nav.mobile-active {
                    display: flex;
                    position: absolute;
                    top: 100%;
                    left: 0;
                    right: 0;
                    background: var(--glass-bg);
                    backdrop-filter: blur(10px);
                    border: 1px solid var(--glass-border);
                    border-radius: var(--radius-lg);
                    flex-direction: column;
                    padding: var(--space-4);
                    margin: var(--space-2);
                    box-shadow: var(--shadow-xl);
                    z-index: 1000;
                }
                .nav.mobile-active .nav-link {
                    padding: var(--space-3) var(--space-4);
                    text-align: center;
                    border-radius: var(--radius-md);
                    margin-bottom: var(--space-2);
                }
            }
        `;
        document.head.appendChild(styles);
    }
}

// ==================== SEARCH FUNCTIONALITY ==================== //
function handleSearch() {
    // Create search modal if it doesn't exist
    if (!document.querySelector('#search-modal')) {
        const modal = document.createElement('div');
        modal.id = 'search-modal';
        modal.innerHTML = `
            <div class="search-overlay" onclick="closeSearchModal()"></div>
            <div class="search-content">
                <div class="search-header">
                    <h3>Buscar en Crunevo</h3>
                    <button onclick="closeSearchModal()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="search-input-container">
                    <input type="text" id="search-input" placeholder="Buscar publicaciones, apuntes, usuarios..." autofocus>
                    <i class="fas fa-search"></i>
                </div>
                <div class="search-results">
                    <div class="search-suggestions">
                        <h4>Búsquedas populares</h4>
                        <div class="suggestion-tags">
                            <span class="suggestion-tag">JavaScript</span>
                            <span class="suggestion-tag">React</span>
                            <span class="suggestion-tag">Python</span>
                            <span class="suggestion-tag">Machine Learning</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Add search modal styles
        const styles = document.createElement('style');
        styles.textContent = `
            #search-modal {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                z-index: 2000;
                display: flex;
                align-items: flex-start;
                justify-content: center;
                padding-top: 10vh;
            }
            .search-overlay {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.5);
                backdrop-filter: blur(5px);
            }
            .search-content {
                background: var(--glass-bg);
                backdrop-filter: blur(10px);
                border: 1px solid var(--glass-border);
                border-radius: var(--radius-xl);
                width: 90%;
                max-width: 600px;
                box-shadow: var(--shadow-2xl);
                position: relative;
                z-index: 1;
                animation: searchModalIn 0.3s ease-out;
            }
            @keyframes searchModalIn {
                from { opacity: 0; transform: translateY(-20px) scale(0.95); }
                to { opacity: 1; transform: translateY(0) scale(1); }
            }
            .search-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: var(--space-6);
                border-bottom: 1px solid var(--glass-border);
            }
            .search-header h3 {
                margin: 0;
                color: var(--gray-800);
            }
            .search-header button {
                background: none;
                border: none;
                color: var(--gray-500);
                font-size: var(--font-size-lg);
                cursor: pointer;
                padding: var(--space-2);
                border-radius: var(--radius-md);
                transition: var(--transition-normal);
            }
            .search-header button:hover {
                background: var(--gray-100);
                color: var(--gray-700);
            }
            .search-input-container {
                position: relative;
                padding: var(--space-6);
            }
            #search-input {
                width: 100%;
                padding: var(--space-4) var(--space-12) var(--space-4) var(--space-4);
                border: 2px solid var(--glass-border);
                border-radius: var(--radius-lg);
                background: rgba(255, 255, 255, 0.8);
                font-size: var(--font-size-lg);
                color: var(--gray-800);
                transition: var(--transition-normal);
            }
            #search-input:focus {
                outline: none;
                border-color: var(--primary-color);
                box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
            }
            .search-input-container i {
                position: absolute;
                right: var(--space-8);
                top: 50%;
                transform: translateY(-50%);
                color: var(--gray-400);
            }
            .search-results {
                padding: var(--space-6);
                max-height: 400px;
                overflow-y: auto;
            }
            .search-suggestions h4 {
                margin-bottom: var(--space-4);
                color: var(--gray-600);
                font-size: var(--font-size-sm);
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            .suggestion-tags {
                display: flex;
                flex-wrap: wrap;
                gap: var(--space-2);
            }
            .suggestion-tag {
                background: rgba(79, 70, 229, 0.1);
                color: var(--primary-color);
                padding: var(--space-2) var(--space-4);
                border-radius: var(--radius-full);
                font-size: var(--font-size-sm);
                cursor: pointer;
                transition: var(--transition-normal);
            }
            .suggestion-tag:hover {
                background: var(--primary-color);
                color: white;
            }
        `;
        document.head.appendChild(styles);
        document.body.appendChild(modal);
        
        // Add search input event listener
        const searchInput = document.getElementById('search-input');
        searchInput.addEventListener('input', debounce(performSearch, 300));
        
        // Add suggestion tag clicks
        document.querySelectorAll('.suggestion-tag').forEach(tag => {
            tag.addEventListener('click', () => {
                searchInput.value = tag.textContent;
                performSearch();
            });
        });
    }
}

function closeSearchModal() {
    const modal = document.querySelector('#search-modal');
    if (modal) {
        modal.style.animation = 'searchModalOut 0.3s ease-in';
        setTimeout(() => modal.remove(), 300);
    }
}

function performSearch() {
    const query = document.getElementById('search-input').value;
    const resultsContainer = document.querySelector('.search-results');
    
    if (query.length < 2) {
        resultsContainer.innerHTML = `
            <div class="search-suggestions">
                <h4>Búsquedas populares</h4>
                <div class="suggestion-tags">
                    <span class="suggestion-tag">JavaScript</span>
                    <span class="suggestion-tag">React</span>
                    <span class="suggestion-tag">Python</span>
                    <span class="suggestion-tag">Machine Learning</span>
                </div>
            </div>
        `;
        return;
    }
    
    // Simulate search results
    resultsContainer.innerHTML = `
        <div class="search-loading">
            <i class="fas fa-spinner fa-spin"></i>
            Buscando "${query}"...
        </div>
    `;
    
    setTimeout(() => {
        resultsContainer.innerHTML = `
            <div class="search-results-list">
                <h4>Resultados para "${query}"</h4>
                <div class="search-result-item">
                    <i class="fas fa-newspaper"></i>
                    <div>
                        <h5>Tutorial de ${query} para principiantes</h5>
                        <p>Por María González • hace 2 horas</p>
                    </div>
                </div>
                <div class="search-result-item">
                    <i class="fas fa-file-alt"></i>
                    <div>
                        <h5>Apuntes completos de ${query}</h5>
                        <p>Por Carlos López • hace 1 día</p>
                    </div>
                </div>
                <div class="search-result-item">
                    <i class="fas fa-user"></i>
                    <div>
                        <h5>@${query.toLowerCase()}expert</h5>
                        <p>Especialista en ${query}</p>
                    </div>
                </div>
            </div>
        `;
        
        // Add result item styles
        if (!document.querySelector('#search-result-styles')) {
            const styles = document.createElement('style');
            styles.id = 'search-result-styles';
            styles.textContent = `
                .search-loading {
                    text-align: center;
                    padding: var(--space-8);
                    color: var(--gray-500);
                }
                .search-results-list h4 {
                    margin-bottom: var(--space-4);
                    color: var(--gray-800);
                }
                .search-result-item {
                    display: flex;
                    align-items: center;
                    gap: var(--space-3);
                    padding: var(--space-3);
                    border-radius: var(--radius-md);
                    cursor: pointer;
                    transition: var(--transition-normal);
                }
                .search-result-item:hover {
                    background: rgba(79, 70, 229, 0.1);
                }
                .search-result-item i {
                    color: var(--primary-color);
                    font-size: var(--font-size-lg);
                }
                .search-result-item h5 {
                    margin: 0 0 var(--space-1) 0;
                    color: var(--gray-800);
                }
                .search-result-item p {
                    margin: 0;
                    font-size: var(--font-size-sm);
                    color: var(--gray-500);
                }
            `;
            document.head.appendChild(styles);
        }
    }, 1000);
}

// ==================== INTERACTION HANDLERS ==================== //
function handleStatButtonClick(btn) {
    const icon = btn.querySelector('i');
    const count = btn.querySelector('span');
    const currentCount = parseInt(count.textContent.replace(/[^\d]/g, ''));
    
    // Toggle active state
    btn.classList.toggle('active');
    
    if (btn.classList.contains('active')) {
        // Animate icon
        icon.style.transform = 'scale(1.3)';
        icon.style.color = 'var(--danger-color)';
        
        // Increment count
        count.textContent = (currentCount + 1).toLocaleString();
        
        // Add bounce animation
        btn.style.animation = 'bounce 0.6s ease-out';
    } else {
        // Reset icon
        icon.style.transform = 'scale(1)';
        icon.style.color = '';
        
        // Decrement count
        count.textContent = Math.max(0, currentCount - 1).toLocaleString();
    }
    
    setTimeout(() => {
        icon.style.transform = '';
        btn.style.animation = '';
    }, 600);
}

function handleFollowButtonClick(btn) {
    const isFollowing = btn.classList.contains('following');
    
    if (isFollowing) {
        btn.textContent = 'Seguir';
        btn.classList.remove('following');
        showNotification('Has dejado de seguir a este usuario', 'info');
    } else {
        btn.textContent = 'Siguiendo';
        btn.classList.add('following');
        btn.style.animation = 'pulse 0.6s ease-out';
        showNotification('Ahora sigues a este usuario', 'success');
    }
    
    setTimeout(() => {
        btn.style.animation = '';
    }, 600);
}

// ==================== EVENT LISTENERS SETUP ==================== //
function addCardEventListeners(card) {
    // Add event listeners to stat buttons in this card
    const cardStatBtns = card.querySelectorAll('.stat-btn');
    cardStatBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            handleStatButtonClick(btn);
        });
    });
    
    // Add event listeners to follow buttons in this card
    const cardFollowBtns = card.querySelectorAll('.follow-btn');
    cardFollowBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            handleFollowButtonClick(btn);
        });
    });
}

function initializeEventListeners() {
    // Filter tabs
    filterTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            filterContent(tab.dataset.filter);
        });
    });
    
    // View toggle buttons
    viewToggleBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            toggleView(btn.dataset.view);
        });
    });
    
    // Time filter
    if (timeFilter) {
        timeFilter.addEventListener('change', (e) => {
            showNotification(`Filtro de tiempo cambiado: ${e.target.options[e.target.selectedIndex].text}`, 'info');
        });
    }
    
    // Load more button
    if (loadMoreBtn) {
        loadMoreBtn.addEventListener('click', loadMoreContent);
    }
    
    // Mobile menu button
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', toggleMobileMenu);
    }
    
    // Search button
    if (searchBtn) {
        searchBtn.addEventListener('click', handleSearch);
    }
    
    // Notification button
    if (notificationBtn) {
        notificationBtn.addEventListener('click', () => {
            showNotification('No tienes notificaciones nuevas', 'info');
        });
    }
    
    // Stat buttons
    statBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            handleStatButtonClick(btn);
        });
    });
    
    // Follow buttons
    followBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            handleFollowButtonClick(btn);
        });
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + K for search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            handleSearch();
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            closeSearchModal();
        }
    });
    
    // Click outside to close mobile menu
    document.addEventListener('click', (e) => {
        if (nav.classList.contains('mobile-active') && 
            !nav.contains(e.target) && 
            !mobileMenuBtn.contains(e.target)) {
            toggleMobileMenu();
        }
    });
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Lazy loading for images
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src || img.src;
                    img.classList.remove('lazy');
                    observer.unobserve(img);
                }
            });
        });
        
        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }
}

// ==================== ANIMATIONS ==================== //
function addAnimationStyles() {
    if (!document.querySelector('#animation-styles')) {
        const styles = document.createElement('style');
        styles.id = 'animation-styles';
        styles.textContent = `
            @keyframes slideInUp {
                from {
                    opacity: 0;
                    transform: translateY(30px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            @keyframes slideOutDown {
                from {
                    opacity: 1;
                    transform: translateY(0);
                }
                to {
                    opacity: 0;
                    transform: translateY(30px);
                }
            }
            
            @keyframes bounce {
                0%, 20%, 53%, 80%, 100% {
                    transform: translateY(0);
                }
                40%, 43% {
                    transform: translateY(-15px);
                }
                70% {
                    transform: translateY(-7px);
                }
                90% {
                    transform: translateY(-3px);
                }
            }
            
            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.05); }
                100% { transform: scale(1); }
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            
            @keyframes fadeOut {
                from { opacity: 1; }
                to { opacity: 0; }
            }
            
            @keyframes searchModalOut {
                from { 
                    opacity: 1; 
                    transform: translateY(0) scale(1); 
                }
                to { 
                    opacity: 0; 
                    transform: translateY(-20px) scale(0.95); 
                }
            }
            
            .stat-btn.active i {
                color: var(--danger-color) !important;
            }
            
            .follow-btn.following {
                background: var(--success-color) !important;
            }
            
            .lazy {
                opacity: 0;
                transition: opacity 0.3s;
            }
            
            .content-card {
                transition: var(--transition-normal);
            }
            
            .content-card:hover .author-avatar {
                transform: scale(1.05);
            }
            
            .content-card:hover .trending-badge {
                animation: pulse 1s ease-in-out;
            }
        `;
        document.head.appendChild(styles);
    }
}

// ==================== INITIALIZATION ==================== //
function initializeCounters() {
    // Animate stat numbers on page load
    document.querySelectorAll('.stat-number').forEach(element => {
        const value = parseInt(element.textContent.replace(/[^\d]/g, ''));
        if (value > 0) {
            element.textContent = '0';
            setTimeout(() => {
                animateCounter(element, 0, value, 2000);
            }, 500);
        }
    });
}

function handleURLParams() {
    // Check for filter parameter in URL
    const urlParams = new URLSearchParams(window.location.search);
    const filterParam = urlParams.get('filter');
    
    if (filterParam && ['all', 'posts', 'notes', 'forum'].includes(filterParam)) {
        filterContent(filterParam);
    }
}

// ==================== MAIN INITIALIZATION ==================== //
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all functionality
    addAnimationStyles();
    initializeEventListeners();
    initializeCounters();
    handleURLParams();
    
    // Add initial content card event listeners
    contentCards.forEach(card => {
        addCardEventListeners(card);
    });
    
    // Add entrance animations to existing content
    setTimeout(() => {
        contentCards.forEach((card, index) => {
            card.style.animation = `slideInUp 0.5s ease-out ${index * 0.1}s both`;
        });
    }, 300);
    
    // Show welcome notification
    setTimeout(() => {
        showNotification('¡Bienvenido a la nueva página de Trending de Crunevo!', 'success');
    }, 1000);
    
    console.log('Crunevo Trending page initialized successfully! 🚀');
});

// ==================== WINDOW RESIZE HANDLER ==================== //
window.addEventListener('resize', debounce(() => {
    // Close mobile menu on resize to larger screen
    if (window.innerWidth > 768 && nav.classList.contains('mobile-active')) {
        toggleMobileMenu();
    }
}, 250));

// ==================== EXPORT FOR TESTING ==================== //
window.CrunevoTrending = {
    filterContent,
    toggleView,
    loadMoreContent,
    toggleMobileMenu,
    handleSearch,
    showNotification
};