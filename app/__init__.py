from flask import Flask
from kubernetes import client, config
from app.extensions import db, scheduler
from config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    scheduler.init_app(app)
    scheduler.start()

    # Initialize Kubernetes client
    config.load_kube_config()
    app.v1 = client.BatchV1Api()
    app.metrics_api = client.CustomObjectsApi()

    # Register blueprints
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    # Create database tables
    with app.app_context():
        db.create_all()

    return app
