from decimal import Decimal

from flask.json import JSONEncoder
from flask_admin import Admin
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect

from cg.apps.lims import LimsAPI
from cg.apps.osticket import OsTicket
from cg.store.api.core import Store


class FlaskLims(LimsAPI):
    def __init__(self, app=None):
        if app:
            self.init_app(app)

    def init_app(self, app):
        config = {
            "lims": {
                "host": app.config["LIMS_HOST"],
                "username": app.config["LIMS_USERNAME"],
                "password": app.config["LIMS_PASSWORD"],
            }
        }
        super(FlaskLims, self).__init__(config)


class FlaskStore(Store):
    def __init__(self, app=None):
        if app:
            self.init_app(app)

    def init_app(self, app):
        uri = app.config["SQLALCHEMY_DATABASE_URI"]
        super(FlaskStore, self).__init__(uri)


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


cors = CORS(resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
csrf = CSRFProtect()
db = FlaskStore()

admin = Admin(name="Clinical Genomics")
lims = FlaskLims()
osticket = OsTicket()
