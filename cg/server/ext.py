from decimal import Decimal
from json import JSONEncoder

from flask_admin import Admin
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect

from cg.apps.lims import LimsAPI
from cg.apps.tb.api import TrailblazerAPI
from cg.clients.freshdesk.freshdesk_client import FreshdeskClient
from cg.server.app_config import app_config
from cg.services.delivery_message.delivery_message_service import DeliveryMessageService
from cg.services.orders.order_service.order_service import OrderService
from cg.services.orders.order_summary_service.order_summary_service import OrderSummaryService
from cg.services.orders.storing.service_registry import (
    StoringServiceRegistry,
    setup_storing_service_registry,
)
from cg.services.orders.submitter.ticket_handler import TicketHandler
from cg.services.orders.validation.service import OrderValidationService
from cg.services.run_devices.pacbio.sequencing_runs_service import PacbioSequencingRunsService
from cg.services.sample_run_metrics_service.sample_run_metrics_service import (
    SampleRunMetricsService,
)
from cg.services.web_services.application.service import ApplicationsWebService
from cg.services.web_services.case.service import CaseWebService
from cg.services.web_services.sample.service import SampleService
from cg.store.database import initialize_database
from cg.store.store import Store
from cg.server.app_config import app_config


class FlaskLims(LimsAPI):
    def __init__(self, app=None):
        if app:
            self.init_app(app)

    def init_app(self, app):
        config = {
            "lims": {
                "host": app_config.lims_host,
                "username": app_config.lims_username,
                "password": app_config.lims_password,
            }
        }
        super(FlaskLims, self).__init__(config)


class FlaskStore(Store):
    def __init__(self, app=None):
        if app:
            self.init_app(app)

    def init_app(self, app):
        uri = app_config.cg_sql_database_uri
        initialize_database(uri)
        super(FlaskStore, self).__init__()


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


class AnalysisClient(TrailblazerAPI):
    def __init__(self, app=None):
        if app:
            self.init_app(app)

    def init_app(self, app):
        config = {
            "trailblazer": {
                "service_account": app_config.trailblazer_service_account,
                "service_account_auth_file": app_config.trailblazer_service_account_auth_file,
                "host": app_config.trailblazer_host,
            }
        }
        super(AnalysisClient, self).__init__(config)


cors = CORS(resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
csrf = CSRFProtect()
db = FlaskStore()

admin = Admin(name="Clinical Genomics")
lims = FlaskLims()
applications_service = ApplicationsWebService(store=db)
analysis_client = AnalysisClient()
delivery_message_service = DeliveryMessageService(store=db, trailblazer_api=analysis_client)
summary_service = OrderSummaryService(store=db, analysis_client=analysis_client)
case_service = CaseWebService(store=db)
order_service = OrderService(store=db, status_service=summary_service)
pacbio_sequencing_runs_service = PacbioSequencingRunsService(db)
sample_service = SampleService(db)
sample_run_metrics_service = SampleRunMetricsService(db)
storing_service_registry: StoringServiceRegistry = setup_storing_service_registry(
    lims=lims,
    status_db=db,
)

order_validation_service = OrderValidationService(store=db)
freshdesk_client = FreshdeskClient(
    base_url=app_config.freshdesk_url, api_key=app_config.freshdesk_api_key
)
ticket_handler = TicketHandler(
    db=db,
    client=freshdesk_client,
    system_email_id=app_config.freshdesk_order_email_id,
    env=app_config.freshdesk_environment,
)
