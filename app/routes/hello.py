from flask import Blueprint, render_template_string, jsonify
from datetime import datetime
from app.extensions import db

hello_bp = Blueprint('hello_bp', __name__)

@hello_bp.route('/', methods=['GET'])
def hello_devs():
    message = (
        '<p>Hello, developers! All routes start with /api.</p>'
    )
    return render_template_string(message)

@hello_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for container orchestration and monitoring.
    Returns the health status of the application and database connectivity.
    """
    try:
        # Check database connectivity
        db.session.execute(db.text('SELECT 1'))
        db_status = 'healthy'
    except Exception as e:
        db_status = f'unhealthy: {str(e)}'
    
    health_status = {
        'status': 'healthy' if db_status == 'healthy' else 'degraded',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'naps-api',
        'database': db_status
    }
    
    status_code = 200 if db_status == 'healthy' else 503
    return jsonify(health_status), status_code
