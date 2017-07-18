# -*- coding: utf-8 -*-
import coloredlogs
from flask import Flask
from flask_admin.contrib.sqla import ModelView

from cg.store import models
from . import api, ext


def create_app():
    """Generate a flask application."""
    app = Flask(__name__)

    # load config
    app.config.from_object(__name__.replace('app', 'config'))

    configure_extensions(app)
    register_blueprints(app)

    if app.config['CG_ENABLE_ADMIN']:
        register_admin_views()

    return app


def configure_extensions(app):
    # initialize logging
    coloredlogs.install(level='DEBUG' if app.debug else 'INFO')

    ext.cors.init_app(app)
    ext.db.init_app(app)
    ext.admin.init_app(app)


def register_blueprints(app):
    app.register_blueprint(api.blueprint)


def register_admin_views():
    ext.admin.add_view(ModelView(models.Customer, ext.db.session))
    ext.admin.add_view(ModelView(models.User, ext.db.session))
    ext.admin.add_view(ModelView(models.FamilySample, ext.db.session))
    ext.admin.add_view(ModelView(models.Family, ext.db.session))
    ext.admin.add_view(ModelView(models.Sample, ext.db.session))
    ext.admin.add_view(ModelView(models.Flowcell, ext.db.session))
    ext.admin.add_view(ModelView(models.Analysis, ext.db.session))
    ext.admin.add_view(ModelView(models.Application, ext.db.session))
    ext.admin.add_view(ModelView(models.ApplicationVersion, ext.db.session))
    ext.admin.add_view(ModelView(models.Panel, ext.db.session))
