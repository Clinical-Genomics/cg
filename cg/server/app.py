# -*- coding: utf-8 -*-
import coloredlogs
from flask import Flask
from flask_admin.contrib.sqla import ModelView
from flask_admin.base import AdminIndexView
import requests

from cg.store import models
from . import api, ext, admin


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

    certs_resp = requests.get('https://www.googleapis.com/oauth2/v1/certs')
    app.config['GOOGLE_OAUTH_CERTS'] = certs_resp.json()

    ext.cors.init_app(app)
    ext.db.init_app(app)
    ext.lims.init_app(app)
    ext.osticket.init_app(app)
    ext.admin.init_app(app, index_view=AdminIndexView(endpoint='admin',
                                                      url=f"/{app.config['SECRET_KEY']}"))


def register_blueprints(app):
    app.register_blueprint(api.blueprint)


def register_admin_views():
    ext.admin.add_view(admin.CustomerView(models.Customer, ext.db.session))
    ext.admin.add_view(admin.UserView(models.User, ext.db.session))
    ext.admin.add_view(admin.FamilyView(models.Family, ext.db.session))
    ext.admin.add_view(admin.SampleView(models.Sample, ext.db.session))
    ext.admin.add_view(admin.FamilySampleView(models.FamilySample, ext.db.session))
    ext.admin.add_view(ModelView(models.Flowcell, ext.db.session))
    ext.admin.add_view(ModelView(models.Analysis, ext.db.session))
    ext.admin.add_view(admin.ApplicationView(models.Application, ext.db.session))
    ext.admin.add_view(admin.ApplicationVersionView(models.ApplicationVersion, ext.db.session))
    ext.admin.add_view(admin.PanelView(models.Panel, ext.db.session))
