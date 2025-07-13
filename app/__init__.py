from flask import Flask
from app.config import load_configurations, configure_logging
from .extensions import db, migrate
from .views import webhook_blueprint

def create_app():
    app = Flask(__name__)

    load_configurations(app)
    configure_logging()

    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(webhook_blueprint)
    with app.app_context():
        from . import models

    return app