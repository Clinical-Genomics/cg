from decimal import Decimal
from json import JSONEncoder

from flask_admin import Admin
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect

from cg.apps.lims import LimsAPI
from cg.apps.osticket import OsTicket
from cg.apps.tb.api import TrailblazerAPI
from cg.services.delivery_message.delivery_message_service import DeliveryMessageService
from cg.services.orders.order_service.order_service import OrderService
from cg.services.orders.order_summary_service.order_summary_service import (
    OrderSummaryService,
)
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
osticket = OsTicket()
analysis_client = AnalysisClient()
delivery_message_service = DeliveryMessageService(store=db, trailblazer_api=analysis_client)
summary_service = OrderSummaryService(store=db, analysis_client=analysis_client)
order_service = OrderService(store=db, status_service=summary_service)
