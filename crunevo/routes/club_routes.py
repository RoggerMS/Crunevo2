
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from crunevo.extensions import db
from crunevo.models.club import Club, ClubMember
from crunevo.utils.credits import add_credit
from crunevo.constants.credit_reasons import CreditReasons

club_bp = Blueprint('club', __name__)


@club_bp.route('/clubes')
def list_clubs():
    clubs = Club.query.all()
    user_clubs = []
    if current_user.is_authenticated:
        user_clubs = [cm.club_id for cm in ClubMember.query.filter_by(user_id=current_user.id).all()]
    
    return render_template('club/list.html', clubs=clubs, user_clubs=user_clubs)


@club_bp.route('/club/<int:club_id>')
def view_club(club_id):
    club = Club.query.get_or_404(club_id)
    is_member = False
    if current_user.is_authenticated:
        is_member = ClubMember.query.filter_by(user_id=current_user.id, club_id=club_id).first() is not None
    
    # Get club posts
    from crunevo.models.club_post import ClubPost
    posts = ClubPost.query.filter_by(club_id=club_id).order_by(ClubPost.created_at.desc()).limit(20).all()
    
    members = ClubMember.query.filter_by(club_id=club_id).limit(10).all()
    return render_template('club/detail.html', club=club, is_member=is_member, members=members, posts=posts)


@club_bp.route('/club/<int:club_id>/post', methods=['POST'])
@login_required
def create_club_post(club_id):
    club = Club.query.get_or_404(club_id)
    
    # Check if user is a member
    membership = ClubMember.query.filter_by(user_id=current_user.id, club_id=club_id).first()
    if not membership:
        flash('Debes ser miembro del club para publicar', 'error')
        return redirect(url_for('club.view_club', club_id=club_id))
    
    content = request.form.get('content')
    if not content or len(content.strip()) < 5:
        flash('El contenido debe tener al menos 5 caracteres', 'error')
        return redirect(url_for('club.view_club', club_id=club_id))
    
    from crunevo.models.club_post import ClubPost
    post = ClubPost(
        club_id=club_id,
        author_id=current_user.id,
        content=content.strip()
    )
    
    db.session.add(post)
    db.session.commit()
    
    # Award credits
    add_credit(current_user, 1, CreditReasons.ACTIVIDAD_SOCIAL, related_id=post.id)
    
    flash('¡Publicación creada en el club!')
    return redirect(url_for('club.view_club', club_id=club_id))


@club_bp.route('/club/<int:club_id>/join', methods=['POST'])
@login_required
def join_club(club_id):
    club = Club.query.get_or_404(club_id)
    
    # Check if already a member
    existing = ClubMember.query.filter_by(user_id=current_user.id, club_id=club_id).first()
    if existing:
        return jsonify({'error': 'Ya eres miembro de este club'}), 400
    
    # Join club
    membership = ClubMember(user_id=current_user.id, club_id=club_id)
    db.session.add(membership)
    
    # Update member count
    club.member_count += 1
    db.session.commit()
    
    # Award credits
    add_credit(current_user, 2, CreditReasons.ACTIVIDAD_SOCIAL, related_id=club_id)
    
    flash(f'¡Te has unido al club {club.name}!')
    return jsonify({'success': True, 'member_count': club.member_count})


@club_bp.route('/club/<int:club_id>/leave', methods=['POST'])
@login_required
def leave_club(club_id):
    club = Club.query.get_or_404(club_id)
    membership = ClubMember.query.filter_by(user_id=current_user.id, club_id=club_id).first()
    
    if not membership:
        return jsonify({'error': 'No eres miembro de este club'}), 400
    
    db.session.delete(membership)
    club.member_count -= 1
    db.session.commit()
    
    flash(f'Has dejado el club {club.name}')
    return jsonify({'success': True, 'member_count': club.member_count})
