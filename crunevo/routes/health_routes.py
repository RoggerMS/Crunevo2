from flask import Blueprint, jsonify
from crunevo.extensions import db

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    """Health check endpoint for Fly.io"""
    try:
        # Verificar conexión a base de datos
        db.session.execute('SELECT 1')
        db_status = 'healthy'
    except Exception as e:
        db_status = f'unhealthy: {str(e)}'
    
    return jsonify({
        'status': 'ok',
        'database': db_status,
        'timestamp': '2025-07-29T05:00:00Z'
    })

@health_bp.route('/healthz')
def healthz():
    """Simple health check endpoint"""
    return "ok", 200

@health_bp.route('/ping')
def ping():
    """Simple ping endpoint"""
    return "pong", 200

@health_bp.route('/')
def root():
    """Root endpoint for basic connectivity test"""
    return "CRUNEVO is running", 200
