from flask import Flask
from app.config import Development, Staging, Production
from app.extensions import db, ma, migrate, jwt
from app.routes.user_routes import user_bp
from app.routes.api_routes import auth_bp
from decouple import config


def create_app(config_class='app.config.Development'):
    app = Flask(__name__)

    app.config.from_object(config_class)

    db.init_app(app)
    ma.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api')
    return app
