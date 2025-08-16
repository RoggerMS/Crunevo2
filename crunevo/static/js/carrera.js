
// Career Module JavaScript
class CareerModule {
    constructor() {
        this.currentTab = 'publicaciones';
        this.currentPage = 1;
        this.isLoading = false;
        this.chatTimer = null;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadCurrentTab();
        this.startChatUpdates();
    }
    
    bindEvents() {
        // Tab navigation
        document.querySelectorAll('.career-nav .nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchTab(link.dataset.tab);
            });
        });
        
        // Post form
        const postForm = document.getElementById('postForm');
        if (postForm) {
            postForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.submitPost();
            });
        }
        
        // Chat form
        const chatForm = document.getElementById('chatForm');
        if (chatForm) {
            chatForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.sendChatMessage();
            });
        }
        
        // Course filter
        const courseFilter = document.getElementById('courseFilter');
        if (courseFilter) {
            let timeout;
            courseFilter.addEventListener('input', (e) => {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    this.filterNotes(e.target.value);
                }, 300);
            });
        }
        
        // Load more posts
        const loadMoreBtn = document.getElementById('loadMorePosts');
        if (loadMoreBtn) {
            loadMoreBtn.addEventListener('click', () => {
                this.loadMorePosts();
            });
        }
    }
    
    switchTab(tab) {
        if (this.isLoading) return;
        
        this.currentTab = tab;
        this.currentPage = 1;
        
        // Update active tab
        document.querySelectorAll('.career-nav .nav-link').forEach(link => {
            link.classList.remove('active');
        });
        const tabLink = document.querySelector(`[data-tab="${tab}"]`);
        if (tabLink) {
            tabLink.classList.add('active');
        }
        
        // Update tab content
        document.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.remove('show', 'active');
        });
        const tabElement = document.getElementById(tab);
        if (tabElement) {
            tabElement.classList.add('show', 'active');
        }
        
        // Load tab content
        this.loadCurrentTab();
        
        // Update URL
        const url = new URL(window.location);
        url.searchParams.set('tab', tab);
        window.history.pushState({}, '', url);
    }
    
    loadCurrentTab() {
        this.showLoading();
        
        switch (this.currentTab) {
            case 'publicaciones':
                this.loadPublicaciones();
                break;
            case 'apuntes':
                this.loadApuntes();
                break;
            case 'cursos':
                this.loadCursos();
                break;
            case 'clubes':
                this.loadClubes();
                break;
            case 'eventos':
                this.loadEventos();
                break;
            case 'chat':
                this.loadChat();
                break;
            case 'destacados':
                this.loadDestacados();
                break;
        }
    }
    
    async loadPublicaciones() {
        try {
            const response = await fetch(`/mi-carrera/api/publicaciones?page=${this.currentPage}`);
            const data = await response.json();
            
            if (data.posts) {
                this.renderPosts(data.posts, this.currentPage === 1);
                this.updateLoadMoreButton(data.has_next);
            }
        } catch (error) {
            this.showError('Error al cargar publicaciones');
        } finally {
            this.hideLoading();
        }
    }
    
    async loadApuntes(courseFilter = '') {
        try {
            const response = await fetch(`/mi-carrera/api/apuntes?course=${courseFilter}`);
            const data = await response.json();
            
            if (data.notes) {
                this.renderNotes(data.notes);
            }
        } catch (error) {
            this.showError('Error al cargar apuntes');
        } finally {
            this.hideLoading();
        }
    }
    
    async loadCursos() {
        try {
            const response = await fetch('/mi-carrera/api/cursos');
            const data = await response.json();
            
            if (data.courses) {
                this.renderCourses(data.courses);
            }
        } catch (error) {
            this.showError('Error al cargar cursos');
        } finally {
            this.hideLoading();
        }
    }
    
    async loadClubes() {
        try {
            const response = await fetch('/mi-carrera/api/clubes');
            const data = await response.json();
            
            if (data.clubs) {
                this.renderClubs(data.clubs);
            }
        } catch (error) {
            this.showError('Error al cargar clubes');
        } finally {
            this.hideLoading();
        }
    }
    
    async loadEventos() {
        try {
            const response = await fetch('/mi-carrera/api/eventos');
            const data = await response.json();
            
            if (data.events) {
                this.renderEvents(data.events);
            }
        } catch (error) {
            this.showError('Error al cargar eventos');
        } finally {
            this.hideLoading();
        }
    }
    
    async loadChat() {
        try {
            const response = await fetch('/mi-carrera/api/chat');
            const data = await response.json();
            
            if (data.messages) {
                this.renderChatMessages(data.messages);
                this.updateActiveUsers(data.active_users);
            }
        } catch (error) {
            this.showError('Error al cargar chat');
        } finally {
            this.hideLoading();
        }
    }
    
    async loadDestacados() {
        try {
            const response = await fetch('/mi-carrera/api/destacados');
            const data = await response.json();
            
            if (data.users) {
                this.renderFeaturedUsers(data.users);
            }
        } catch (error) {
            this.showError('Error al cargar estudiantes destacados');
        } finally {
            this.hideLoading();
        }
    }
    
    renderPosts(posts, replace = true) {
        const container = document.getElementById('postsList');
        if (!container) return;
        
        if (replace) {
            container.innerHTML = '';
        }
        
        posts.forEach(post => {
            const postElement = this.createPostElement(post);
            container.appendChild(postElement);
        });
    }
    
    createPostElement(post) {
        const div = document.createElement('div');
        div.className = 'card career-card mb-4';
        div.innerHTML = `
            <div class="card-body">
                <div class="d-flex gap-3">
                    <img src="${post.author.avatar_url}" alt="${post.author.username}" 
                         class="rounded-circle" width="48" height="48">
                    <div class="flex-grow-1">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <div>
                                <h6 class="mb-0">${post.author.username}</h6>
                                <small class="text-muted">${post.author.career} • ${post.created_at}</small>
                            </div>
                        </div>
                        <p class="mb-3">${post.content}</p>
                        <div class="d-flex gap-3">
                            <button class="btn btn-outline-primary btn-sm">
                                <i class="bi bi-heart me-1"></i>${post.likes}
                            </button>
                            <button class="btn btn-outline-secondary btn-sm">
                                <i class="bi bi-chat me-1"></i>${post.comments_count}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        return div;
    }
    
    renderNotes(notes) {
        const container = document.getElementById('notesList');
        if (!container) return;
        
        container.innerHTML = '';
        
        notes.forEach(note => {
            const noteElement = this.createNoteElement(note);
            container.appendChild(noteElement);
        });
    }
    
    createNoteElement(note) {
        const div = document.createElement('div');
        div.className = 'col-lg-4 col-md-6';
        div.innerHTML = `
            <div class="card note-card h-100">
                <div class="card-header">
                    <div class="d-flex justify-content-between align-items-start">
                        <h6 class="mb-0">${note.title}</h6>
                        <span class="badge bg-primary">${note.course || 'General'}</span>
                    </div>
                </div>
                <div class="card-body">
                    <p class="text-muted small mb-3">${note.description}</p>
                    <div class="d-flex justify-content-between align-items-center">
                        <small class="text-muted">
                            <i class="bi bi-person me-1"></i>${note.author.username}
                        </small>
                        <div class="d-flex gap-2">
                            <small class="text-muted">
                                <i class="bi bi-eye me-1"></i>${note.views}
                            </small>
                            <small class="text-muted">
                                <i class="bi bi-download me-1"></i>${note.downloads}
                            </small>
                        </div>
                    </div>
                </div>
                <div class="card-footer bg-transparent">
                    <a href="/notes/${note.id}" class="btn btn-primary btn-sm w-100">
                        Ver Apunte
                    </a>
                </div>
            </div>
        `;
        return div;
    }
    
    renderCourses(courses) {
        const container = document.getElementById('coursesList');
        if (!container) return;
        
        container.innerHTML = '';
        
        courses.forEach(course => {
            const courseElement = this.createCourseElement(course);
            container.appendChild(courseElement);
        });
    }
    
    createCourseElement(course) {
        const div = document.createElement('div');
        div.className = 'col-lg-4 col-md-6';
        div.innerHTML = `
            <div class="card course-card h-100">
                <div class="course-thumbnail">
                    ${course.thumbnail_url ? 
                        `<img src="${course.thumbnail_url}" alt="${course.title}" class="w-100 h-100 object-fit-cover">` :
                        `<i class="bi bi-play-circle"></i>`
                    }
                </div>
                <div class="card-body">
                    <h6 class="mb-2">${course.title}</h6>
                    <p class="text-muted small mb-3">${course.description}</p>
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <span class="badge badge-difficulty badge-${course.difficulty.toLowerCase()}">${course.difficulty}</span>
                        <small class="text-muted">${course.duration_minutes} min</small>
                    </div>
                    <div class="d-flex justify-content-between align-items-center">
                        <small class="text-muted">
                            <i class="bi bi-person me-1"></i>${course.creator.username}
                        </small>
                        <small class="text-muted">
                            <i class="bi bi-eye me-1"></i>${course.views}
                        </small>
                    </div>
                </div>
                <div class="card-footer bg-transparent">
                    <a href="/courses/${course.id}" class="btn btn-primary btn-sm w-100">
                        Ver Curso
                    </a>
                </div>
            </div>
        `;
        return div;
    }
    
    renderClubs(clubs) {
        const container = document.getElementById('clubsList');
        if (!container) return;
        
        container.innerHTML = '';
        
        clubs.forEach(club => {
            const clubElement = this.createClubElement(club);
            container.appendChild(clubElement);
        });
    }
    
    createClubElement(club) {
        const div = document.createElement('div');
        div.className = 'col-md-6';
        div.innerHTML = `
            <div class="card club-card h-100">
                <div class="card-body">
                    <div class="d-flex gap-3">
                        <img src="${club.avatar_url || '/static/img/default.png'}" alt="${club.name}" 
                             class="club-avatar">
                        <div class="flex-grow-1">
                            <h6 class="mb-1">${club.name}</h6>
                            <p class="text-muted small mb-2">${club.description}</p>
                            <div class="d-flex justify-content-between align-items-center">
                                <small class="text-muted">
                                    <i class="bi bi-people me-1"></i>${club.member_count} miembros
                                </small>
                                ${club.is_member ? 
                                    '<span class="badge bg-success">Miembro</span>' :
                                    `<button class="btn btn-outline-primary btn-sm" onclick="careerModule.joinClub(${club.id})">
                                        Unirse
                                    </button>`
                                }
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        return div;
    }
    
    renderEvents(events) {
        const container = document.getElementById('eventsList');
        if (!container) return;
        
        container.innerHTML = '';
        
        events.forEach(event => {
            const eventElement = this.createEventElement(event);
            container.appendChild(eventElement);
        });
    }
    
    createEventElement(event) {
        const div = document.createElement('div');
        div.className = 'col-lg-4 col-md-6';
        div.innerHTML = `
            <div class="card event-card h-100">
                <div class="event-image">
                    ${event.image_url ? 
                        `<img src="${event.image_url}" alt="${event.title}" class="w-100 h-100 object-fit-cover">` :
                        `<i class="bi bi-calendar-event"></i>`
                    }
                </div>
                <div class="card-body">
                    <h6 class="mb-2">${event.title}</h6>
                    <p class="text-muted small mb-3">${event.description}</p>
                    <div class="d-flex justify-content-between align-items-center">
                        <small class="text-muted">
                            <i class="bi bi-calendar me-1"></i>${event.event_date}
                        </small>
                        <span class="badge badge-career">${event.category}</span>
                    </div>
                </div>
                <div class="card-footer bg-transparent">
                    <a href="/events/${event.id}" class="btn btn-primary btn-sm w-100">
                        Ver Evento
                    </a>
                </div>
            </div>
        `;
        return div;
    }
    
    renderChatMessages(messages) {
        const container = document.getElementById('chatMessages');
        if (!container) return;
        
        container.innerHTML = '';
        
        messages.forEach(message => {
            const messageElement = this.createMessageElement(message);
            container.appendChild(messageElement);
        });
        
        // Scroll to bottom
        container.scrollTop = container.scrollHeight;
    }
    
    createMessageElement(message) {
        const div = document.createElement('div');
        div.className = 'chat-message';
        div.innerHTML = `
            <div class="message-header">
                <strong>${message.sender.username}</strong>
                <span class="text-muted ms-2">${message.timestamp}</span>
            </div>
            <div class="message-content">
                ${message.content}
            </div>
        `;
        return div;
    }
    
    renderFeaturedUsers(users) {
        const container = document.getElementById('featuredUsersList');
        if (!container) return;
        
        container.innerHTML = '';
        
        users.forEach((user, index) => {
            const userElement = this.createUserElement(user, index + 1);
            container.appendChild(userElement);
        });
    }
    
    createUserElement(user, rank) {
        const div = document.createElement('div');
        div.className = 'col-lg-4 col-md-6';
        div.innerHTML = `
            <div class="card user-card h-100">
                <div class="card-body text-center">
                    <div class="position-relative d-inline-block mb-3">
                        <img src="${user.avatar_url}" alt="${user.username}" class="user-avatar">
                        <span class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-warning">
                            #${rank}
                        </span>
                        ${user.verification_level >= 2 ? 
                            '<i class="bi bi-patch-check-fill position-absolute bottom-0 end-0 text-primary"></i>' : 
                            ''
                        }
                    </div>
                    <h6 class="mb-1">${user.username}</h6>
                    <div class="row text-center mb-3">
                        <div class="col-4">
                            <div class="fw-bold text-primary">${user.credits}</div>
                            <small class="text-muted">Créditos</small>
                        </div>
                        <div class="col-4">
                            <div class="fw-bold text-success">${user.notes_count}</div>
                            <small class="text-muted">Apuntes</small>
                        </div>
                        <div class="col-4">
                            <div class="fw-bold text-info">${user.posts_count}</div>
                            <small class="text-muted">Posts</small>
                        </div>
                    </div>
                    <a href="/perfil/${user.username}" class="btn btn-outline-primary btn-sm w-100">
                        Ver Perfil
                    </a>
                </div>
            </div>
        `;
        return div;
    }
    
    async submitPost() {
        const postContentEl = document.getElementById('postContent');
        if (!postContentEl) return;
        const content = postContentEl.value.trim();
        if (!content) return;
        
        try {
            const formData = new FormData();
            formData.append('content', content);
            const csrfTokenEl = document.querySelector('[name="csrf_token"]');
            if (csrfTokenEl) {
                formData.append('csrf_token', csrfTokenEl.value);
            }
            
            const response = await fetch('/feed/create_post', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const postContentEl = document.getElementById('postContent');
                if (postContentEl) {
                    postContentEl.value = '';
                }
                this.loadPublicaciones(); // Reload posts
                this.showSuccess('Publicación creada exitosamente');
            } else {
                this.showError('Error al crear la publicación');
            }
        } catch (error) {
            this.showError('Error al crear la publicación');
        }
    }
    
    async sendChatMessage() {
        const input = document.getElementById('chatInput');
        if (!input) return;
        const content = input.value.trim();
        if (!content) return;
        
        try {
            const response = await fetch('/mi-carrera/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content })
            });
            
            if (response.ok) {
                if (input) {
                    input.value = '';
                }
                this.loadChat(); // Reload chat
            } else {
                this.showError('Error al enviar mensaje');
            }
        } catch (error) {
            this.showError('Error al enviar mensaje');
        }
    }
    
    async joinClub(clubId) {
        try {
            const response = await fetch(`/mi-carrera/api/join-club/${clubId}`, {
                method: 'POST'
            });
            
            if (response.ok) {
                this.loadClubes(); // Reload clubs
                this.showSuccess('Te has unido al club exitosamente');
            } else {
                this.showError('Error al unirse al club');
            }
        } catch (error) {
            this.showError('Error al unirse al club');
        }
    }
    
    async loadMorePosts() {
        this.currentPage++;
        this.loadPublicaciones();
    }
    
    async filterNotes(courseFilter) {
        this.loadApuntes(courseFilter);
    }
    
    updateLoadMoreButton(hasNext) {
        const button = document.getElementById('loadMorePosts');
        if (button) {
            button.style.display = hasNext ? 'block' : 'none';
        }
    }
    
    updateActiveUsers(count) {
        const elements = [
            document.getElementById('activeUsersCount'),
            document.getElementById('chatActiveUsers')
        ];
        
        elements.forEach(el => {
            if (el) {
                if (el.id === 'chatActiveUsers') {
                    el.textContent = `${count} activos`;
                } else {
                    el.textContent = count;
                }
            }
        });
    }
    
    startChatUpdates() {
        // Update chat every 10 seconds when chat tab is active
        this.chatTimer = setInterval(() => {
            if (this.currentTab === 'chat') {
                this.loadChat();
            }
        }, 10000);
    }
    
    showLoading() {
        this.isLoading = true;
        const spinner = document.getElementById('loadingSpinner');
        if (spinner) {
            spinner.classList.remove('d-none');
        }
    }
    
    hideLoading() {
        this.isLoading = false;
        const spinner = document.getElementById('loadingSpinner');
        if (spinner) {
            spinner.classList.add('d-none');
        }
    }
    
    showSuccess(message) {
        // Use existing toast system if available
        if (window.showToast) {
            window.showToast(message, 'success');
        } else {
            alert(message);
        }
    }
    
    showError(message) {
        // Use existing toast system if available
        if (window.showToast) {
            window.showToast(message, 'error');
        } else {
            alert(message);
        }
    }
}

function initCareerPage() {
    window.careerModule = new CareerModule();

    const tabs = document.querySelectorAll('.career-nav .nav-link');
    const contents = document.querySelectorAll('.tab-pane');

    tabs.forEach((tab) => {
        tab.addEventListener('click', (e) => {
            e.preventDefault();
            tabs.forEach((t) => t.classList.remove('active'));
            tab.classList.add('active');

            contents.forEach((c) => c.classList.add('d-none'));
            const target = document.getElementById(tab.dataset.tab);
            if (target) target.classList.remove('d-none');
        });
    });
}

window.initCareerPage = initCareerPage;
