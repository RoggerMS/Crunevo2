from datetime import datetime
from crunevo.extensions import db
from sqlalchemy.dialects.postgresql import JSONB

class SystemMetrics(db.Model):
    """Modelo para almacenar métricas del sistema"""
    __tablename__ = 'system_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Métricas del sistema
    system_metrics = db.Column(JSONB)
    
    # Métricas de base de datos
    database_metrics = db.Column(JSONB)
    
    # Métricas de rendimiento
    performance_metrics = db.Column(JSONB)
    
    # Alertas
    alerts = db.Column(JSONB)
    
    def __repr__(self):
        return f'<SystemMetrics {self.id} at {self.timestamp}>'
    
    def to_dict(self):
        """Convierte el modelo a diccionario"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'system_metrics': self.system_metrics,
            'database_metrics': self.database_metrics,
            'performance_metrics': self.performance_metrics,
            'alerts': self.alerts
        }

class PerformanceMetric(db.Model):
    """Modelo para métricas de rendimiento específicas"""
    __tablename__ = 'performance_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    operation = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.Float, nullable=False)  # en segundos
    success = db.Column(db.Boolean, default=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Información adicional
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<PerformanceMetric {self.operation} {self.duration}s>'
    
    def to_dict(self):
        """Convierte el modelo a diccionario"""
        return {
            'id': self.id,
            'operation': self.operation,
            'duration': self.duration,
            'success': self.success,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'user_id': self.user_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent
        } 