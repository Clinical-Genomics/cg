import coloredlogs
import requests
from flask import Flask, redirect, session, url_for
from flask_admin.base import AdminIndexView
from flask_dance.consumer import oauth_authorized
from flask_dance.contrib.google import google, make_google_blueprint
from sqlalchemy.orm import scoped_session

from cg.server import admin, ext, invoices
from cg.server.app_config import app_config
from cg.server.endpoints.analyses import ANALYSES_BLUEPRINT
from cg.server.endpoints.applications import APPLICATIONS_BLUEPRINT
from cg.server.endpoints.cases import CASES_BLUEPRINT
from cg.server.endpoints.flow_cells.flow_cells import FLOW_CELLS_BLUEPRINT
from cg.server.endpoints.orders import ORDERS_BLUEPRINT
from cg.server.endpoints.pools import POOLS_BLUEPRINT
from cg.server.endpoints.samples import SAMPLES_BLUEPRINT
from cg.server.endpoints.users import USERS_BLUEPRINT
from cg.store.database import get_scoped_session_registry
from cg.store.models import (
    Analysis,
    Application,
    ApplicationLimitations,
    ApplicationVersion,
    Bed,
    BedVersion,
    Case,
    CaseSample,
    Collaboration,
    Customer,
    IlluminaSampleSequencingMetrics,
    IlluminaSequencingRun,
    Invoice,
    Order,
    Organism,
    PacbioSampleSequencingMetrics,
    PacbioSequencingRun,
    Panel,
    Pool,
    Sample,
    User,
)


def create_app():
    """Generate a flask application."""
    app = Flask(__name__, template_folder="templates")
    _load_config(app)
    _configure_extensions(app)
    _register_blueprints(app)
    _register_teardowns(app)

    return app


def _load_config(app: Flask):
    app.config.update(app_config.dict())
    app.secret_key = app.config["cg_secret_key"]


def _configure_extensions(app: Flask):
    _initialize_logging(app)
    certs_resp = requests.get("https://www.googleapis.com/oauth2/v1/certs")
    app.config["GOOGLE_OAUTH_CERTS"] = certs_resp.json()

    ext.cors.init_app(app)
    ext.csrf.init_app(app)
    ext.db.init_app(app)
    ext.lims.init_app(app)
    ext.analysis_client.init_app(app)
    ext.admin.init_app(app, index_view=AdminIndexView(endpoint="admin"))
    app.json_provider_class = ext.CustomJSONEncoder


def _initialize_logging(app):
    coloredlogs.install(level="DEBUG" if app.debug else "INFO")


def _register_blueprints(app: Flask):
    oauth_bp = make_google_blueprint(
        client_id=app.config["google_oauth_client_id"],
        client_secret=app.config["google_oauth_client_secret"],
        scope=["openid", "https://www.googleapis.com/auth/userinfo.email"],
    )

    @oauth_authorized.connect_via(oauth_bp)
    def logged_in(blueprint, token):
        """Called when the user logs in via Google OAuth."""
        resp = google.get("/oauth2/v1/userinfo?alt=json")
        assert resp.ok, resp.text
        user_data = resp.json()
        session["user_email"] = user_data["email"]

    app.register_blueprint(invoices.BLUEPRINT, url_prefix="/invoices")
    app.register_blueprint(oauth_bp, url_prefix="/login")
    app.register_blueprint(APPLICATIONS_BLUEPRINT)
    app.register_blueprint(CASES_BLUEPRINT)
    app.register_blueprint(ORDERS_BLUEPRINT)
    app.register_blueprint(SAMPLES_BLUEPRINT)
    app.register_blueprint(POOLS_BLUEPRINT)
    app.register_blueprint(FLOW_CELLS_BLUEPRINT)
    app.register_blueprint(ANALYSES_BLUEPRINT)
    app.register_blueprint(USERS_BLUEPRINT)
    _register_admin_views()

    ext.csrf.exempt(SAMPLES_BLUEPRINT)
    ext.csrf.exempt(CASES_BLUEPRINT)
    ext.csrf.exempt(APPLICATIONS_BLUEPRINT)
    ext.csrf.exempt(ORDERS_BLUEPRINT)
    ext.csrf.exempt(POOLS_BLUEPRINT)
    ext.csrf.exempt(FLOW_CELLS_BLUEPRINT)
    ext.csrf.exempt(ANALYSES_BLUEPRINT)
    ext.csrf.exempt(USERS_BLUEPRINT)

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
    ext.admin.add_view(admin.ApplicationLimitationsView(ApplicationLimitations, ext.db.session))
    ext.admin.add_view(admin.BedView(Bed, ext.db.session))
    ext.admin.add_view(admin.BedVersionView(BedVersion, ext.db.session))
    ext.admin.add_view(admin.CustomerView(Customer, ext.db.session))
    ext.admin.add_view(admin.CollaborationView(Collaboration, ext.db.session))
    ext.admin.add_view(admin.OrganismView(Organism, ext.db.session))
    ext.admin.add_view(admin.OrderView(Order, ext.db.session))
    ext.admin.add_view(admin.PanelView(Panel, ext.db.session))
    ext.admin.add_view(admin.UserView(User, ext.db.session))

    # Business data views
    ext.admin.add_view(admin.CaseView(Case, ext.db.session))
    ext.admin.add_view(admin.CaseSampleView(CaseSample, ext.db.session))
    ext.admin.add_view(admin.SampleView(Sample, ext.db.session))
    ext.admin.add_view(admin.PoolView(Pool, ext.db.session))
    ext.admin.add_view(admin.AnalysisView(Analysis, ext.db.session))
    ext.admin.add_view(admin.InvoiceView(Invoice, ext.db.session))
    ext.admin.add_view(
        admin.IlluminaFlowCellView(IlluminaSequencingRun, ext.db.session, name="Illumina Flow Cell")
    )
    ext.admin.add_view(
        admin.IlluminaSampleSequencingMetricsView(IlluminaSampleSequencingMetrics, ext.db.session)
    )
    ext.admin.add_view(admin.PacbioSmrtCellView(PacbioSequencingRun, ext.db.session))
    ext.admin.add_view(
        admin.PacbioSampleRunMetricsView(PacbioSampleSequencingMetrics, ext.db.session)
    )


def _register_teardowns(app: Flask):
    """Register teardown functions."""

    @app.teardown_appcontext
    def remove_database_session(exception=None):
        """
        Remove the database session to ensure database resources are
        released when a request has been processed.
        """
        scoped_session_registry: scoped_session | None = get_scoped_session_registry()
        if scoped_session_registry:
            scoped_session_registry.remove()
