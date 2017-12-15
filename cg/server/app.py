# -*- coding: utf-8 -*-
import coloredlogs
from flask import Flask, redirect, url_for, session
from flask_admin.base import AdminIndexView
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer import oauth_authorized
import requests

from cg.store import models
from . import api, ext, admin, invoices


def create_app():
    """Generate a flask application."""
    app = Flask(__name__, template_folder='templates')

    # load config
    app.config.from_object(__name__.replace('app', 'config'))

    configure_extensions(app)

    register_blueprints(app)

    return app


def configure_extensions(app: Flask):
    # initialize logging
    coloredlogs.install(level='DEBUG' if app.debug else 'INFO')

    certs_resp = requests.get('https://www.googleapis.com/oauth2/v1/certs')
    app.config['GOOGLE_OAUTH_CERTS'] = certs_resp.json()

    ext.cors.init_app(app)
    ext.db.init_app(app)
    ext.lims.init_app(app)
    if app.config['OSTICKET_API_KEY']:
        ext.osticket.init_app(app)
    ext.admin.init_app(app, index_view=AdminIndexView(endpoint='admin'))


def register_blueprints(app: Flask):

    if not app.config['CG_ENABLE_ADMIN']:
        return

    oauth_bp = make_google_blueprint(
        client_id=app.config['GOOGLE_OAUTH_CLIENT_ID'],
        client_secret=app.config['GOOGLE_OAUTH_CLIENT_SECRET'],
        scope=['email', 'profile'],
    )

    @oauth_authorized.connect_via(oauth_bp)
    def logged_in(blueprint, token):
        """Called when the user logs in via Google OAuth."""
        resp = google.get('/oauth2/v1/userinfo?alt=json')
        assert resp.ok, resp.text
        user_data = resp.json()
        session['user_email'] = user_data['email']
        session['user_name'] = user_data['name']

    app.register_blueprint(api.BLUEPRINT)
    register_admin_views()
    app.register_blueprint(invoices.BLUEPRINT, url_prefix='/invoices')

    app.register_blueprint(oauth_bp, url_prefix='/login')

    @app.route('/')
    def index():
        return redirect(url_for('admin.index'))

    @app.route('/logout')
    def logout():
        """Log out the user."""
        session['user_email'] = None
        return redirect(url_for('index'))


def register_admin_views():
    ext.admin.add_view(admin.CustomerView(models.Customer, ext.db.session))
    ext.admin.add_view(admin.UserView(models.User, ext.db.session))
    ext.admin.add_view(admin.FamilyView(models.Family, ext.db.session))
    ext.admin.add_view(admin.FamilySampleView(models.FamilySample, ext.db.session))
    ext.admin.add_view(admin.SampleView(models.Sample, ext.db.session))
    ext.admin.add_view(admin.BaseView(models.Pool, ext.db.session))
    ext.admin.add_view(admin.FlowcellView(models.Flowcell, ext.db.session))
    ext.admin.add_view(admin.AnalysisView(models.Analysis, ext.db.session))
    ext.admin.add_view(admin.ApplicationView(models.Application, ext.db.session))
    ext.admin.add_view(admin.ApplicationVersionView(models.ApplicationVersion, ext.db.session))
    ext.admin.add_view(admin.BaseView(models.Delivery, ext.db.session))
    ext.admin.add_view(admin.PanelView(models.Panel, ext.db.session))
    ext.admin.add_view(admin.InvoiceView(models.Invoice, ext.db.session))
    ext.admin.add_view(admin.OrderView(models.Order, ext.db.session))
    ext.admin.add_view(admin.MicrobialSampleView(models.MicrobialSample, ext.db.session))
