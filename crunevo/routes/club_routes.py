
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
    
    members = ClubMember.query.filter_by(club_id=club_id).limit(10).all()
    return render_template('club/detail.html', club=club, is_member=is_member, members=members)


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
