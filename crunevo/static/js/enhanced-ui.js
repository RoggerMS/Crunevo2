
// Enhanced UI interactions and animations for CRUNEVO

// Initialization handled in main.js
window.initializeEnhancedUI = initializeEnhancedUI;

function initializeEnhancedUI() {
    // Initialize floating action buttons
    initFloatingButtons();
    
    // Initialize achievement animations
    initAchievementAnimations();
    
    // Initialize story rings
    initStoryRings();
    
    // Initialize image gallery enhancements
    initImageGalleryEnhancements();
    
    // Initialize mission completion animations
    initMissionAnimations();
    
    // Initialize enhanced tooltips
    initEnhancedTooltips();
    
    // Initialize quick view modals
    initQuickViewModals();
    
}

function initFloatingButtons() {
    // Floating cart button with cart count
    const cartButton = document.querySelector('.floating-cart-btn');
    if (cartButton) {
        updateCartCount();
        
        cartButton.addEventListener('click', function() {
            window.location.href = '/store/carrito';
        });
    }
    
    // Profile edit buttons
    const avatarEditBtns = document.querySelectorAll('.avatar-edit-btn');
    avatarEditBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            // Trigger file input for avatar upload
            const fileInput = document.createElement('input');
            fileInput.type = 'file';
            fileInput.accept = 'image/*';
            fileInput.onchange = function(e) {
                uploadAvatar(e.target.files[0]);
            };
            fileInput.click();
        });
    });
    
    // Banner edit button
    const bannerEditBtn = document.querySelector('.profile-banner-edit');
    if (bannerEditBtn) {
        bannerEditBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const fileInput = document.createElement('input');
            fileInput.type = 'file';
            fileInput.accept = 'image/*';
            fileInput.onchange = function(e) {
                uploadBanner(e.target.files[0]);
            };
            fileInput.click();
        });
    }
}

function initAchievementAnimations() {
    // Animate achievements on hover
    const achievementBadges = document.querySelectorAll('.achievement-badge');
    achievementBadges.forEach(badge => {
        badge.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.1) rotate(5deg)';
        });
        
        badge.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1) rotate(0deg)';
        });
        
        badge.addEventListener('click', function() {
            showAchievementModal(this.dataset.achievementId);
        });
    });
}

function initStoryRings() {
    const storyRings = document.querySelectorAll('.story-ring');
    storyRings.forEach(ring => {
        ring.addEventListener('click', function() {
            const userId = this.dataset.userId;
            openStoryViewer(userId);
        });
        
        // Add animation for new stories
        if (this.dataset.hasNewStory === 'true') {
            ring.classList.add('animated');
        }
    });
}

function initImageGalleryEnhancements() {
    // Enhanced image gallery interactions
    const galleryImages = document.querySelectorAll('.gallery-img');
    galleryImages.forEach((img, index) => {
        img.addEventListener('click', function() {
            const postId = this.closest('[data-post-id]')?.dataset.postId;
            openImageModal(this.src, index, postId);
        });
        
        // Add loading placeholder
        img.addEventListener('load', function() {
            this.classList.add('loaded');
        });
        
        // Lazy loading intersection observer
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        if (img.dataset.src) {
                            img.src = img.dataset.src;
                            img.removeAttribute('data-src');
                            observer.unobserve(img);
                        }
                    }
                });
            });
            
            if (img.dataset.src) {
                imageObserver.observe(img);
            }
        }
    });
}

function initMissionAnimations() {
    // Mission completion with confetti
    const claimButtons = document.querySelectorAll('.reward-claim-btn');
    claimButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            if (this.classList.contains('claimed')) return;
            
            const missionId = this.dataset.missionId;
            claimMissionReward(missionId, this);
        });
    });
}

function claimMissionReward(missionId, button) {
    // Show loading state
    button.disabled = true;
    button.innerHTML = '<i class="bi bi-hourglass-split"></i> Reclamando...';
    
    // Simulate API call (replace with actual endpoint)
    csrfFetch(`/missions/claim/${missionId}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Trigger confetti animation
            triggerConfetti(button.closest('.mission-complete-animation'));
            
            // Update button state
            button.classList.add('claimed');
            button.innerHTML = '<i class="bi bi-check-circle"></i> ¡Reclamado!';
            
            // Show reward notification
            showRewardNotification(data.reward);
            
            // Update user credits in navbar
            updateUserCredits(data.newCredits);
        } else {
            button.disabled = false;
            button.innerHTML = '<i class="bi bi-gift"></i> Reclamar Recompensa';
            showErrorToast(data.message || 'Error al reclamar recompensa');
        }
    })
    .catch(error => {
        console.error('Error claiming reward:', error);
        button.disabled = false;
        button.innerHTML = '<i class="bi bi-gift"></i> Reclamar Recompensa';
        showErrorToast('Error de conexión');
    });
}

function triggerConfetti(container) {
    if (!container) return;
    
    const confettiContainer = document.createElement('div');
    confettiContainer.className = 'confetti-container';
    container.appendChild(confettiContainer);
    
    // Create confetti pieces
    for (let i = 0; i < 50; i++) {
        const confetti = document.createElement('div');
        confetti.className = 'confetti-piece';
        confetti.style.left = Math.random() * 100 + '%';
        confetti.style.animationDelay = Math.random() * 3 + 's';
        confetti.style.animationDuration = (Math.random() * 2 + 2) + 's';
        confettiContainer.appendChild(confetti);
    }
    
    // Remove confetti after animation
    setTimeout(() => {
        confettiContainer.remove();
    }, 5000);
}


function initEnhancedTooltips() {
    // Initialize custom tooltips for elements with data-tooltip
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    tooltipElements.forEach(element => {
        element.classList.add('tooltip-enhanced');
    });
}

function initQuickViewModals() {
    // Quick view for posts
    const quickViewBtns = document.querySelectorAll('.quick-view-btn');
    quickViewBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const target = this.dataset.postId || this.dataset.url;
            openQuickView(target);
        });
    });
}

function openQuickView(target) {
    // Create modal
    const modal = document.createElement('div');
    modal.className = 'modal fade quick-view-modal';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Vista Rápida</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="text-center">
                        <div class="spinner-modern"></div>
                        <p class="mt-3">Cargando...</p>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();

    const isUrl = typeof target === 'string' && (target.startsWith('http') || target.startsWith('/'));
    if (isUrl) {
        const ext = target.split('?')[0].split('.').pop().toLowerCase();
        modal.querySelector('.modal-body').innerHTML = `<div id="noteViewer" data-url="${target}" data-type="${ext === 'pdf' ? 'pdf' : 'image'}"></div>`;
        if (typeof initNoteViewer === 'function') initNoteViewer();
    } else {
        // Load post content
        fetch(`/feed/post/${target}/quick-view`)
            .then(response => response.text())
            .then(html => {
                modal.querySelector('.modal-body').innerHTML = html;
            })
            .catch(error => {
                console.error('Error loading quick view:', error);
                modal.querySelector('.modal-body').innerHTML = `
                    <div class="text-center text-danger">
                        <i class="bi bi-exclamation-triangle fs-1"></i>
                        <p class="mt-3">Error al cargar el contenido</p>
                    </div>`;
            });
    }
    
    // Remove modal when hidden
    modal.addEventListener('hidden.bs.modal', function() {
        modal.remove();
    });
}


// Utility functions
function updateCartCount() {
    fetch('/tienda/api/cart_count')
        .then(response => response.json())
        .then(data => {
            const cartCount = document.querySelector('.floating-cart-btn .cart-count');
            if (cartCount) {
                cartCount.textContent = data.count;
                cartCount.style.display = data.count > 0 ? 'flex' : 'none';
            }
        })
        .catch(error => console.error('Error updating cart count:', error));
}

function uploadAvatar(file) {
    if (!file) return;
    
    const formData = new FormData();
    formData.append('avatar', file);
    
    csrfFetch('/auth/upload-profile-picture', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update avatar in UI
            document.querySelectorAll('.profile-avatar img, .navbar .avatar').forEach(img => {
                img.src = data.avatarUrl;
            });
            showSuccessToast('Avatar actualizado correctamente');
        } else {
            showErrorToast(data.message || 'Error al subir avatar');
        }
    })
    .catch(error => {
        console.error('Error uploading avatar:', error);
        showErrorToast('Error de conexión');
    });
}

function uploadBanner(file) {
    if (!file) return;

    console.log('Banner file selected:', file);

    const formData = new FormData();
    formData.append('banner', file);

    csrfFetch('/auth/upload-banner', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.querySelectorAll('.profile-banner').forEach(img => {
                img.src = data.bannerUrl;
            });
            showSuccessToast('Banner actualizado correctamente');
        } else {
            showErrorToast(data.message || 'Error al subir banner');
        }
    })
    .catch(error => {
        console.error('Error uploading banner:', error);
        showErrorToast('Error de conexión');
    });
}

function showSuccessToast(message) {
    showToast(message, 'success');
}

function showErrorToast(message) {
    showToast(message, 'error');
}

function showToast(message, type = 'info') {
    const toastContainer = document.querySelector('.toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast toast-notification ${type}`;
    toast.innerHTML = `
        <div class="toast-body d-flex align-items-center">
            <i class="bi bi-${getToastIcon(type)} me-2"></i>
            <span class="flex-grow-1">${message}</span>
            <button type="button" class="btn-close btn-sm ms-2" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const toastInstance = new bootstrap.Toast(toast, {
        autohide: true,
        delay: 5000
    });
    
    toastInstance.show();
    
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '1060';
    document.body.appendChild(container);
    return container;
}

function getToastIcon(type) {
    switch (type) {
        case 'success': return 'check-circle';
        case 'error': return 'exclamation-triangle';
        case 'warning': return 'exclamation-triangle';
        default: return 'info-circle';
    }
}

function showRewardNotification(reward) {
    showSuccessToast(`¡Has ganado ${reward.amount} ${reward.type}!`);
}

function updateUserCredits(newCredits) {
    const creditsElement = document.querySelector('[data-user-credits]');
    if (creditsElement) {
        creditsElement.textContent = newCredits;
    }
}

// Export functions for global use
window.CRUNEVO_UI = {
    showSuccessToast,
    showErrorToast,
    triggerConfetti,
    updateCartCount,
    showRewardNotification
};
