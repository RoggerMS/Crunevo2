
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from crunevo.extensions import db
from crunevo.models.league import AcademicTeam, TeamMember, LeagueMonth, TeamAction
from crunevo.models.user import User
from crunevo.utils.helpers import activated_required
from datetime import datetime, timedelta
from sqlalchemy import desc, func

league_bp = Blueprint('league', __name__, url_prefix='/liga')


@league_bp.route('/')
@login_required
@activated_required
def index():
    """Academic League main page"""
    current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Get current user's team
    user_team = None
    user_membership = TeamMember.query.filter_by(
        user_id=current_user.id, 
        is_active=True
    ).first()
    
    if user_membership:
        user_team = user_membership.team
    
    # Get top teams this month
    top_teams = AcademicTeam.query.filter_by(is_active=True).order_by(
        desc(AcademicTeam.points)
    ).limit(10).all()
    
    # Get league stats
    total_teams = AcademicTeam.query.filter_by(is_active=True).count()
    total_participants = TeamMember.query.filter_by(is_active=True).count()
    
    # Get current month league
    current_league = LeagueMonth.query.filter(
        LeagueMonth.start_date <= datetime.now(),
        LeagueMonth.end_date >= datetime.now()
    ).first()
    
    return render_template('league/index.html',
                         user_team=user_team,
                         top_teams=top_teams,
                         total_teams=total_teams,
                         total_participants=total_participants,
                         current_league=current_league)


@league_bp.route('/crear-equipo', methods=['GET', 'POST'])
@login_required
@activated_required
def create_team():
    """Create new academic team"""
    if request.method == 'POST':
        # Check if user is already in a team
        existing_membership = TeamMember.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).first()
        
        if existing_membership:
            flash('Ya perteneces a un equipo activo', 'warning')
            return redirect(url_for('league.index'))
        
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        if not name or len(name) < 3:
            flash('El nombre del equipo debe tener al menos 3 caracteres', 'error')
            return redirect(url_for('league.create_team'))
        
        # Check if team name exists
        existing_team = AcademicTeam.query.filter_by(name=name).first()
        if existing_team:
            flash('Ya existe un equipo con ese nombre', 'error')
            return redirect(url_for('league.create_team'))
        
        # Create team
        team = AcademicTeam(
            name=name,
            description=description,
            captain_id=current_user.id
        )
        
        db.session.add(team)
        db.session.flush()
        
        # Add captain as member
        member = TeamMember(
            team_id=team.id,
            user_id=current_user.id
        )
        
        db.session.add(member)
        db.session.commit()
        
        flash('¡Equipo creado exitosamente!', 'success')
        return redirect(url_for('league.team_detail', team_id=team.id))
    
    return render_template('league/create_team.html')


@league_bp.route('/equipo/<int:team_id>')
@login_required
@activated_required
def team_detail(team_id):
    """Team detail page"""
    team = AcademicTeam.query.get_or_404(team_id)
    members = team.members.filter_by(is_active=True).all()
    
    # Check if current user can join
    can_join = False
    user_membership = TeamMember.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).first()
    
    if not user_membership and team.can_accept_members:
        can_join = True
    
    # Get recent team actions
    recent_actions = TeamAction.query.filter_by(team_id=team_id).order_by(
        desc(TeamAction.created_at)
    ).limit(10).all()
    
    return render_template('league/team_detail.html',
                         team=team,
                         members=members,
                         can_join=can_join,
                         recent_actions=recent_actions)


@league_bp.route('/unirse/<int:team_id>', methods=['POST'])
@login_required
@activated_required
def join_team(team_id):
    """Join a team"""
    team = AcademicTeam.query.get_or_404(team_id)
    
    # Check if user is already in a team
    existing_membership = TeamMember.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).first()
    
    if existing_membership:
        return jsonify({'error': 'Ya perteneces a un equipo'}), 400
    
    # Check if team has space
    if not team.can_accept_members:
        return jsonify({'error': 'El equipo está completo'}), 400
    
    # Join team
    member = TeamMember(
        team_id=team_id,
        user_id=current_user.id
    )
    
    db.session.add(member)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '¡Te has unido al equipo!'})


@league_bp.route('/salir-equipo', methods=['POST'])
@login_required
def leave_team():
    """Leave current team"""
    membership = TeamMember.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).first()
    
    if not membership:
        return jsonify({'error': 'No perteneces a ningún equipo'}), 400
    
    team = membership.team
    
    # If user is captain and there are other members, transfer captaincy
    if team.captain_id == current_user.id and team.member_count > 1:
        other_member = team.members.filter(
            TeamMember.user_id != current_user.id,
            TeamMember.is_active == True
        ).first()
        
        if other_member:
            team.captain_id = other_member.user_id
    
    # Deactivate membership
    membership.is_active = False
    
    # If no members left, deactivate team
    if team.member_count <= 1:
        team.is_active = False
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Has salido del equipo'})


@league_bp.route('/api/ranking')
@login_required
def get_ranking():
    """Get current month ranking"""
    teams = AcademicTeam.query.filter_by(is_active=True).order_by(
        desc(AcademicTeam.points)
    ).limit(50).all()
    
    ranking_data = []
    for i, team in enumerate(teams, 1):
        ranking_data.append({
            'position': i,
            'id': team.id,
            'name': team.name,
            'points': team.points,
            'member_count': team.member_count,
            'avatar_url': team.avatar_url,
            'captain': team.captain.username
        })
    
    return jsonify({'ranking': ranking_data})


def award_team_points(user_id, action_type, points):
    """Award points to user's team for actions"""
    membership = TeamMember.query.filter_by(
        user_id=user_id,
        is_active=True
    ).first()
    
    if not membership:
        return
    
    # Record action
    action = TeamAction(
        team_id=membership.team_id,
        user_id=user_id,
        action_type=action_type,
        points_earned=points
    )
    
    # Update team points
    membership.team.points += points
    membership.points_contributed += points
    
    db.session.add(action)
    db.session.commit()
