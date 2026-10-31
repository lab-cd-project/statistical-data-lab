"""Application factory: cada novo projeto registra seu próprio Blueprint."""

import os
from pathlib import Path

from flask import Flask


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        DATA_PATH=os.getenv(
            "NBA_DATA_PATH",
            str(Path(__file__).resolve().parents[2] / "stats_times_regular_final.xlsx"),
        ),
        MAX_CONTENT_LENGTH=1024 * 1024,
    )
    if config:
        app.config.update(config)
    from .project1 import bp

    app.register_blueprint(bp)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
