from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy import func, and_, or_
from crunevo.models.forum import ForumQuestion, ForumAnswer, ForumTag
from crunevo.models.user import User
from crunevo.models.badge import UserBadge, ForumBadge as Badge
from crunevo.models.user import User as UserLevel  # Temporary alias
from crunevo.extensions import db


class LearningToolsService:
    """Servicio para herramientas de aprendizaje y seguimiento de progreso"""

    @staticmethod
    def get_user_learning_stats(user_id: int) -> Dict:
        """Obtiene estadísticas de aprendizaje del usuario"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {}

            # Estadísticas básicas
            questions_asked = ForumQuestion.query.filter_by(author_id=user_id).count()
            answers_given = ForumAnswer.query.filter_by(author_id=user_id).count()

            # Preguntas resueltas (donde el usuario dio la mejor respuesta)
            solved_questions = (
                db.session.query(ForumQuestion)
                .join(ForumAnswer, ForumQuestion.id == ForumAnswer.question_id)
                .filter(
                    and_(ForumAnswer.author_id == user_id, ForumAnswer.is_best_answer)
                )
                .count()
            )

            # Tasa de éxito
            success_rate = (
                (solved_questions / answers_given * 100) if answers_given > 0 else 0
            )

            # Actividad por categoría
            category_stats = (
                db.session.query(
                    ForumQuestion.category, func.count(ForumQuestion.id).label("count")
                )
                .filter(
                    or_(
                        ForumQuestion.author_id == user_id,
                        ForumQuestion.id.in_(
                            db.session.query(ForumAnswer.question_id).filter_by(
                                author_id=user_id
                            )
                        ),
                    )
                )
                .group_by(ForumQuestion.category)
                .all()
            )

            # Progreso semanal
            week_ago = datetime.utcnow() - timedelta(days=7)
            weekly_activity = {
                "questions": ForumQuestion.query.filter(
                    and_(
                        ForumQuestion.author_id == user_id,
                        ForumQuestion.created_at >= week_ago,
                    )
                ).count(),
                "answers": ForumAnswer.query.filter(
                    and_(
                        ForumAnswer.author_id == user_id,
                        ForumAnswer.created_at >= week_ago,
                    )
                ).count(),
            }

            # Nivel actual y progreso
            user_level = UserLevel.query.filter_by(user_id=user_id).first()
            current_level = user_level.level if user_level else 1
            current_xp = user_level.experience_points if user_level else 0

            # XP necesario para siguiente nivel
            next_level_xp = LearningToolsService._calculate_xp_for_level(
                current_level + 1
            )
            current_level_xp = LearningToolsService._calculate_xp_for_level(
                current_level
            )
            progress_to_next = (
                (
                    (current_xp - current_level_xp)
                    / (next_level_xp - current_level_xp)
                    * 100
                )
                if next_level_xp > current_level_xp
                else 100
            )

            return {
                "questions_asked": questions_asked,
                "answers_given": answers_given,
                "solved_questions": solved_questions,
                "success_rate": round(success_rate, 1),
                "category_stats": [
                    {"category": cat, "count": count} for cat, count in category_stats
                ],
                "weekly_activity": weekly_activity,
                "current_level": current_level,
                "current_xp": current_xp,
                "progress_to_next": round(progress_to_next, 1),
                "next_level_xp": next_level_xp,
            }

        except Exception as e:
            print(f"Error getting learning stats: {e}")
            return {}

    @staticmethod
    def get_study_recommendations(user_id: int, limit: int = 5) -> List[Dict]:
        """Genera recomendaciones de estudio personalizadas"""
        try:
            user = User.query.get(user_id)
            if not user:
                return []

            recommendations = []

            # Analizar áreas débiles
            weak_categories = LearningToolsService._identify_weak_categories(user_id)

            # Recomendar preguntas sin responder en áreas débiles
            for category in weak_categories[:3]:
                unanswered_questions = (
                    ForumQuestion.query.filter(
                        and_(
                            ForumQuestion.category == category,
                            ForumQuestion.answer_count == 0,
                            ForumQuestion.author_id != user_id,
                        )
                    )
                    .order_by(ForumQuestion.created_at.desc())
                    .limit(2)
                    .all()
                )

                for question in unanswered_questions:
                    recommendations.append(
                        {
                            "type": "practice",
                            "title": f"Practica en {category}",
                            "description": f"Responde: {question.title[:60]}...",
                            "url": f"/foro/pregunta/{question.id}",
                            "category": category,
                            "difficulty": question.difficulty_level,
                            "points": 10
                            + (5 if question.difficulty_level == "hard" else 0),
                        }
                    )

            # Recomendar temas populares
            popular_tags = (
                db.session.query(
                    ForumTag.name, func.count(ForumTag.name).label("usage_count")
                )
                .join(ForumQuestion.tags)
                .group_by(ForumTag.name)
                .order_by(func.count(ForumTag.name).desc())
                .limit(3)
                .all()
            )

            for tag, count in popular_tags:
                recommendations.append(
                    {
                        "type": "explore",
                        "title": f"Explora {tag}",
                        "description": f"Tema popular con {count} preguntas",
                        "url": f"/foro?tag={tag}",
                        "category": "general",
                        "difficulty": "medium",
                        "points": 5,
                    }
                )

            # Recomendar insignias por obtener
            available_badges = LearningToolsService._get_available_badges(user_id)

            for badge in available_badges[:2]:
                recommendations.append(
                    {
                        "type": "achievement",
                        "title": f"Obtén la insignia {badge['name']}",
                        "description": badge["description"],
                        "url": "/foro/insignias",
                        "category": badge["category"],
                        "difficulty": "medium",
                        "points": badge["points"],
                    }
                )

            return recommendations[:limit]

        except Exception as e:
            print(f"Error getting study recommendations: {e}")
            return []

    @staticmethod
    def get_learning_path(user_id: int, subject: str) -> Dict:
        """Genera una ruta de aprendizaje personalizada"""
        try:
            # Evaluar nivel actual en la materia
            current_level = LearningToolsService._assess_subject_level(user_id, subject)

            # Definir pasos de la ruta de aprendizaje
            learning_steps = [
                {
                    "step": 1,
                    "title": "Fundamentos básicos",
                    "description": f"Domina los conceptos básicos de {subject}",
                    "difficulty": "easy",
                    "estimated_time": "1-2 semanas",
                    "completed": current_level >= 1,
                },
                {
                    "step": 2,
                    "title": "Conceptos intermedios",
                    "description": f"Profundiza en temas intermedios de {subject}",
                    "difficulty": "medium",
                    "estimated_time": "2-3 semanas",
                    "completed": current_level >= 2,
                },
                {
                    "step": 3,
                    "title": "Aplicación práctica",
                    "description": "Aplica tus conocimientos en problemas reales",
                    "difficulty": "medium",
                    "estimated_time": "2-4 semanas",
                    "completed": current_level >= 3,
                },
                {
                    "step": 4,
                    "title": "Temas avanzados",
                    "description": f"Explora aspectos avanzados de {subject}",
                    "difficulty": "hard",
                    "estimated_time": "3-5 semanas",
                    "completed": current_level >= 4,
                },
                {
                    "step": 5,
                    "title": "Maestría",
                    "description": f"Conviértete en experto en {subject}",
                    "difficulty": "expert",
                    "estimated_time": "4-6 semanas",
                    "completed": current_level >= 5,
                },
            ]

            # Encontrar preguntas relevantes para cada paso
            for step in learning_steps:
                if not step["completed"]:
                    questions = (
                        ForumQuestion.query.filter(
                            and_(
                                ForumQuestion.category.ilike(f"%{subject}%"),
                                ForumQuestion.difficulty_level == step["difficulty"],
                            )
                        )
                        .limit(3)
                        .all()
                    )

                    step["recommended_questions"] = [
                        {
                            "id": q.id,
                            "title": q.title,
                            "difficulty": q.difficulty_level,
                            "points": 10 + (5 if q.difficulty_level == "hard" else 0),
                        }
                        for q in questions
                    ]
                else:
                    step["recommended_questions"] = []

            return {
                "subject": subject,
                "current_level": current_level,
                "progress_percentage": (current_level / 5) * 100,
                "steps": learning_steps,
                "estimated_completion": f"{(5 - current_level) * 3}-{(5 - current_level) * 4} semanas",
            }

        except Exception as e:
            print(f"Error generating learning path: {e}")
            return {}

    @staticmethod
    def track_study_session(
        user_id: int, activity_type: str, duration_minutes: int, topics: List[str]
    ) -> bool:
        """Registra una sesión de estudio"""
        try:
            # Aquí se podría implementar un modelo StudySession
            # Por ahora, actualizamos las estadísticas del usuario

            user_level = UserLevel.query.filter_by(user_id=user_id).first()
            if user_level:
                # Otorgar XP por tiempo de estudio
                xp_gained = duration_minutes // 10  # 1 XP por cada 10 minutos
                user_level.experience_points += xp_gained
                db.session.commit()

            return True

        except Exception as e:
            print(f"Error tracking study session: {e}")
            return False

    @staticmethod
    def get_performance_analytics(user_id: int, days: int = 30) -> Dict:
        """Analiza el rendimiento del usuario en un período"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            # Actividad diaria
            daily_activity = (
                db.session.query(
                    func.date(ForumQuestion.created_at).label("date"),
                    func.count(ForumQuestion.id).label("questions"),
                )
                .filter(
                    and_(
                        ForumQuestion.author_id == user_id,
                        ForumQuestion.created_at >= start_date,
                    )
                )
                .group_by(func.date(ForumQuestion.created_at))
                .all()
            )

            daily_answers = (
                db.session.query(
                    func.date(ForumAnswer.created_at).label("date"),
                    func.count(ForumAnswer.id).label("answers"),
                )
                .filter(
                    and_(
                        ForumAnswer.author_id == user_id,
                        ForumAnswer.created_at >= start_date,
                    )
                )
                .group_by(func.date(ForumAnswer.created_at))
                .all()
            )

            # Calidad promedio
            avg_question_quality = (
                db.session.query(func.avg(ForumQuestion.quality_score))
                .filter(
                    and_(
                        ForumQuestion.author_id == user_id,
                        ForumQuestion.created_at >= start_date,
                    )
                )
                .scalar()
                or 0
            )

            avg_answer_quality = (
                db.session.query(func.avg(ForumAnswer.quality_score))
                .filter(
                    and_(
                        ForumAnswer.author_id == user_id,
                        ForumAnswer.created_at >= start_date,
                    )
                )
                .scalar()
                or 0
            )

            # Tendencias
            first_half = start_date + timedelta(days=days // 2)

            early_activity = (
                ForumQuestion.query.filter(
                    and_(
                        ForumQuestion.author_id == user_id,
                        ForumQuestion.created_at >= start_date,
                        ForumQuestion.created_at < first_half,
                    )
                ).count()
                + ForumAnswer.query.filter(
                    and_(
                        ForumAnswer.author_id == user_id,
                        ForumAnswer.created_at >= start_date,
                        ForumAnswer.created_at < first_half,
                    )
                ).count()
            )

            recent_activity = (
                ForumQuestion.query.filter(
                    and_(
                        ForumQuestion.author_id == user_id,
                        ForumQuestion.created_at >= first_half,
                    )
                ).count()
                + ForumAnswer.query.filter(
                    and_(
                        ForumAnswer.author_id == user_id,
                        ForumAnswer.created_at >= first_half,
                    )
                ).count()
            )

            activity_trend = (
                "increasing"
                if recent_activity > early_activity
                else "decreasing" if recent_activity < early_activity else "stable"
            )

            return {
                "period_days": days,
                "daily_questions": [
                    {"date": str(date), "count": count}
                    for date, count in daily_activity
                ],
                "daily_answers": [
                    {"date": str(date), "count": count} for date, count in daily_answers
                ],
                "avg_question_quality": round(avg_question_quality, 1),
                "avg_answer_quality": round(avg_answer_quality, 1),
                "activity_trend": activity_trend,
                "total_activity": early_activity + recent_activity,
            }

        except Exception as e:
            print(f"Error getting performance analytics: {e}")
            return {}

    # Métodos auxiliares privados

    @staticmethod
    def _calculate_xp_for_level(level: int) -> int:
        """Calcula XP necesario para un nivel específico"""
        return level * 100 + (level - 1) * 50

    @staticmethod
    def _identify_weak_categories(user_id: int) -> List[str]:
        """Identifica categorías donde el usuario tiene bajo rendimiento"""
        try:
            # Obtener estadísticas por categoría
            category_performance = (
                db.session.query(
                    ForumQuestion.category,
                    func.avg(ForumAnswer.quality_score).label("avg_quality"),
                    func.count(ForumAnswer.id).label("answer_count"),
                )
                .join(ForumAnswer, ForumQuestion.id == ForumAnswer.question_id)
                .filter(ForumAnswer.author_id == user_id)
                .group_by(ForumQuestion.category)
                .all()
            )

            # Identificar categorías con baja calidad o poca actividad
            weak_categories = []
            for category, avg_quality, count in category_performance:
                if avg_quality < 60 or count < 3:
                    weak_categories.append(category)

            return weak_categories

        except Exception as e:
            print(f"Error identifying weak categories: {e}")
            return []

    @staticmethod
    def _get_available_badges(user_id: int) -> List[Dict]:
        """Obtiene insignias disponibles para el usuario"""
        try:
            # Obtener insignias que el usuario no tiene
            earned_badge_ids = (
                db.session.query(UserBadge.badge_id)
                .filter_by(user_id=user_id)
                .subquery()
            )

            available_badges = (
                Badge.query.filter(~Badge.id.in_(earned_badge_ids)).limit(5).all()
            )

            return [
                {
                    "id": badge.id,
                    "name": badge.name,
                    "description": badge.description,
                    "category": badge.category,
                    "points": badge.points_reward,
                }
                for badge in available_badges
            ]

        except Exception as e:
            print(f"Error getting available badges: {e}")
            return []

    @staticmethod
    def _assess_subject_level(user_id: int, subject: str) -> int:
        """Evalúa el nivel del usuario en una materia específica"""
        try:
            # Contar actividad en la materia
            questions_in_subject = ForumQuestion.query.filter(
                and_(
                    ForumQuestion.author_id == user_id,
                    ForumQuestion.category.ilike(f"%{subject}%"),
                )
            ).count()

            answers_in_subject = (
                db.session.query(ForumAnswer)
                .join(ForumQuestion, ForumAnswer.question_id == ForumQuestion.id)
                .filter(
                    and_(
                        ForumAnswer.author_id == user_id,
                        ForumQuestion.category.ilike(f"%{subject}%"),
                    )
                )
                .count()
            )

            total_activity = questions_in_subject + answers_in_subject

            # Determinar nivel basado en actividad
            if total_activity >= 50:
                return 5
            elif total_activity >= 30:
                return 4
            elif total_activity >= 15:
                return 3
            elif total_activity >= 5:
                return 2
            elif total_activity >= 1:
                return 1
            else:
                return 0

        except Exception as e:
            print(f"Error assessing subject level: {e}")
            return 0
