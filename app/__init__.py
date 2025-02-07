from flask import Flask
from flask_cors import CORS
from app.config import Development, Staging, Production
from app.extensions import db, ma, migrate, jwt, mail
from app.routes.user_routes import user_bp
from app.routes.api_auth_routes import auth_bp
from app.routes.admin_routes import admin_bp
from app.routes.hello import hello_bp
from flask_swagger_ui import get_swaggerui_blueprint


def create_app(config_class='app.config.Development'):
    app = Flask(__name__)
    CORS(app)
    app.config.from_object(config_class)

    db.init_app(app)
    ma.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)

    app.register_blueprint(hello_bp)
    app.register_blueprint(admin_bp, url_prefix='/api')
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api')

    # swagger setup
    SWAGGER_URL = '/api/docs'
    API_URL = '/static/swagger.yaml'
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': "NAPS API"
        }
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    return app
