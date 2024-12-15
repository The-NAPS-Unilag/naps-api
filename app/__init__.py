from flask import Flask
from app.config import Development, Staging, Production
from app.extensions import db, ma, migrate
from app.routes.user_routes import user_bp
from decouple import config


def create_app():
    app = Flask(__name__)

    environment = config('FLASK_ENV', default='development').lower()

    if environment == 'production':
        app.config.from_object(Production)
    elif environment == 'staging':
        app.config.from_object(Staging)
    else:  # defaults to development
        app.config.from_object(Development)

    db.init_app(app)
    ma.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(user_bp, url_prefix='/api')

    return app
