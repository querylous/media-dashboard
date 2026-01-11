from flask import Flask
from app.routes.api import api
from app.routes.views import views


def create_app():
    app = Flask(__name__, static_folder="../static", static_url_path="/static")

    # Register blueprints
    app.register_blueprint(api)
    app.register_blueprint(views)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
