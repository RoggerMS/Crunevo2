from typing import Dict, List
import re
from datetime import datetime, timedelta
from sqlalchemy import func
from crunevo.extensions import db
from crunevo.models.forum import ForumQuestion, ForumAnswer, ForumReport
from crunevo.models.user import User


class ModerationService:
    """Servicio de moderación automática para el foro"""

    # Palabras y patrones que indican contenido de baja calidad
    LOW_QUALITY_PATTERNS = [
        r"\b(ayuda|help|pls|plz|por favor)\b",
        r"^.{1,10}$",  # Contenido muy corto
        r"\b(urgente|rapido|ya|ahora)\b",
        r"[A-Z]{5,}",  # Muchas mayúsculas seguidas
        r"[!]{3,}|[?]{3,}",  # Múltiples signos de exclamación/interrogación
    ]

    # Palabras spam comunes
    SPAM_KEYWORDS = [
        "gratis",
        "dinero",
        "ganar",
        "click",
        "enlace",
        "link",
        "promocion",
        "oferta",
        "descuento",
        "premio",
    ]

    # Patrones de contenido duplicado
    DUPLICATE_PATTERNS = [
        r"(.)\1{4,}",  # Caracteres repetidos
        r"\b(\w+)\s+\1\b",  # Palabras duplicadas
    ]

    @staticmethod
    def analyze_content_quality(content: str, title: str = "") -> Dict[str, any]:
        """Analiza la calidad del contenido y retorna un score y detalles"""

        full_text = f"{title} {content}".lower()
        issues = []
        quality_score = 100  # Empezamos con 100 y restamos puntos

        # 1. Verificar longitud mínima
        if len(content.strip()) < 20:
            issues.append("Contenido muy corto")
            quality_score -= 30

        # 2. Verificar patrones de baja calidad
        for pattern in ModerationService.LOW_QUALITY_PATTERNS:
            if re.search(pattern, full_text, re.IGNORECASE):
                issues.append("Contiene patrones de baja calidad")
                quality_score -= 15
                break

        # 3. Verificar spam
        spam_count = sum(
            1 for keyword in ModerationService.SPAM_KEYWORDS if keyword in full_text
        )
        if spam_count > 0:
            issues.append(f"Posible spam ({spam_count} palabras sospechosas)")
            quality_score -= spam_count * 10

        # 4. Verificar contenido duplicado
        for pattern in ModerationService.DUPLICATE_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append("Contiene patrones repetitivos")
                quality_score -= 20
                break

        # 5. Verificar ratio de mayúsculas
        if content:
            uppercase_ratio = sum(1 for c in content if c.isupper()) / len(content)
            if uppercase_ratio > 0.3:
                issues.append("Demasiadas mayúsculas")
                quality_score -= 25

        # 6. Verificar signos de puntuación excesivos
        punctuation_count = len(re.findall(r"[!?]{2,}", content))
        if punctuation_count > 2:
            issues.append("Uso excesivo de signos de puntuación")
            quality_score -= 15

        # 7. Verificar si tiene estructura (párrafos, puntos, etc.)
        has_structure = bool(re.search(r"\n|\.|,|;|:", content))
        if not has_structure and len(content) > 50:
            issues.append("Falta de estructura en el texto")
            quality_score -= 10

        # Asegurar que el score no sea negativo
        quality_score = max(0, quality_score)

        # Determinar nivel de calidad
        if quality_score >= 80:
            quality_level = "high"
        elif quality_score >= 60:
            quality_level = "medium"
        elif quality_score >= 40:
            quality_level = "low"
        else:
            quality_level = "very_low"

        return {
            "quality_score": quality_score,
            "quality_level": quality_level,
            "issues": issues,
            "requires_review": quality_score < 60,
            "auto_reject": quality_score < 30,
        }

    @staticmethod
    def check_user_behavior(user_id: int) -> Dict[str, any]:
        """Analiza el comportamiento del usuario para detectar patrones sospechosos"""

        user = User.query.get(user_id)
        if not user:
            return {"is_suspicious": False, "reasons": []}

        suspicious_reasons = []

        # 1. Verificar frecuencia de publicaciones
        recent_questions = ForumQuestion.query.filter(
            ForumQuestion.author_id == user_id,
            ForumQuestion.created_at >= datetime.utcnow() - timedelta(hours=1),
        ).count()

        if recent_questions > 5:
            suspicious_reasons.append("Demasiadas preguntas en poco tiempo")

        # 2. Verificar ratio de preguntas vs respuestas
        total_questions = ForumQuestion.query.filter_by(author_id=user_id).count()
        total_answers = ForumAnswer.query.filter_by(author_id=user_id).count()

        if total_questions > 10 and total_answers == 0:
            suspicious_reasons.append("Solo hace preguntas, nunca responde")

        # 3. Verificar reportes recibidos
        recent_reports = ForumReport.query.filter(
            ForumReport.reported_user_id == user_id,
            ForumReport.created_at >= datetime.utcnow() - timedelta(days=7),
        ).count()

        if recent_reports > 3:
            suspicious_reasons.append("Múltiples reportes recientes")

        # 4. Verificar cuenta nueva con actividad alta
        account_age = datetime.utcnow() - user.created_at
        if account_age.days < 1 and (total_questions + total_answers) > 10:
            suspicious_reasons.append("Cuenta nueva con actividad muy alta")

        return {
            "is_suspicious": len(suspicious_reasons) > 0,
            "reasons": suspicious_reasons,
            "risk_level": (
                "high"
                if len(suspicious_reasons) >= 3
                else "medium" if len(suspicious_reasons) >= 2 else "low"
            ),
        }

    @staticmethod
    def auto_moderate_question(question: ForumQuestion) -> Dict[str, any]:
        """Modera automáticamente una pregunta"""

        # Analizar calidad del contenido
        content_analysis = ModerationService.analyze_content_quality(
            question.content, question.title
        )

        # Analizar comportamiento del usuario
        user_analysis = ModerationService.check_user_behavior(question.author_id)

        # Determinar acción
        action = "approve"  # Por defecto aprobar

        if content_analysis["auto_reject"] or user_analysis["risk_level"] == "high":
            action = "reject"
        elif content_analysis["requires_review"] or user_analysis["is_suspicious"]:
            action = "review"

        # Actualizar score de calidad en la pregunta
        question.quality_score = content_analysis["quality_score"]

        return {
            "action": action,
            "content_analysis": content_analysis,
            "user_analysis": user_analysis,
            "confidence": ModerationService._calculate_confidence(
                content_analysis, user_analysis
            ),
        }

    @staticmethod
    def auto_moderate_answer(answer: ForumAnswer) -> Dict[str, any]:
        """Modera automáticamente una respuesta"""

        # Analizar calidad del contenido
        content_analysis = ModerationService.analyze_content_quality(answer.content)

        # Analizar comportamiento del usuario
        user_analysis = ModerationService.check_user_behavior(answer.author_id)

        # Determinar acción
        action = "approve"

        if content_analysis["auto_reject"] or user_analysis["risk_level"] == "high":
            action = "reject"
        elif content_analysis["requires_review"] or user_analysis["is_suspicious"]:
            action = "review"

        # Actualizar score de calidad en la respuesta
        answer.quality_score = content_analysis["quality_score"]

        return {
            "action": action,
            "content_analysis": content_analysis,
            "user_analysis": user_analysis,
            "confidence": ModerationService._calculate_confidence(
                content_analysis, user_analysis
            ),
        }

    @staticmethod
    def _calculate_confidence(content_analysis: Dict, user_analysis: Dict) -> float:
        """Calcula la confianza en la decisión de moderación"""

        base_confidence = 0.7

        # Aumentar confianza si hay múltiples indicadores
        if len(content_analysis["issues"]) > 2:
            base_confidence += 0.1

        if user_analysis["is_suspicious"]:
            base_confidence += 0.1

        # Reducir confianza si los scores están en zona gris
        if 40 <= content_analysis["quality_score"] <= 70:
            base_confidence -= 0.2

        return min(1.0, max(0.1, base_confidence))

    @staticmethod
    def get_moderation_stats() -> Dict[str, any]:
        """Obtiene estadísticas de moderación"""

        # Contar contenido por calidad
        high_quality = (
            db.session.query(func.count(ForumQuestion.id))
            .filter(ForumQuestion.quality_score >= 80)
            .scalar()
            or 0
        )

        medium_quality = (
            db.session.query(func.count(ForumQuestion.id))
            .filter(ForumQuestion.quality_score.between(60, 79))
            .scalar()
            or 0
        )

        low_quality = (
            db.session.query(func.count(ForumQuestion.id))
            .filter(ForumQuestion.quality_score < 60)
            .scalar()
            or 0
        )

        # Reportes pendientes
        pending_reports = ForumReport.query.filter_by(status="pending").count()

        return {
            "high_quality_content": high_quality,
            "medium_quality_content": medium_quality,
            "low_quality_content": low_quality,
            "pending_reports": pending_reports,
            "total_content": high_quality + medium_quality + low_quality,
        }

    @staticmethod
    def suggest_improvements(content: str, issues: List[str]) -> List[str]:
        """Sugiere mejoras basadas en los problemas detectados"""

        suggestions = []

        if "Contenido muy corto" in issues:
            suggestions.append(
                "Proporciona más detalles sobre tu pregunta. Incluye contexto, lo que has intentado y dónde tienes dificultades."
            )

        if "Contiene patrones de baja calidad" in issues:
            suggestions.append(
                "Evita usar palabras como 'ayuda', 'urgente' o 'rápido'. En su lugar, sé específico sobre lo que necesitas."
            )

        if "Demasiadas mayúsculas" in issues:
            suggestions.append(
                "Evita escribir en mayúsculas. Usa mayúsculas solo al inicio de oraciones y para nombres propios."
            )

        if "Uso excesivo de signos de puntuación" in issues:
            suggestions.append(
                "Usa signos de puntuación con moderación. Un solo signo de interrogación o exclamación es suficiente."
            )

        if "Falta de estructura en el texto" in issues:
            suggestions.append(
                "Organiza tu texto en párrafos. Usa puntos y comas para hacer tu pregunta más clara."
            )

        if not suggestions:
            suggestions.append(
                "Tu contenido se ve bien. Considera agregar más detalles si es necesario."
            )

        return suggestions
