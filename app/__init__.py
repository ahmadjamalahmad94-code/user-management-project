from .logging_config import configure_logging

configure_logging()

from .legacy import app as app


def register_internal_blueprints(flask_app):
    if "health.healthz" not in flask_app.view_functions:
        from .health import health_bp

        flask_app.register_blueprint(health_bp)
    if "dashboard" not in flask_app.view_functions:
        # Dashboard blueprint not used — legacy app already provides /dashboard
        pass


def create_app():
    """Application factory — returns the configured Flask app."""
    register_internal_blueprints(app)
    return app


register_internal_blueprints(app)
