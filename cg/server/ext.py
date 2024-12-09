from decimal import Decimal
from json import JSONEncoder

from flask_admin import Admin
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect

from cg.apps.lims import LimsAPI
from cg.apps.tb.api import TrailblazerAPI
from cg.clients.freshdesk.freshdesk_client import FreshdeskClient
from cg.meta.orders.ticket_handler import TicketHandler
from cg.server.app_config import app_config
from cg.services.application.service import ApplicationsWebService
from cg.services.delivery_message.delivery_message_service import DeliveryMessageService
from cg.services.order_validation_service.workflows.balsamic.validation_service import (
    BalsamicValidationService,
)
from cg.services.order_validation_service.workflows.balsamic_umi.validation_service import (
    BalsamicUmiValidationService,
)
from cg.services.order_validation_service.workflows.fastq.validation_service import (
    FastqValidationService,
)
from cg.services.order_validation_service.workflows.microbial_fastq.validation_service import (
    MicrobialFastqValidationService,
)
from cg.services.order_validation_service.workflows.microsalt.validation_service import (
    MicroSaltValidationService,
)
from cg.services.order_validation_service.workflows.mip_dna.validation_service import (
    MipDnaValidationService,
)
from cg.services.order_validation_service.workflows.mutant.validation_service import (
    MutantValidationService,
)
from cg.services.order_validation_service.workflows.pacbio_long_read.validation_service import (
    PacbioLongReadValidationService,
)
from cg.services.order_validation_service.workflows.rna_fusion.validation_service import (
    RnaFusionValidationService,
)
from cg.services.order_validation_service.workflows.tomte.validation_service import (
    TomteValidationService,
)
from cg.services.orders.order_service.order_service import OrderService
from cg.services.orders.order_summary_service.order_summary_service import OrderSummaryService
from cg.services.orders.submitters.order_submitter_registry import (
    OrderSubmitterRegistry,
    setup_order_submitter_registry,
)
from cg.services.sample_run_metrics_service.sample_run_metrics_service import (
    SampleRunMetricsService,
)
from cg.services.sample_service.sample_service import SampleService
from cg.store.database import initialize_database
from cg.store.store import Store


class FlaskLims(LimsAPI):
    def __init__(self, app=None):
        if app:
            self.init_app(app)

    def init_app(self, app):
        config = {
            "lims": {
                "host": app.config["lims_host"],
                "username": app.config["lims_username"],
                "password": app.config["lims_password"],
            }
        }
        super(FlaskLims, self).__init__(config)


class FlaskStore(Store):
    def __init__(self, app=None):
        if app:
            self.init_app(app)

    def init_app(self, app):
        uri = app.config["cg_sql_database_uri"]
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
        service_account: str = app.config["trailblazer_service_account"]
        service_account_auth_file: str = app.config["trailblazer_service_account_auth_file"]
        host: str = app.config["trailblazer_host"]
        config = {
            "trailblazer": {
                "service_account": service_account,
                "service_account_auth_file": service_account_auth_file,
                "host": host,
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
order_service = OrderService(store=db, status_service=summary_service)
sample_service = SampleService(db)
flow_cell_service = SampleRunMetricsService(db)
order_submitter_registry: OrderSubmitterRegistry = setup_order_submitter_registry(
    lims=lims,
    status_db=db,
)

balsamic_validation_service = BalsamicValidationService(store=db)
balsamic_umi_validation_service = BalsamicUmiValidationService(store=db)
fastq_validation_service = FastqValidationService(store=db)
microbial_fastq_validation_service = MicrobialFastqValidationService(store=db)
microsalt_validation_service = MicroSaltValidationService(store=db)
mip_dna_validation_service = MipDnaValidationService(store=db)
mutant_validation_service = MutantValidationService(store=db)
pacbio_long_read_validation_service = PacbioLongReadValidationService(store=db)
rna_fusion_validation_service = RnaFusionValidationService(store=db)
tomte_validation_service = TomteValidationService(store=db)

freshdesk_client = FreshdeskClient(
    base_url=app_config.freshdesk_url, api_key=app_config.freshdesk_api_key
)
ticket_handler = TicketHandler(
    db=db,
    client=freshdesk_client,
    system_email_id=app_config.freshdesk_order_email_id,
    env=app_config.freshdesk_environment,
)
