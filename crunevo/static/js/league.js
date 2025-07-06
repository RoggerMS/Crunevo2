
// League functionality
class LeagueManager {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadRanking();
    }

    bindEvents() {
        // Join team button
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="join-team"]')) {
                const teamId = e.target.dataset.teamId;
                this.joinTeam(teamId);
            }
        });

        // Leave team button
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="leave-team"]')) {
                this.leaveTeam();
            }
        });

        // Tab changes
        document.querySelectorAll('#leagueTabs button').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const target = e.target.dataset.bsTarget;
                if (target === '#teams') {
                    this.loadTeams();
                }
            });
        });
    }

    async loadRanking() {
        try {
            const response = await fetch('/liga/api/ranking');
            const data = await response.json();
            this.updateRankingDisplay(data.ranking);
        } catch (error) {
            console.error('Error loading ranking:', error);
        }
    }

    updateRankingDisplay(ranking) {
        const container = document.getElementById('ranking-list');
        if (!container) return;

        container.innerHTML = ranking.map((team, index) => {
            const position = index + 1;
            const isPodium = position <= 3;
            const podiumClass = isPodium ? `podium-${position}` : '';

            let positionIcon = '';
            if (position === 1) {
                positionIcon = '<i class="bi bi-trophy text-warning"></i>';
            } else if (position === 2) {
                positionIcon = '<i class="bi bi-award text-secondary"></i>';
            } else if (position === 3) {
                positionIcon = '<i class="bi bi-award text-danger"></i>';
            }

            return `
                <div class="ranking-item ${podiumClass}">
                    <div class="position-badge">
                        ${positionIcon}
                        <span class="position">${position}</span>
                    </div>
                    <img src="${team.avatar_url}" alt="Avatar" class="team-avatar">
                    <div class="team-info">
                        <h6 class="team-name">${team.name}</h6>
                        <small class="text-muted">${team.member_count} miembros</small>
                    </div>
                    <div class="team-points">
                        <span class="points">${team.points}</span>
                        <small>puntos</small>
                    </div>
                </div>
            `;
        }).join('');
    }

    async loadTeams() {
        try {
            const response = await fetch('/liga/api/equipos');
            const data = await response.json();
            this.updateTeamsDisplay(data.teams);
        } catch (error) {
            console.error('Error loading teams:', error);
        }
    }

    updateTeamsDisplay(teams) {
        const container = document.getElementById('teams-grid');
        if (!container) return;

        container.innerHTML = teams.map(team => `
            <div class="col-lg-6 col-xl-4 mb-4">
                <div class="card team-card h-100">
                    <div class="card-body">
                        <div class="d-flex align-items-center mb-3">
                            <img src="${team.avatar_url}" alt="Avatar" class="team-avatar me-3">
                            <div>
                                <h6 class="mb-1">${team.name}</h6>
                                <small class="text-muted">Capitán: ${team.captain}</small>
                            </div>
                        </div>
                        <p class="text-muted small">${team.description || 'Sin descripción'}</p>
                        <div class="team-stats d-flex justify-content-between">
                            <span><i class="bi bi-people text-primary"></i> ${team.member_count}/5</span>
                            <span><i class="bi bi-trophy text-warning"></i> ${team.points}</span>
                        </div>
                        <div class="mt-3">
                            <a href="/liga/equipo/${team.id}" class="btn btn-outline-primary btn-sm w-100">
                                Ver Detalles
                            </a>
                            ${team.can_join ? `
                                <button class="btn btn-primary btn-sm w-100 mt-2" 
                                        data-action="join-team" data-team-id="${team.id}">
                                    Unirse al Equipo
                                </button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    async joinTeam(teamId) {
        try {
            const response = await csrfFetch(`/liga/unirse/${teamId}`, {
                method: 'POST'
            });

            const data = await response.json();

            if (data.success) {
                showNotification(data.message, 'success');
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                showNotification(data.error, 'error');
            }
        } catch (error) {
            console.error('Error joining team:', error);
            showNotification('Error al unirse al equipo', 'error');
        }
    }

    async leaveTeam() {
        if (!confirm('¿Estás seguro de que quieres salir del equipo?')) {
            return;
        }

        try {
            const response = await csrfFetch('/liga/salir-equipo', {
                method: 'POST'
            });

            const data = await response.json();

            if (data.success) {
                showNotification(data.message, 'success');
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                showNotification(data.error, 'error');
            }
        } catch (error) {
            console.error('Error leaving team:', error);
            showNotification('Error al salir del equipo', 'error');
        }
    }
}

// Team creation form
class TeamCreationForm {
    constructor() {
        this.form = document.getElementById('createTeamForm');
        if (this.form) {
            this.bindEvents();
        }
    }

    bindEvents() {
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitForm();
        });

        // Team name validation
        const nameInput = this.form.querySelector('[name="name"]');
        if (nameInput) {
            nameInput.addEventListener('input', () => {
                this.validateTeamName(nameInput.value);
            });
        }
    }

    async validateTeamName(name) {
        if (name.length < 3) {
            this.showFieldError('name', 'El nombre debe tener al menos 3 caracteres');
            return false;
        }

        try {
            const response = await fetch(`/liga/api/validar-nombre?name=${encodeURIComponent(name)}`);
            const data = await response.json();

            if (!data.available) {
                this.showFieldError('name', 'Este nombre ya está en uso');
                return false;
            }

            this.clearFieldError('name');
            return true;
        } catch (error) {
            console.error('Error validating name:', error);
            return false;
        }
    }

    showFieldError(fieldName, message) {
        const field = this.form.querySelector(`[name="${fieldName}"]`);
        const errorElement = field.parentElement.querySelector('.field-error');
        
        if (errorElement) {
            errorElement.textContent = message;
        } else {
            const error = document.createElement('div');
            error.className = 'field-error text-danger small mt-1';
            error.textContent = message;
            field.parentElement.appendChild(error);
        }

        field.classList.add('is-invalid');
    }

    clearFieldError(fieldName) {
        const field = this.form.querySelector(`[name="${fieldName}"]`);
        const errorElement = field.parentElement.querySelector('.field-error');
        
        if (errorElement) {
            errorElement.remove();
        }

        field.classList.remove('is-invalid');
    }

    async submitForm() {
        const formData = new FormData(this.form);
        
        // Validate team name
        const isValid = await this.validateTeamName(formData.get('name'));
        if (!isValid) {
            return;
        }

        try {
            const response = await csrfFetch('/liga/crear-equipo', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                showNotification('Equipo creado exitosamente', 'success');
                setTimeout(() => {
                    window.location.href = '/liga';
                }, 1500);
            } else {
                const data = await response.json();
                showNotification(data.error || 'Error al crear equipo', 'error');
            }
        } catch (error) {
            console.error('Error creating team:', error);
            showNotification('Error al crear equipo', 'error');
        }
    }
}

// Initialize league features
document.addEventListener('DOMContentLoaded', function() {
    new LeagueManager();
    new TeamCreationForm();
});

// Utility functions
function showNotification(message, type = 'info') {
    // Use existing CRUNEVO notification system
    if (window.CRUNEVO_UI && window.CRUNEVO_UI.showSuccessToast) {
        if (type === 'success') {
            window.CRUNEVO_UI.showSuccessToast(message);
        } else if (type === 'error') {
            window.CRUNEVO_UI.showErrorToast(message);
        }
        return;
    }

    // Fallback notification
    const toast = document.createElement('div');
    toast.className = `toast-notification ${type}`;
    toast.innerHTML = `
        <div class="toast-body d-flex align-items-center">
            <i class="bi bi-${getToastIcon(type)} me-2"></i>
            <span class="flex-grow-1">${message}</span>
            <button type="button" class="btn-close btn-sm ms-2" onclick="this.parentElement.parentElement.remove()"></button>
        </div>
    `;

    const container = document.querySelector('.toast-container') || createToastContainer();
    container.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 5000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '1060';
    document.body.appendChild(container);
    return container;
}

function getToastIcon(type) {
    const icons = {
        success: 'check-circle',
        error: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    return icons[type] || 'info-circle';
}
