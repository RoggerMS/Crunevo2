from datetime import date
from crunevo.extensions import db
from crunevo.models.user import User
from crunevo.models.badge import ForumBadge, UserBadge
from crunevo.services.crolars_integration import CrolarsIntegrationService
from flask import flash


class GamificationService:
    """Service for managing forum gamification system."""

    # Experience points for different actions
    EXPERIENCE_POINTS = {
        "ask_question": 5,
        "answer_question": 10,
        "best_answer": 25,
        "receive_vote": 2,
        "daily_activity": 5,
        "first_question": 10,
        "first_answer": 15,
    }

    @staticmethod
    def award_experience(user, action, amount=None):
        """Award experience points to user for an action."""
        if amount is None:
            amount = GamificationService.EXPERIENCE_POINTS.get(action, 0)

        if amount > 0:
            level_up = user.add_forum_experience(amount)
            db.session.commit()

            if level_up:
                flash(
                    f"¡Felicidades! Has subido al nivel {user.forum_level}: {user.get_forum_rank()}!",
                    "success",
                )

            # Check for new badges
            GamificationService.check_and_award_badges(user)

            return level_up
        return False

    @staticmethod
    def update_user_stats(user, action):
        """Update user statistics based on action."""
        if action == "ask_question":
            user.questions_asked += 1
        elif action == "answer_question":
            user.answers_given += 1
        elif action == "best_answer":
            user.best_answers += 1
        elif action == "receive_vote":
            user.helpful_votes += 1

        # Update daily streak
        today = date.today()
        if user.last_activity_date != today:
            if user.last_activity_date == date.today().replace(day=today.day - 1):
                user.forum_streak += 1
            else:
                user.forum_streak = 1
            user.last_activity_date = today

        db.session.commit()

    @staticmethod
    def check_and_award_badges(user):
        """Check if user qualifies for new badges and award them."""
        badges = ForumBadge.query.filter_by(is_active=True).all()
        awarded_badges = []

        for badge in badges:
            # Check if user already has this badge
            existing = UserBadge.query.filter_by(
                user_id=user.id, badge_id=badge.id
            ).first()

            if existing:
                continue

            # Check if user meets requirements
            if GamificationService._meets_requirements(user, badge.requirements):
                user_badge = UserBadge(user_id=user.id, badge_id=badge.id)
                db.session.add(user_badge)

                # Award experience points for badge
                if badge.points_reward > 0:
                    user.add_forum_experience(badge.points_reward)

                awarded_badges.append(badge)

        if awarded_badges:
            db.session.commit()
            for badge in awarded_badges:
                flash(f"¡Nueva insignia desbloqueada: {badge.name}!", "badge")

        return awarded_badges

    @staticmethod
    def _meets_requirements(user, requirements):
        """Check if user meets badge requirements."""
        if not requirements:
            return False

        for req_key, req_value in requirements.items():
            user_value = getattr(user, req_key, 0)
            if user_value < req_value:
                return False

        return True

    @staticmethod
    def get_user_badges(user, limit=None):
        """Get user's badges, optionally limited."""
        query = UserBadge.query.filter_by(user_id=user.id).join(ForumBadge)

        if limit:
            query = query.limit(limit)

        return query.all()

    @staticmethod
    def get_leaderboard(limit=10):
        """Get forum leaderboard based on reputation score."""
        return (
            User.query.filter(User.reputation_score > 0)
            .order_by(
                User.reputation_score.desc(),
                User.forum_level.desc(),
                User.forum_experience.desc(),
            )
            .limit(limit)
            .all()
        )

    @staticmethod
    def calculate_reputation(user):
        """Calculate and update user's reputation score."""
        # Base reputation calculation
        reputation = (
            user.best_answers * 10
            + user.helpful_votes * 2
            + user.answers_given * 1
            + user.forum_level * 5
        )

        # Bonus for badges
        user_badges = GamificationService.get_user_badges(user)
        badge_bonus = sum(ub.badge.points_reward for ub in user_badges) // 10

        user.reputation_score = reputation + badge_bonus
        db.session.commit()

        return user.reputation_score

    @staticmethod
    def initialize_default_badges():
        """Initialize default badges in the database."""
        default_badges = ForumBadge.get_default_badges()

        for badge_data in default_badges:
            existing = ForumBadge.query.filter_by(name=badge_data["name"]).first()
            if not existing:
                badge = ForumBadge(**badge_data)
                db.session.add(badge)

        db.session.commit()

    @staticmethod
    def process_question_action(user, is_first=False, question=None):
        """Process gamification for asking a question."""
        GamificationService.update_user_stats(user, "ask_question")

        if is_first:
            GamificationService.award_experience(user, "first_question")
            CrolarsIntegrationService.award_crolars_for_action(user, "first_question")
        else:
            GamificationService.award_experience(user, "ask_question")
            # Award Crolars based on question quality
            if question:
                crolars_amount = CrolarsIntegrationService.calculate_question_reward(
                    question
                )
                CrolarsIntegrationService.award_crolars_for_action(
                    user, "ask_question", crolars_amount
                )
            else:
                CrolarsIntegrationService.award_crolars_for_action(user, "ask_question")

    @staticmethod
    def process_answer_action(user, is_first=False, answer=None):
        """Process gamification for giving an answer."""
        GamificationService.update_user_stats(user, "answer_question")

        if is_first:
            GamificationService.award_experience(user, "first_answer")
            CrolarsIntegrationService.award_crolars_for_action(user, "first_answer")
        else:
            GamificationService.award_experience(user, "answer_question")
            # Award Crolars based on answer quality
            if answer:
                crolars_amount = CrolarsIntegrationService.calculate_answer_reward(
                    answer
                )
                CrolarsIntegrationService.award_crolars_for_action(
                    user, "answer_question", crolars_amount
                )
            else:
                CrolarsIntegrationService.award_crolars_for_action(
                    user, "answer_question"
                )

    @staticmethod
    def process_best_answer(user, answer=None):
        """Process gamification for getting best answer."""
        GamificationService.update_user_stats(user, "best_answer")
        GamificationService.award_experience(user, "best_answer")

        # Award Crolars for best answer
        if answer:
            crolars_amount = CrolarsIntegrationService.calculate_answer_reward(
                answer, is_best=True
            )
            CrolarsIntegrationService.award_crolars_for_action(
                user, "best_answer", crolars_amount
            )
        else:
            CrolarsIntegrationService.award_crolars_for_action(user, "best_answer")

    @staticmethod
    def process_vote(user):
        """Process gamification for receiving a vote."""
        GamificationService.update_user_stats(user, "receive_vote")
        GamificationService.award_experience(user, "receive_vote")

        # Award Crolars for receiving votes
        CrolarsIntegrationService.award_crolars_for_action(user, "receive_vote")

        # Check for daily activity bonus
        CrolarsIntegrationService.process_daily_activity_bonus(user)

        # Check for weekly participation bonus
        CrolarsIntegrationService.check_weekly_participation_bonus(user)
