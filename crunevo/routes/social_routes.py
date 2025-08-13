from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from crunevo.extensions import db
from crunevo.models.user import User
from crunevo.models.forum import ForumQuestion, ForumAnswer
from crunevo.models.social import (
    Mentorship, StudyGroup, StudyGroupMember, Competition, 
    CompetitionParticipant, Challenge, UserChallenge,
    MentorshipStatus, CompetitionStatus, ChallengeStatus
)
from crunevo.services.crolars_integration import CrolarsIntegrationService
from sqlalchemy import desc, func, and_

social_bp = Blueprint("social", __name__)


# ===== MENTORSHIP SYSTEM =====

@social_bp.route("/mentoria")
@login_required
def mentorship_dashboard():
    """Mentorship dashboard"""
    # Get available mentors (users with level >= 10 who are active mentors)
    mentors = User.query.filter(
        User.forum_level >= 5,
        User.reputation_score >= 100,
        User.id != current_user.id
    ).order_by(User.reputation_score.desc()).limit(20).all()
    
    # Get pending mentorship requests for current user
    my_requests = Mentorship.query.filter_by(
        student_id=current_user.id,
        status=MentorshipStatus.PENDING
    ).all()
    
    # Get active mentorships as student
    my_mentorships = Mentorship.query.filter_by(
        student_id=current_user.id,
        status=MentorshipStatus.ACTIVE
    ).all()
    
    # If user can be mentor, get their mentorship requests
    mentor_requests = []
    if current_user.forum_level >= 5:
        mentor_requests = Mentorship.query.filter_by(
            mentor_id=current_user.id,
            status=MentorshipStatus.PENDING
        ).all()
    
    return render_template(
        "social/mentorship_dashboard.html",
        available_mentors=mentors,
        my_requests=my_requests,
        my_mentorships=my_mentorships,
        mentor_requests=mentor_requests,
        can_be_mentor=current_user.forum_level >= 5
    )


@social_bp.route("/mentoria/solicitar/<int:mentor_id>", methods=["POST"])
@login_required
def request_mentorship(mentor_id):
    """Request mentorship"""
    mentor = User.query.get_or_404(mentor_id)
    
    # Check if mentor is eligible
    if mentor.forum_level < 5:
        flash("Este usuario no puede ser mentor", "error")
        return redirect(url_for("social.mentorship_dashboard"))
    
    if mentor.id == current_user.id:
        flash("No puedes solicitarte mentoría a ti mismo.", "error")
        return redirect(url_for("social.mentorship_dashboard"))
    
    # Check if already has pending/active mentorship with this mentor
    existing_mentorship = Mentorship.query.filter_by(
        student_id=current_user.id,
        mentor_id=mentor_id
    ).filter(
        Mentorship.status.in_([MentorshipStatus.PENDING, MentorshipStatus.ACTIVE])
    ).first()
    
    if existing_mentorship:
        flash("Ya tienes una mentoría activa o pendiente con este mentor", "warning")
        return redirect(url_for("social.mentorship_dashboard"))
    
    subject = request.form.get("subject", "")
    message = request.form.get("message", "")
    
    # Create mentorship request
    mentorship = Mentorship(
        student_id=current_user.id,
        mentor_id=mentor_id,
        subject=subject,
        message=message,
        status=MentorshipStatus.PENDING
    )
    db.session.add(mentorship)
    
    # Award credits for seeking help
    CrolarsIntegrationService.award_crolars(current_user.id, "seeking_help", 5)
    
    db.session.commit()
    flash(f"Tu solicitud de mentoría ha sido enviada a {mentor.username}", "success")
    return redirect(url_for("social.mentorship_dashboard"))


# ===== STUDY GROUPS =====

@social_bp.route("/grupos-estudio")
@login_required
def study_groups():
    """Display available study groups"""
    study_groups = StudyGroup.query.filter_by(is_active=True).all()
    my_groups = StudyGroupMember.query.filter_by(
        user_id=current_user.id, is_active=True
    ).all()
    
    return render_template(
        "social/study_groups.html",
        study_groups=study_groups,
        my_groups=my_groups
    )


@social_bp.route("/grupos-estudio/crear", methods=["POST"])
@login_required
def create_study_group():
    """Create a new study group"""
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    subject = request.form.get("subject", "").strip()
    max_members = int(request.form.get("max_members", 10))
    
    if not name or not subject:
        flash("Nombre y materia son requeridos", "error")
        return redirect(url_for("social.study_groups"))
    
    # Create study group
    group = StudyGroup(
        name=name,
        description=description,
        subject=subject,
        max_members=max_members,
        creator_id=current_user.id
    )
    db.session.add(group)
    db.session.flush()  # Get the group ID
    
    # Add creator as first member
    member = StudyGroupMember(
        group_id=group.id,
        user_id=current_user.id
    )
    db.session.add(member)
    
    # Award Crolars for creating group
    CrolarsIntegrationService.award_crolars(current_user.id, "create_group", 25)
    
    db.session.commit()
    flash(f"Grupo '{name}' creado exitosamente", "success")
    return redirect(url_for("social.study_groups"))


@social_bp.route("/grupos-estudio/<int:group_id>/unirse", methods=["POST"])
@login_required
def join_study_group(group_id):
    """Join a study group"""
    group = StudyGroup.query.get_or_404(group_id)
    
    # Check if already a member
    existing_member = StudyGroupMember.query.filter_by(
        group_id=group_id, user_id=current_user.id, is_active=True
    ).first()
    
    if existing_member:
        flash("Ya eres miembro de este grupo", "warning")
        return redirect(url_for("social.study_groups"))
    
    # Check if group is full
    current_members = StudyGroupMember.query.filter_by(
        group_id=group_id, is_active=True
    ).count()
    
    if current_members >= group.max_members:
        flash("Este grupo está lleno", "error")
        return redirect(url_for("social.study_groups"))
    
    # Add member
    member = StudyGroupMember(
        group_id=group_id,
        user_id=current_user.id
    )
    db.session.add(member)
    
    # Award Crolars for joining
    CrolarsIntegrationService.award_crolars(current_user.id, "join_group", 10)
    
    db.session.commit()
    flash(f"Te has unido al grupo '{group.name}' exitosamente", "success")
    return redirect(url_for("social.study_groups"))


# ===== COMPETITIONS =====

@social_bp.route("/competencias")
@login_required
def competitions():
    """Display academic competitions"""
    now = datetime.utcnow()
    
    # Get upcoming and active competitions
    upcoming_competitions = Competition.query.filter(
        Competition.start_date > now
    ).order_by(Competition.start_date).all()
    
    active_competitions = Competition.query.filter(
        and_(
            Competition.start_date <= now,
            Competition.end_date >= now,
            Competition.status == CompetitionStatus.ACTIVE
        )
    ).all()
    
    # Get user's competitions
    my_competitions = CompetitionParticipant.query.filter_by(
        user_id=current_user.id
    ).all()
    
    return render_template(
        "social/competitions.html",
        upcoming_competitions=upcoming_competitions,
        active_competitions=active_competitions,
        my_competitions=my_competitions
    )


@social_bp.route("/competencias/<int:competition_id>/participar", methods=["POST"])
@login_required
def join_competition(competition_id):
    """Participate in a competition"""
    competition = Competition.query.get_or_404(competition_id)
    
    # Check if already participating
    existing_participant = CompetitionParticipant.query.filter_by(
        competition_id=competition_id,
        user_id=current_user.id
    ).first()
    
    if existing_participant:
        flash("Ya estás participando en esta competencia", "warning")
        return redirect(url_for("social.competitions"))
    
    # Check if competition is full
    if competition.max_participants:
        current_participants = CompetitionParticipant.query.filter_by(
            competition_id=competition_id
        ).count()
        
        if current_participants >= competition.max_participants:
            flash("Esta competencia está llena", "error")
            return redirect(url_for("social.competitions"))
    
    # Check if user has enough Crolars for entry fee
    if competition.entry_fee > 0:
        if current_user.credits < competition.entry_fee:
            flash(f"Necesitas {competition.entry_fee} Crolars para participar", "error")
            return redirect(url_for("social.competitions"))
        
        # Deduct entry fee
        current_user.credits -= competition.entry_fee
    
    # Add participant
    participant = CompetitionParticipant(
        competition_id=competition_id,
        user_id=current_user.id
    )
    db.session.add(participant)
    
    db.session.commit()
    flash(f"Te has inscrito en '{competition.title}' exitosamente", "success")
    return redirect(url_for("social.competitions"))


# ===== CHALLENGES =====

@social_bp.route("/desafios")
@login_required
def challenges():
    """Daily and weekly challenges page"""
    # Get active challenges and user progress
    active_challenges = CrolarsIntegrationService.get_active_challenges(current_user.id)
    
    # Separate daily and weekly challenges
    daily_challenges = [c for c in active_challenges if c['type'] == 'daily']
    weekly_challenges = [c for c in active_challenges if c['type'] == 'weekly']
    
    return render_template(
        "social/challenges.html",
        daily_challenges=daily_challenges,
        weekly_challenges=weekly_challenges
    )


@social_bp.route("/api/desafios/<int:challenge_id>/reclamar", methods=["POST"])
@login_required
def claim_challenge_reward(challenge_id):
    """Claim completed challenge reward"""
    try:
        result = CrolarsIntegrationService.claim_challenge_reward(current_user.id, challenge_id)
        
        if result['success']:
            return jsonify({
                "success": True,
                "message": f"¡Has ganado {result['reward']} Crolars!",
                "new_balance": current_user.credits
            })
        else:
            return jsonify({
                "success": False,
                "message": result['message']
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Error al reclamar la recompensa"
        }), 500


# ===== LEADERBOARDS =====

@social_bp.route("/clasificaciones")
@login_required
def leaderboards():
    """Leaderboards and rankings"""
    # Get level leaderboard
    level_leaderboard = User.query.filter(
        User.level > 0
    ).order_by(User.level.desc(), User.forum_experience.desc()).limit(10).all()
    
    # Get reputation leaderboard
    reputation_leaderboard = User.query.filter(
        User.reputation_score > 0
    ).order_by(User.reputation_score.desc()).limit(10).all()
    
    # Get helpful answers leaderboard
    helpful_answers_leaderboard = User.query.filter(
        User.helpful_answers_count > 0
    ).order_by(User.helpful_answers_count.desc()).limit(10).all()
    
    # Get Crolars leaderboard
    crolars_leaderboard = CrolarsIntegrationService.get_crolars_leaderboard(limit=10)
    
    # Get current user's positions
    user_level_rank = User.query.filter(
        User.level > current_user.level
    ).count() + 1
    
    user_reputation_rank = User.query.filter(
        User.reputation_score > current_user.reputation_score
    ).count() + 1
    
    user_helpful_rank = User.query.filter(
        User.helpful_answers_count > current_user.helpful_answers_count
    ).count() + 1
    
    user_crolars_rank = User.query.filter(
        User.credits > current_user.credits
    ).count() + 1
    
    return render_template(
        "social/leaderboards.html",
        level_leaderboard=level_leaderboard,
        reputation_leaderboard=reputation_leaderboard,
        helpful_answers_leaderboard=helpful_answers_leaderboard,
        crolars_leaderboard=crolars_leaderboard,
        user_level_rank=user_level_rank,
        user_reputation_rank=user_reputation_rank,
        user_helpful_rank=user_helpful_rank,
        user_crolars_rank=user_crolars_rank
    )


# ===== SOCIAL FEED =====

@social_bp.route("/feed")
@login_required
def social_feed():
    """Social feed with recent forum activities"""
    activities = []
    
    # Get recent questions (last 24 hours)
    recent_questions = ForumQuestion.query.filter(
        ForumQuestion.created_at >= datetime.utcnow() - timedelta(days=1)
    ).order_by(ForumQuestion.created_at.desc()).limit(10).all()
    
    for question in recent_questions:
        activities.append({
            "type": "new_question",
            "user": question.author,
            "content": {
                "title": question.title,
                "subject": question.subject or "General",
                "id": question.id
            },
            "timestamp": question.created_at
        })
    
    # Get recent answers (last 24 hours)
    recent_answers = ForumAnswer.query.filter(
        ForumAnswer.created_at >= datetime.utcnow() - timedelta(days=1)
    ).order_by(ForumAnswer.created_at.desc()).limit(10).all()
    
    for answer in recent_answers:
        activities.append({
            "type": "new_answer",
            "user": answer.author,
            "content": {
                "question_title": answer.question.title,
                "preview": answer.content[:100] + "..." if len(answer.content) > 100 else answer.content,
                "question_id": answer.question_id
            },
            "timestamp": answer.created_at
        })
    
    # Get recent accepted answers (last 7 days)
    accepted_answers = ForumAnswer.query.filter(
        ForumAnswer.is_accepted == True,
        ForumAnswer.updated_at >= datetime.utcnow() - timedelta(days=7)
    ).order_by(ForumAnswer.updated_at.desc()).limit(5).all()
    
    for answer in accepted_answers:
        activities.append({
            "type": "accepted_answer",
            "user": answer.author,
            "content": {
                "question_title": answer.question.title,
                "crolars_earned": 50,
                "question_id": answer.question_id
            },
            "timestamp": answer.updated_at
        })
    
    # Sort all activities by timestamp
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Limit to 20 most recent activities
    activities = activities[:20]
    
    return render_template("social/social_feed.html", activities=activities)


@social_bp.route("/crolars/estadisticas")
@login_required
def crolars_stats():
    """Crolars statistics page"""
    # Get user's Crolars statistics
    stats = CrolarsIntegrationService.get_user_crolars_stats(current_user.id)
    
    # Get Crolars leaderboard
    leaderboard = CrolarsIntegrationService.get_crolars_leaderboard(limit=10)
    
    return render_template(
        "social/crolars_stats.html",
        stats=stats,
        leaderboard=leaderboard
    )


@social_bp.route("/premium")
@login_required
def premium_features():
    """Premium features page"""
    feature = request.args.get('feature', 'boost')
    
    # Get premium costs
    from crunevo.services.crolars_integration import PREMIUM_COSTS
    
    return render_template(
        "social/premium_feature.html",
        feature=feature,
        costs=PREMIUM_COSTS,
        user_balance=current_user.credits
    )


@social_bp.route("/premium/comprar", methods=["POST"])
@login_required
def buy_premium_feature():
    """Buy premium feature"""
    feature_type = request.form.get('feature_type')
    
    if not feature_type:
        flash("Tipo de función premium no especificado", "error")
        return redirect(url_for("social.premium_features"))
    
    # Check if user can afford the feature
    can_afford = CrolarsIntegrationService.can_afford_premium_feature(
        current_user.id, feature_type
    )
    
    if not can_afford:
        flash("No tienes suficientes Crolars para esta función", "error")
        return redirect(url_for("social.premium_features"))
    
    # Handle custom title feature
    if feature_type == 'custom_title':
        custom_title = request.form.get('custom_title', '').strip()
        if not custom_title or len(custom_title) > 50:
            flash("El título personalizado debe tener entre 1 y 50 caracteres", "error")
            return redirect(url_for("social.premium_features", feature='title'))
        
        # Use the premium feature
        success = CrolarsIntegrationService.use_premium_feature(
            current_user.id, feature_type, custom_title=custom_title
        )
        
        if success:
            # Update user's custom title
            current_user.custom_forum_title = custom_title
            db.session.commit()
            flash(f"Título personalizado '{custom_title}' activado exitosamente", "success")
        else:
            flash("Error al activar el título personalizado", "error")
    
    else:
        # For other premium features (boost, highlight)
        question_id = request.form.get('question_id')
        answer_id = request.form.get('answer_id')
        
        success = CrolarsIntegrationService.use_premium_feature(
            current_user.id, feature_type, 
            question_id=question_id, answer_id=answer_id
        )
        
        if success:
            feature_names = {
                'boost_question': 'impulso de pregunta',
                'highlight_answer': 'destacado de respuesta'
            }
            flash(f"Función de {feature_names.get(feature_type, feature_type)} activada exitosamente", "success")
        else:
            flash("Error al activar la función premium", "error")
    
    return redirect(url_for("social.premium_features"))