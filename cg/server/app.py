import coloredlogs
import requests
from flask import Flask, redirect, session, url_for
from flask_admin.base import AdminIndexView
from flask_dance.consumer import oauth_authorized
from flask_dance.contrib.google import google, make_google_blueprint

from cg.store.models import (
    Analysis,
    Application,
    ApplicationVersion,
    Bed,
    BedVersion,
    Collaboration,
    Customer,
    Delivery,
    Family,
    FamilySample,
    Flowcell,
    Invoice,
    Organism,
    Panel,
    Pool,
    Sample,
    User,
    SampleLaneSequencingMetrics,
)

from . import admin, api, ext, invoices


def create_app():
    """Generate a flask application."""
    app = Flask(__name__, template_folder="templates")
    _load_config(app)
    _configure_extensions(app)
    _register_blueprints(app)
    _register_teardowns(app)

    return app


def _load_config(app):
    app.config.from_object(__name__.replace("app", "config"))


def _configure_extensions(app: Flask):
    _initialize_logging(app)
    certs_resp = requests.get("https://www.googleapis.com/oauth2/v1/certs")
    app.config["GOOGLE_OAUTH_CERTS"] = certs_resp.json()

    ext.cors.init_app(app)
    ext.csrf.init_app(app)
    ext.db.init_app(app)
    ext.lims.init_app(app)
    if app.config["OSTICKET_API_KEY"]:
        ext.osticket.init_app(app)
    ext.admin.init_app(app, index_view=AdminIndexView(endpoint="admin"))
    app.json_encoder = ext.CustomJSONEncoder


def _initialize_logging(app):
    coloredlogs.install(level="DEBUG" if app.debug else "INFO")


def _register_blueprints(app: Flask):
    if not app.config["CG_ENABLE_ADMIN"]:
        return

    oauth_bp = make_google_blueprint(
        client_id=app.config["GOOGLE_OAUTH_CLIENT_ID"],
        client_secret=app.config["GOOGLE_OAUTH_CLIENT_SECRET"],
        scope=["openid", "https://www.googleapis.com/auth/userinfo.email"],
    )

    @oauth_authorized.connect_via(oauth_bp)
    def logged_in(blueprint, token):
        """Called when the user logs in via Google OAuth."""
        resp = google.get("/oauth2/v1/userinfo?alt=json")
        assert resp.ok, resp.text
        user_data = resp.json()
        session["user_email"] = user_data["email"]

    app.register_blueprint(api.BLUEPRINT)
    app.register_blueprint(invoices.BLUEPRINT, url_prefix="/invoices")
    app.register_blueprint(oauth_bp, url_prefix="/login")
    _register_admin_views()

    ext.csrf.exempt(api.BLUEPRINT)  # Protected with Auth header already

    @app.route("/")
    def index():
        return redirect(url_for("admin.index"))

    @app.route("/logout")
    def logout():
        """Log out the user."""
        session["user_email"] = None
        return redirect(url_for("index"))


def _register_admin_views():
    # Base data views
    ext.admin.add_view(admin.ApplicationView(Application, ext.db.session))
    ext.admin.add_view(admin.ApplicationVersionView(ApplicationVersion, ext.db.session))
    ext.admin.add_view(admin.BedView(Bed, ext.db.session))
    ext.admin.add_view(admin.BedVersionView(BedVersion, ext.db.session))
    ext.admin.add_view(admin.CustomerView(Customer, ext.db.session))
    ext.admin.add_view(admin.CollaborationView(Collaboration, ext.db.session))
    ext.admin.add_view(admin.OrganismView(Organism, ext.db.session))
    ext.admin.add_view(admin.PanelView(Panel, ext.db.session))
    ext.admin.add_view(admin.UserView(User, ext.db.session))
    ext.admin.add_view(
        admin.SampleLaneSequencingMetricsView(SampleLaneSequencingMetrics, ext.db.session)
    )

    # Business data views
    ext.admin.add_view(admin.FamilyView(Family, ext.db.session))
    ext.admin.add_view(admin.FamilySampleView(FamilySample, ext.db.session))
    ext.admin.add_view(admin.SampleView(Sample, ext.db.session))
    ext.admin.add_view(admin.PoolView(Pool, ext.db.session))
    ext.admin.add_view(admin.FlowcellView(Flowcell, ext.db.session))
    ext.admin.add_view(admin.AnalysisView(Analysis, ext.db.session))
    ext.admin.add_view(admin.DeliveryView(Delivery, ext.db.session))
    ext.admin.add_view(admin.InvoiceView(Invoice, ext.db.session))


def _register_teardowns(app: Flask):
    """Register teardown functions."""

    @app.teardown_appcontext
    def remove_database_session(exception=None):
        ext.db.session.remove()
