import logging
import time
import psutil
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from flask import current_app, request
from crunevo.extensions import db
from crunevo.models import User, Post, Note, FeedItem

logger = logging.getLogger(__name__)

class CRUNEVOMonitor:
    """Sistema de monitoreo para CRUNEVO"""
    
    def __init__(self):
        self.metrics = {}
        self.alerts = []
        self.performance_data = {}
    
    def collect_system_metrics(self) -> Dict:
        """Recopila métricas del sistema"""
        try:
            # Métricas del sistema
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Métricas de la aplicación
            app_metrics = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available': memory.available / (1024**3),  # GB
                'disk_percent': disk.percent,
                'disk_free': disk.free / (1024**3),  # GB
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.metrics['system'] = app_metrics
            return app_metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {}
    
    def collect_database_metrics(self) -> Dict:
        """Recopila métricas de la base de datos"""
        try:
            start_time = time.time()
            
            # Contar registros principales
            user_count = User.query.count()
            post_count = Post.query.count()
            note_count = Note.query.count()
            feed_item_count = FeedItem.query.count()
            
            # Verificar conexión
            db.session.execute('SELECT 1')
            db_connection_time = (time.time() - start_time) * 1000
            
            db_metrics = {
                'user_count': user_count,
                'post_count': post_count,
                'note_count': note_count,
                'feed_item_count': feed_item_count,
                'connection_time_ms': db_connection_time,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.metrics['database'] = db_metrics
            return db_metrics
            
        except Exception as e:
            logger.error(f"Error collecting database metrics: {e}")
            return {}
    
    def collect_performance_metrics(self) -> Dict:
        """Recopila métricas de rendimiento de la aplicación"""
        try:
            # Métricas de request
            request_metrics = {
                'active_requests': len(request.environ.get('werkzeug.request', [])),
                'request_time': getattr(request, '_start_time', 0),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Métricas de caché
            from crunevo.cache.feed_cache import get_cache_stats
            cache_stats = get_cache_stats()
            
            perf_metrics = {
                'request': request_metrics,
                'cache': cache_stats,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.metrics['performance'] = perf_metrics
            return perf_metrics
            
        except Exception as e:
            logger.error(f"Error collecting performance metrics: {e}")
            return {}
    
    def check_alerts(self) -> List[Dict]:
        """Verifica si hay alertas que disparar"""
        alerts = []
        
        # Verificar métricas del sistema
        if 'system' in self.metrics:
            sys_metrics = self.metrics['system']
            
            if sys_metrics.get('cpu_percent', 0) > 80:
                alerts.append({
                    'type': 'high_cpu',
                    'message': f'CPU usage is high: {sys_metrics["cpu_percent"]}%',
                    'severity': 'warning',
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            if sys_metrics.get('memory_percent', 0) > 85:
                alerts.append({
                    'type': 'high_memory',
                    'message': f'Memory usage is high: {sys_metrics["memory_percent"]}%',
                    'severity': 'warning',
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            if sys_metrics.get('disk_percent', 0) > 90:
                alerts.append({
                    'type': 'low_disk',
                    'message': f'Disk space is low: {sys_metrics["disk_percent"]}% used',
                    'severity': 'critical',
                    'timestamp': datetime.utcnow().isoformat()
                })
        
        # Verificar métricas de base de datos
        if 'database' in self.metrics:
            db_metrics = self.metrics['database']
            
            if db_metrics.get('connection_time_ms', 0) > 1000:
                alerts.append({
                    'type': 'slow_database',
                    'message': f'Database connection is slow: {db_metrics["connection_time_ms"]}ms',
                    'severity': 'warning',
                    'timestamp': datetime.utcnow().isoformat()
                })
        
        self.alerts = alerts
        return alerts
    
    def log_metrics(self):
        """Registra las métricas recopiladas"""
        try:
            from crunevo.models import SystemMetrics
            
            # Crear registro de métricas
            metrics_record = SystemMetrics(
                system_metrics=self.metrics.get('system', {}),
                database_metrics=self.metrics.get('database', {}),
                performance_metrics=self.metrics.get('performance', {}),
                alerts=self.alerts
            )
            
            db.session.add(metrics_record)
            db.session.commit()
            
            logger.info(f"Metrics logged: {len(self.metrics)} categories")
            
        except Exception as e:
            logger.error(f"Error logging metrics: {e}")
    
    def get_health_status(self) -> Dict:
        """Obtiene el estado de salud general del sistema"""
        try:
            # Recopilar todas las métricas
            self.collect_system_metrics()
            self.collect_database_metrics()
            self.collect_performance_metrics()
            
            # Verificar alertas
            alerts = self.check_alerts()
            
            # Determinar estado general
            critical_alerts = [a for a in alerts if a['severity'] == 'critical']
            warning_alerts = [a for a in alerts if a['severity'] == 'warning']
            
            if critical_alerts:
                status = 'critical'
            elif warning_alerts:
                status = 'warning'
            else:
                status = 'healthy'
            
            health_status = {
                'status': status,
                'timestamp': datetime.utcnow().isoformat(),
                'metrics': self.metrics,
                'alerts': alerts,
                'summary': {
                    'total_alerts': len(alerts),
                    'critical_alerts': len(critical_alerts),
                    'warning_alerts': len(warning_alerts)
                }
            }
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def cleanup_old_metrics(self, days: int = 30):
        """Limpia métricas antiguas"""
        try:
            from crunevo.models import SystemMetrics
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            old_metrics = SystemMetrics.query.filter(
                SystemMetrics.timestamp < cutoff_date
            ).delete()
            
            db.session.commit()
            logger.info(f"Cleaned up {old_metrics} old metric records")
            
        except Exception as e:
            logger.error(f"Error cleaning up old metrics: {e}")

# Instancia global del monitor
monitor = CRUNEVOMonitor()

def get_system_health():
    """Función helper para obtener el estado de salud del sistema"""
    return monitor.get_health_status()

def log_performance_metric(operation: str, duration: float, success: bool = True):
    """Registra una métrica de rendimiento específica"""
    try:
        from crunevo.models import PerformanceMetric
        
        metric = PerformanceMetric(
            operation=operation,
            duration=duration,
            success=success,
            timestamp=datetime.utcnow()
        )
        
        db.session.add(metric)
        db.session.commit()
        
    except Exception as e:
        logger.error(f"Error logging performance metric: {e}")

def monitor_request_time():
    """Decorator para monitorear el tiempo de request"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = f(*args, **kwargs)
                duration = time.time() - start_time
                log_performance_metric(f.__name__, duration, True)
                return result
            except Exception as e:
                duration = time.time() - start_time
                log_performance_metric(f.__name__, duration, False)
                raise e
        return wrapper
    return decorator 