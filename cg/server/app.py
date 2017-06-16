# -*- coding: utf-8 -*-
from flask import Flask

from . import ext
from .blueprints import public, api


def create_app(config):
    """Create Flask app."""
    app = Flask(__name__)
    app.config.from_object(config)

    # configure extensions
    ext.db.init_app(app)
    ext.cors.init_app(app)

    # register blueprints
    app.register_blueprint(public.blueprint)
    app.register_blueprint(api.blueprint)

    return app
