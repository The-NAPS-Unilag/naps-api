from flask import Flask
from flask_cors import CORS
from app.extensions import db, ma, migrate, jwt, mail
from app.routes.user_routes import user_bp
from app.routes.api_auth_routes import auth_bp
from app.routes.admin_routes import admin_bp
from app.routes.hello import hello_bp
from app.routes.event_routes import event_bp
from app.routes.resource_routes import resource_bp
from app.routes.forum_routes import forum_bp
from app.routes.mentorship import mentorship_bp
from app.routes.feedback_routes import feedback_bp

from app.socketio import socketio

import os

def create_app(config_class='app.config.Development'):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Configure CORS - use environment variable for allowed origins
    # In production, set CORS_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"
    cors_origins = os.getenv('CORS_ORIGINS', '*')
    if cors_origins != '*':
        cors_origins = [origin.strip() for origin in cors_origins.split(',')]
    
    CORS(app)

    #from models import api_key, event, user
    db.init_app(app)
    ma.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)

    app.register_blueprint(hello_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(event_bp)
    app.register_blueprint(resource_bp)
    app.register_blueprint(forum_bp)
    app.register_blueprint(mentorship_bp)
    app.register_blueprint(feedback_bp)

    socketio.init_app(app, cors_allowed_origins="*")
    return app
