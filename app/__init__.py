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


def create_app(config_class='app.config.Development'):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.url_map.strict_slashes = False

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": [
                    "http://localhost:5173",
                    "http://192.168.0.163:5173",
                    "http://localhost:5000",
                    "http://127.0.0.1:5000",
                    "http://127.0.0.1",
                    "http://127.0.0.1:5174",
                    "https://naps-web-ten.vercel.app/",
                    "https://admin-dashboard-mu-inky-66.vercel.app/",
                    "http://localhost:5174",
                ],
                "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization", "X-API-Key"],
                "supports_credentials": True,
            }
        },
    )
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
