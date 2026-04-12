#!/usr/bin/env python3
"""Local entrypoint for running the Flask app without Gunicorn."""

from __future__ import annotations

import os

from webapp import app


def _as_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


if __name__ == "__main__":
    host = os.getenv("APP_HOST", "127.0.0.1")
    port = int(os.getenv("APP_PORT", "5001"))
    debug = _as_bool(os.getenv("APP_DEBUG", "0"), default=False)

    app.config["TEMPLATES_AUTO_RELOAD"] = debug
    app.run(debug=debug, host=host, port=port)
