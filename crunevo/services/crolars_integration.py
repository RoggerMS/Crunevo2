from datetime import datetime, timedelta
from sqlalchemy import func, desc
from crunevo.extensions import db
from crunevo.models.user import User
from crunevo.models.forum import ForumQuestion, ForumAnswer
from crunevo.models.social import Competition, Challenge, UserChallenge
from typing import Dict, List, Optional


class CrolarsIntegrationService:
    """Service for integrating Crolars rewards with forum activities"""
    
    # Premium feature costs in Crolars
    PREMIUM_COSTS = {
        'boost_question': 100,
        'highlight_answer': 75,
        'custom_title': 200
    }
    
    # Crolars rewards for different activities
    ACTIVITY_REWARDS = {
        'ask_question': 10,
        'answer_question': 15,
        'best_answer': 50,
        'helpful_vote': 5,
        'question_solved': 25,
        'daily_login': 5,
        'complete_challenge': 100
    }
    
    @staticmethod
    def get_user_crolars_stats(user_id: int) -> Dict:
        """Get comprehensive Crolars statistics for a user"""
        user = User.query.get(user_id)
        if not user:
            return {}
        
        # Calculate earnings over different periods
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        # Get forum activity stats
        questions_count = ForumQuestion.query.filter_by(author_id=user_id).count()
        answers_count = ForumAnswer.query.filter_by(author_id=user_id).count()
        best_answers_count = ForumAnswer.query.filter_by(
            author_id=user_id, is_accepted=True
        ).count()
        helpful_votes = db.session.query(func.sum(ForumAnswer.helpful_count)).filter_by(
            author_id=user_id
        ).scalar() or 0
        
        # Calculate estimated Crolars earned from forum activities
        estimated_forum_crolars = (
            questions_count * CrolarsIntegrationService.ACTIVITY_REWARDS['ask_question'] +
            answers_count * CrolarsIntegrationService.ACTIVITY_REWARDS['answer_question'] +
            best_answers_count * CrolarsIntegrationService.ACTIVITY_REWARDS['best_answer'] +
            helpful_votes * CrolarsIntegrationService.ACTIVITY_REWARDS['helpful_vote']
        )
        
        return {
            'total_crolars': user.credits,  # Assuming credits are Crolars
            'crolars_7_days': estimated_forum_crolars // 4,  # Rough estimate
            'crolars_30_days': estimated_forum_crolars // 2,  # Rough estimate
            'questions_asked': questions_count,
            'answers_given': answers_count,
            'best_answers': best_answers_count,
            'helpful_votes': helpful_votes,
            'forum_level': user.forum_level,
            'reputation': user.reputation_score
        }
    
    @staticmethod
    def get_crolars_leaderboard(limit: int = 10) -> List[Dict]:
        """Get top users by Crolars earnings"""
        users = User.query.order_by(desc(User.credits)).limit(limit).all()
        
        leaderboard = []
        for i, user in enumerate(users, 1):
            # Calculate total estimated Crolars from forum activities
            questions_count = ForumQuestion.query.filter_by(author_id=user.id).count()
            answers_count = ForumAnswer.query.filter_by(author_id=user.id).count()
            best_answers_count = ForumAnswer.query.filter_by(
                author_id=user.id, is_accepted=True
            ).count()
            
            estimated_earned = (
                questions_count * CrolarsIntegrationService.ACTIVITY_REWARDS['ask_question'] +
                answers_count * CrolarsIntegrationService.ACTIVITY_REWARDS['answer_question'] +
                best_answers_count * CrolarsIntegrationService.ACTIVITY_REWARDS['best_answer']
            )
            
            leaderboard.append({
                'rank': i,
                'user': user,
                'total_crolars': user.credits,
                'estimated_earned': estimated_earned
            })
        
        return leaderboard
    
    @staticmethod
    def can_afford_premium_feature(user_id: int, feature: str) -> bool:
        """Check if user can afford a premium feature"""
        user = User.query.get(user_id)
        if not user:
            return False
        
        cost = CrolarsIntegrationService.PREMIUM_COSTS.get(feature, 0)
        return user.credits >= cost
    
    @staticmethod
    def use_premium_feature(user_id: int, feature: str, **kwargs) -> Dict:
        """Use a premium feature and deduct Crolars"""
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'error': 'Usuario no encontrado'}
        
        cost = CrolarsIntegrationService.PREMIUM_COSTS.get(feature, 0)
        if user.credits < cost:
            return {'success': False, 'error': 'Crolars insuficientes'}
        
        try:
            if feature == 'boost_question':
                question_id = kwargs.get('question_id')
                question = ForumQuestion.query.get(question_id)
                if question and question.author_id == user_id:
                    question.is_boosted = True
                    question.boost_expires = datetime.utcnow() + timedelta(days=7)
                    
            elif feature == 'highlight_answer':
                answer_id = kwargs.get('answer_id')
                answer = ForumAnswer.query.get(answer_id)
                if answer and answer.author_id == user_id:
                    answer.is_highlighted = True
                    answer.highlight_expires = datetime.utcnow() + timedelta(days=3)
                    
            elif feature == 'custom_title':
                custom_title = kwargs.get('custom_title', '').strip()
                if len(custom_title) <= 50:
                    user.custom_forum_title = custom_title
            
            # Deduct Crolars
            user.credits -= cost
            db.session.commit()
            
            return {
                'success': True, 
                'remaining_crolars': user.credits,
                'feature_used': feature,
                'cost': cost
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'Error al procesar: {str(e)}'}
    
    @staticmethod
    def award_crolars(user_id: int, activity: str, amount: Optional[int] = None) -> bool:
        """Award Crolars for forum activities"""
        user = User.query.get(user_id)
        if not user:
            return False
        
        if amount is None:
            amount = CrolarsIntegrationService.ACTIVITY_REWARDS.get(activity, 0)
        
        if amount > 0:
            user.credits += amount
            try:
                db.session.commit()
                return True
            except Exception:
                db.session.rollback()
                return False
        
        return False
    
    @staticmethod
    def get_active_challenges(user_id: int) -> List[Dict]:
        """Get active challenges for a user"""
        now = datetime.utcnow()
        
        # Get all active challenges
        active_challenges = Challenge.query.filter(
            Challenge.is_active == True,
            Challenge.start_date <= now,
            Challenge.end_date >= now
        ).all()
        
        user_challenges = []
        for challenge in active_challenges:
            # Check if user has this challenge
            user_challenge = UserChallenge.query.filter_by(
                user_id=user_id,
                challenge_id=challenge.id
            ).first()
            
            if not user_challenge:
                # Auto-enroll user in new challenges
                user_challenge = UserChallenge(
                    user_id=user_id,
                    challenge_id=challenge.id,
                    progress=0
                )
                db.session.add(user_challenge)
            
            # Calculate progress based on challenge type
            progress = CrolarsIntegrationService._calculate_challenge_progress(
                user_id, challenge, user_challenge
            )
            
            user_challenges.append({
                'challenge': challenge,
                'user_challenge': user_challenge,
                'progress': progress,
                'progress_percentage': min(100, (progress / challenge.target_value) * 100),
                'is_completed': progress >= challenge.target_value,
                'time_remaining': challenge.end_date - now
            })
        
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
        
        return user_challenges
    
    @staticmethod
    def _calculate_challenge_progress(user_id: int, challenge: Challenge, user_challenge: UserChallenge) -> int:
        """Calculate current progress for a challenge"""
        start_date = max(challenge.start_date, user_challenge.started_at)
        
        if challenge.target_action == 'ask_questions':
            return ForumQuestion.query.filter(
                ForumQuestion.author_id == user_id,
                ForumQuestion.created_at >= start_date
            ).count()
            
        elif challenge.target_action == 'answer_questions':
            return ForumAnswer.query.filter(
                ForumAnswer.author_id == user_id,
                ForumAnswer.created_at >= start_date
            ).count()
            
        elif challenge.target_action == 'get_helpful_votes':
            return db.session.query(func.sum(ForumAnswer.helpful_count)).filter(
                ForumAnswer.author_id == user_id,
                ForumAnswer.created_at >= start_date
            ).scalar() or 0
            
        elif challenge.target_action == 'get_best_answers':
            return ForumAnswer.query.filter(
                ForumAnswer.author_id == user_id,
                ForumAnswer.is_accepted == True,
                ForumAnswer.created_at >= start_date
            ).count()
        
        return user_challenge.progress
    
    @staticmethod
    def claim_challenge_reward(user_id: int, challenge_id: int) -> Dict:
        """Claim reward for completed challenge"""
        user_challenge = UserChallenge.query.filter_by(
            user_id=user_id,
            challenge_id=challenge_id
        ).first()
        
        if not user_challenge:
            return {'success': False, 'error': 'Desafío no encontrado'}
        
        if user_challenge.reward_claimed:
            return {'success': False, 'error': 'Recompensa ya reclamada'}
        
        challenge = user_challenge.challenge
        progress = CrolarsIntegrationService._calculate_challenge_progress(
            user_id, challenge, user_challenge
        )
        
        if progress < challenge.target_value:
            return {'success': False, 'error': 'Desafío no completado'}
        
        # Award Crolars
        user = User.query.get(user_id)
        user.credits += challenge.reward_crolars
        user_challenge.reward_claimed = True
        user_challenge.completed_at = datetime.utcnow()
        
        try:
            db.session.commit()
            return {
                'success': True,
                'reward': challenge.reward_crolars,
                'new_balance': user.credits
            }
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'Error al reclamar: {str(e)}'}