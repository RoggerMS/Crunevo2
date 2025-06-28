
from datetime import datetime, timedelta
from sqlalchemy import func
from crunevo.models import Post, Note, User, Purchase
from crunevo.extensions import db

class Analytics:
    @staticmethod
    def get_engagement_metrics(days=7):
        """Métricas de engagement de los últimos N días"""
        since = datetime.utcnow() - timedelta(days=days)
        
        metrics = {
            'new_posts': Post.query.filter(Post.created_at >= since).count(),
            'new_notes': Note.query.filter(Note.created_at >= since).count(),
            'new_users': User.query.filter(User.created_at >= since).count(),
            'total_likes': db.session.query(func.sum(Post.likes)).filter(Post.created_at >= since).scalar() or 0,
            'active_users': db.session.query(func.count(func.distinct(Post.author_id))).filter(Post.created_at >= since).scalar() or 0
        }
        
        return metrics
    
    @staticmethod
    def get_revenue_metrics(days=30):
        """Métricas de ingresos"""
        since = datetime.utcnow() - timedelta(days=days)
        
        revenue = db.session.query(
            func.sum(Purchase.total_credits),
            func.count(Purchase.id)
        ).filter(Purchase.created_at >= since).first()
        
        return {
            'total_revenue': revenue[0] or 0,
            'total_purchases': revenue[1] or 0,
            'avg_purchase': (revenue[0] / revenue[1]) if revenue[1] > 0 else 0
        }
