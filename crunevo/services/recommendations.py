from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from sqlalchemy import func, and_, or_, desc
from crunevo.models.forum import ForumQuestion, ForumAnswer, ForumTag, question_tags
from crunevo.models.user import User
from crunevo.extensions import db


class RecommendationService:
    """Servicio para generar recomendaciones personalizadas"""

    @staticmethod
    def get_personalized_recommendations(user_id: int, limit: int = 10) -> List[Dict]:
        """Genera recomendaciones personalizadas basadas en el comportamiento del usuario"""
        try:
            user = User.query.get(user_id)
            if not user:
                return []

            recommendations = []

            # 1. Recomendaciones basadas en actividad reciente
            recent_recommendations = (
                RecommendationService._get_activity_based_recommendations(
                    user_id, limit // 3
                )
            )
            recommendations.extend(recent_recommendations)

            # 2. Recomendaciones basadas en intereses (tags)
            interest_recommendations = (
                RecommendationService._get_interest_based_recommendations(
                    user_id, limit // 3
                )
            )
            recommendations.extend(interest_recommendations)

            # 3. Recomendaciones colaborativas (usuarios similares)
            collaborative_recommendations = (
                RecommendationService._get_collaborative_recommendations(
                    user_id, limit // 3
                )
            )
            recommendations.extend(collaborative_recommendations)

            # 4. Recomendaciones de contenido popular
            if len(recommendations) < limit:
                popular_recommendations = (
                    RecommendationService._get_popular_content_recommendations(
                        user_id, limit - len(recommendations)
                    )
                )
                recommendations.extend(popular_recommendations)

            # Ordenar por score y eliminar duplicados
            seen_ids = set()
            unique_recommendations = []

            for rec in sorted(
                recommendations, key=lambda x: x.get("score", 0), reverse=True
            ):
                if rec["id"] not in seen_ids:
                    seen_ids.add(rec["id"])
                    unique_recommendations.append(rec)
                    if len(unique_recommendations) >= limit:
                        break

            return unique_recommendations

        except Exception as e:
            print(f"Error getting personalized recommendations: {e}")
            return []

    @staticmethod
    def get_similar_questions(question_id: int, limit: int = 5) -> List[Dict]:
        """Encuentra preguntas similares basadas en contenido y tags"""
        try:
            question = ForumQuestion.query.get(question_id)
            if not question:
                return []

            # Obtener tags de la pregunta actual
            current_tags = [tag.name for tag in question.tags]

            # Buscar preguntas con tags similares
            similar_questions = (
                db.session.query(ForumQuestion)
                .join(ForumQuestion.tags)
                .filter(
                    and_(
                        ForumQuestion.id != question_id, ForumTag.name.in_(current_tags)
                    )
                )
                .group_by(ForumQuestion.id)
                .order_by(
                    desc(func.count(ForumTag.id)),  # Más tags en común primero
                    desc(ForumQuestion.views),
                )
                .limit(limit * 2)
                .all()
            )  # Obtener más para filtrar

            recommendations = []
            for similar_q in similar_questions:
                # Calcular score de similitud
                common_tags = len(
                    set(current_tags) & set([tag.name for tag in similar_q.tags])
                )
                category_match = 1 if similar_q.category == question.category else 0
                difficulty_match = (
                    1 if similar_q.difficulty_level == question.difficulty_level else 0
                )

                score = (
                    (common_tags * 0.5)
                    + (category_match * 0.3)
                    + (difficulty_match * 0.2)
                )

                recommendations.append(
                    {
                        "id": similar_q.id,
                        "title": similar_q.title,
                        "category": similar_q.category,
                        "difficulty": similar_q.difficulty_level,
                        "views": similar_q.views,
                        "answer_count": similar_q.answer_count,
                        "is_solved": similar_q.is_solved,
                        "score": score,
                        "reason": f"Comparte {common_tags} tema(s) en común",
                        "url": f"/foro/pregunta/{similar_q.id}",
                    }
                )

            # Ordenar por score y retornar los mejores
            return sorted(recommendations, key=lambda x: x["score"], reverse=True)[
                :limit
            ]

        except Exception as e:
            print(f"Error getting similar questions: {e}")
            return []

    @staticmethod
    def get_trending_topics(days: int = 7, limit: int = 10) -> List[Dict]:
        """Obtiene temas trending basados en actividad reciente"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            # Obtener tags más usados en el período
            trending_tags = (
                db.session.query(
                    ForumTag.name,
                    func.count(ForumTag.name).label("usage_count"),
                    func.count(func.distinct(ForumQuestion.id)).label("question_count"),
                )
                .join(question_tags, ForumTag.id == question_tags.c.tag_id)
                .join(ForumQuestion, question_tags.c.question_id == ForumQuestion.id)
                .filter(ForumQuestion.created_at >= start_date)
                .group_by(ForumTag.name)
                .order_by(desc(func.count(ForumTag.name)))
                .limit(limit)
                .all()
            )

            # Obtener categorías más activas
            trending_categories = (
                db.session.query(
                    ForumQuestion.category,
                    func.count(ForumQuestion.id).label("question_count"),
                    func.sum(ForumQuestion.views).label("total_views"),
                )
                .filter(ForumQuestion.created_at >= start_date)
                .group_by(ForumQuestion.category)
                .order_by(desc(func.count(ForumQuestion.id)))
                .limit(limit)
                .all()
            )

            trends = []

            # Agregar tags trending
            for tag, usage_count, question_count in trending_tags:
                trends.append(
                    {
                        "type": "tag",
                        "name": tag,
                        "activity_count": usage_count,
                        "question_count": question_count,
                        "url": f"/foro?tags={tag}",
                        "description": f"{question_count} preguntas recientes",
                    }
                )

            # Agregar categorías trending
            for category, question_count, total_views in trending_categories:
                trends.append(
                    {
                        "type": "category",
                        "name": category,
                        "activity_count": question_count,
                        "total_views": total_views or 0,
                        "url": f"/foro?category={category}",
                        "description": f"{question_count} preguntas, {total_views or 0} vistas",
                    }
                )

            return trends[:limit]

        except Exception as e:
            print(f"Error getting trending topics: {e}")
            return []

    @staticmethod
    def get_study_recommendations_for_user(
        user_id: int, subject: str = None, limit: int = 5
    ) -> List[Dict]:
        """Genera recomendaciones de estudio específicas para un usuario"""
        try:
            user = User.query.get(user_id)
            if not user:
                return []

            recommendations = []

            # Analizar áreas débiles del usuario
            weak_areas = RecommendationService._identify_weak_areas(user_id, subject)

            # Recomendar preguntas sin responder en áreas débiles
            for area in weak_areas:
                category_filter = area if subject is None else subject

                unanswered_questions = (
                    ForumQuestion.query.filter(
                        and_(
                            ForumQuestion.category.ilike(f"%{category_filter}%"),
                            ForumQuestion.answer_count == 0,
                            ForumQuestion.author_id != user_id,
                        )
                    )
                    .order_by(
                        desc(ForumQuestion.bounty_points),
                        desc(ForumQuestion.created_at),
                    )
                    .limit(2)
                    .all()
                )

                for question in unanswered_questions:
                    recommendations.append(
                        {
                            "id": question.id,
                            "type": "practice",
                            "title": question.title,
                            "category": question.category,
                            "difficulty": question.difficulty_level,
                            "bounty_points": question.bounty_points,
                            "reason": f"Área de mejora: {area}",
                            "url": f"/foro/pregunta/{question.id}",
                            "action": "Responder para practicar",
                        }
                    )

            # Recomendar preguntas resueltas para estudiar
            solved_questions = (
                ForumQuestion.query.filter(
                    and_(
                        ForumQuestion.is_solved,
                        (
                            ForumQuestion.category.ilike(f"%{subject}%")
                            if subject
                            else True
                        ),
                        ForumQuestion.author_id != user_id,
                    )
                )
                .order_by(desc(ForumQuestion.views), desc(ForumQuestion.answer_count))
                .limit(3)
                .all()
            )

            for question in solved_questions:
                recommendations.append(
                    {
                        "id": question.id,
                        "type": "study",
                        "title": question.title,
                        "category": question.category,
                        "difficulty": question.difficulty_level,
                        "answer_count": question.answer_count,
                        "reason": "Problema resuelto para estudiar",
                        "url": f"/foro/pregunta/{question.id}",
                        "action": "Estudiar solución",
                    }
                )

            return recommendations[:limit]

        except Exception as e:
            print(f"Error getting study recommendations: {e}")
            return []

    @staticmethod
    def get_content_recommendations_by_performance(
        user_id: int, limit: int = 5
    ) -> List[Dict]:
        """Recomienda contenido basado en el rendimiento del usuario"""
        try:
            user = User.query.get(user_id)
            if not user:
                return []

            # Analizar rendimiento por categoría
            performance_by_category = RecommendationService._analyze_user_performance(
                user_id
            )

            recommendations = []

            for category, performance in performance_by_category.items():
                if performance["avg_quality"] < 60:  # Área de mejora
                    # Recomendar contenido educativo
                    educational_questions = (
                        ForumQuestion.query.filter(
                            and_(
                                ForumQuestion.category == category,
                                ForumQuestion.is_solved,
                                ForumQuestion.difficulty_level == "basico",
                            )
                        )
                        .order_by(desc(ForumQuestion.views))
                        .limit(2)
                        .all()
                    )

                    for question in educational_questions:
                        recommendations.append(
                            {
                                "id": question.id,
                                "type": "improvement",
                                "title": question.title,
                                "category": question.category,
                                "difficulty": question.difficulty_level,
                                "reason": f"Mejorar en {category} (calidad actual: {performance['avg_quality']:.1f}%)",
                                "url": f"/foro/pregunta/{question.id}",
                                "priority": "high",
                            }
                        )

                elif performance["avg_quality"] > 80:  # Área fuerte
                    # Recomendar desafíos más difíciles
                    challenging_questions = (
                        ForumQuestion.query.filter(
                            and_(
                                ForumQuestion.category == category,
                                ForumQuestion.difficulty_level == "avanzado",
                                ForumQuestion.answer_count == 0,
                            )
                        )
                        .order_by(desc(ForumQuestion.bounty_points))
                        .limit(1)
                        .all()
                    )

                    for question in challenging_questions:
                        recommendations.append(
                            {
                                "id": question.id,
                                "type": "challenge",
                                "title": question.title,
                                "category": question.category,
                                "difficulty": question.difficulty_level,
                                "bounty_points": question.bounty_points,
                                "reason": f"Desafío en tu área fuerte: {category}",
                                "url": f"/foro/pregunta/{question.id}",
                                "priority": "medium",
                            }
                        )

            return recommendations[:limit]

        except Exception as e:
            print(f"Error getting performance-based recommendations: {e}")
            return []

    # Métodos auxiliares privados

    @staticmethod
    def _get_activity_based_recommendations(user_id: int, limit: int) -> List[Dict]:
        """Recomendaciones basadas en actividad reciente del usuario"""
        try:
            # Obtener categorías donde el usuario ha sido activo recientemente
            recent_activity = (
                db.session.query(
                    ForumQuestion.category,
                    func.count(ForumQuestion.id).label("activity_count"),
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
                .filter(
                    ForumQuestion.created_at >= datetime.utcnow() - timedelta(days=30)
                )
                .group_by(ForumQuestion.category)
                .order_by(desc(func.count(ForumQuestion.id)))
                .limit(3)
                .all()
            )

            recommendations = []

            for category, activity_count in recent_activity:
                # Buscar preguntas sin responder en esas categorías
                questions = (
                    ForumQuestion.query.filter(
                        and_(
                            ForumQuestion.category == category,
                            ForumQuestion.answer_count == 0,
                            ForumQuestion.author_id != user_id,
                        )
                    )
                    .order_by(desc(ForumQuestion.created_at))
                    .limit(2)
                    .all()
                )

                for question in questions:
                    recommendations.append(
                        {
                            "id": question.id,
                            "title": question.title,
                            "category": question.category,
                            "difficulty": question.difficulty_level,
                            "score": activity_count * 0.8,
                            "reason": f"Activo recientemente en {category}",
                            "url": f"/foro/pregunta/{question.id}",
                        }
                    )

            return recommendations[:limit]

        except Exception as e:
            print(f"Error getting activity-based recommendations: {e}")
            return []

    @staticmethod
    def _get_interest_based_recommendations(user_id: int, limit: int) -> List[Dict]:
        """Recomendaciones basadas en intereses (tags) del usuario"""
        try:
            # Obtener tags más usados por el usuario
            user_tags = (
                db.session.query(
                    ForumTag.name, func.count(ForumTag.name).label("usage_count")
                )
                .join(question_tags, ForumTag.id == question_tags.c.tag_id)
                .join(ForumQuestion, question_tags.c.question_id == ForumQuestion.id)
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
                .group_by(ForumTag.name)
                .order_by(desc(func.count(ForumTag.name)))
                .limit(5)
                .all()
            )

            recommendations = []

            for tag_name, usage_count in user_tags:
                # Buscar preguntas con estos tags
                questions = (
                    db.session.query(ForumQuestion)
                    .join(ForumQuestion.tags)
                    .filter(
                        and_(
                            ForumTag.name == tag_name,
                            ForumQuestion.author_id != user_id,
                            ForumQuestion.answer_count
                            < 3,  # Preguntas que necesitan más respuestas
                        )
                    )
                    .order_by(desc(ForumQuestion.created_at))
                    .limit(2)
                    .all()
                )

                for question in questions:
                    recommendations.append(
                        {
                            "id": question.id,
                            "title": question.title,
                            "category": question.category,
                            "difficulty": question.difficulty_level,
                            "score": usage_count * 0.6,
                            "reason": f"Interés en {tag_name}",
                            "url": f"/foro/pregunta/{question.id}",
                        }
                    )

            return recommendations[:limit]

        except Exception as e:
            print(f"Error getting interest-based recommendations: {e}")
            return []

    @staticmethod
    def _get_collaborative_recommendations(user_id: int, limit: int) -> List[Dict]:
        """Recomendaciones colaborativas basadas en usuarios similares"""
        try:
            # Encontrar usuarios con intereses similares
            similar_users = RecommendationService._find_similar_users(user_id, 5)

            recommendations = []

            for similar_user_id, similarity_score in similar_users:
                # Obtener preguntas que este usuario similar ha respondido bien
                good_answers = (
                    db.session.query(ForumAnswer)
                    .filter(
                        and_(
                            ForumAnswer.author_id == similar_user_id,
                            ForumAnswer.is_best_answer,
                        )
                    )
                    .limit(2)
                    .all()
                )

                for answer in good_answers:
                    question = answer.question
                    if question.author_id != user_id:  # No recomendar propias preguntas
                        recommendations.append(
                            {
                                "id": question.id,
                                "title": question.title,
                                "category": question.category,
                                "difficulty": question.difficulty_level,
                                "score": similarity_score * 0.4,
                                "reason": "Usuario con intereses similares",
                                "url": f"/foro/pregunta/{question.id}",
                            }
                        )

            return recommendations[:limit]

        except Exception as e:
            print(f"Error getting collaborative recommendations: {e}")
            return []

    @staticmethod
    def _get_popular_content_recommendations(user_id: int, limit: int) -> List[Dict]:
        """Recomendaciones de contenido popular"""
        try:
            # Obtener preguntas populares que el usuario no ha visto
            popular_questions = (
                ForumQuestion.query.filter(ForumQuestion.author_id != user_id)
                .order_by(desc(ForumQuestion.views), desc(ForumQuestion.answer_count))
                .limit(limit * 2)
                .all()
            )

            recommendations = []

            for question in popular_questions:
                recommendations.append(
                    {
                        "id": question.id,
                        "title": question.title,
                        "category": question.category,
                        "difficulty": question.difficulty_level,
                        "views": question.views,
                        "score": question.views * 0.001,  # Score basado en popularidad
                        "reason": f"Popular: {question.views} vistas",
                        "url": f"/foro/pregunta/{question.id}",
                    }
                )

            return recommendations[:limit]

        except Exception as e:
            print(f"Error getting popular content recommendations: {e}")
            return []

    @staticmethod
    def _find_similar_users(user_id: int, limit: int) -> List[Tuple[int, float]]:
        """Encuentra usuarios con intereses similares"""
        try:
            # Obtener categorías de interés del usuario
            user_categories = (
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

            user_category_counts = {
                category: count for category, count in user_categories
            }

            # Encontrar otros usuarios activos en las mismas categorías
            similar_users = []

            for category in user_category_counts.keys():
                other_users = (
                    db.session.query(
                        User.id, func.count(ForumQuestion.id).label("activity_count")
                    )
                    .join(ForumQuestion, User.id == ForumQuestion.author_id)
                    .filter(
                        and_(ForumQuestion.category == category, User.id != user_id)
                    )
                    .group_by(User.id)
                    .order_by(desc(func.count(ForumQuestion.id)))
                    .limit(10)
                    .all()
                )

                for other_user_id, activity_count in other_users:
                    # Calcular similitud simple basada en actividad compartida
                    similarity = min(
                        activity_count, user_category_counts[category]
                    ) / max(activity_count, user_category_counts[category])
                    similar_users.append((other_user_id, similarity))

            # Ordenar por similitud y retornar los mejores
            similar_users.sort(key=lambda x: x[1], reverse=True)
            return similar_users[:limit]

        except Exception as e:
            print(f"Error finding similar users: {e}")
            return []

    @staticmethod
    def _identify_weak_areas(user_id: int, subject: str = None) -> List[str]:
        """Identifica áreas donde el usuario necesita mejorar"""
        try:
            # Analizar rendimiento por categoría
            performance_query = (
                db.session.query(
                    ForumQuestion.category,
                    func.avg(ForumAnswer.quality_score).label("avg_quality"),
                    func.count(ForumAnswer.id).label("answer_count"),
                )
                .join(ForumAnswer, ForumQuestion.id == ForumAnswer.question_id)
                .filter(ForumAnswer.author_id == user_id)
            )

            if subject:
                performance_query = performance_query.filter(
                    ForumQuestion.category.ilike(f"%{subject}%")
                )

            performance_data = performance_query.group_by(ForumQuestion.category).all()

            weak_areas = []
            for category, avg_quality, answer_count in performance_data:
                if avg_quality < 60 or answer_count < 3:
                    weak_areas.append(category)

            return weak_areas

        except Exception as e:
            print(f"Error identifying weak areas: {e}")
            return []

    @staticmethod
    def _analyze_user_performance(user_id: int) -> Dict[str, Dict]:
        """Analiza el rendimiento del usuario por categoría"""
        try:
            performance_data = (
                db.session.query(
                    ForumQuestion.category,
                    func.avg(ForumAnswer.quality_score).label("avg_quality"),
                    func.count(ForumAnswer.id).label("answer_count"),
                    func.sum(ForumAnswer.is_best_answer).label("best_answers"),
                )
                .join(ForumAnswer, ForumQuestion.id == ForumAnswer.question_id)
                .filter(ForumAnswer.author_id == user_id)
                .group_by(ForumQuestion.category)
                .all()
            )

            performance = {}
            for category, avg_quality, answer_count, best_answers in performance_data:
                performance[category] = {
                    "avg_quality": avg_quality or 0,
                    "answer_count": answer_count,
                    "best_answers": best_answers or 0,
                    "success_rate": (
                        (best_answers / answer_count * 100) if answer_count > 0 else 0
                    ),
                }

            return performance

        except Exception as e:
            print(f"Error analyzing user performance: {e}")
            return {}
