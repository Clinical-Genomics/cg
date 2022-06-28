from flask_admin import Admin
from flask_alchy import Alchy
from flask_cors import CORS

from cg.apps.lims import LimsAPI
from cg.apps.osticket import OsTicket
from cg.store import api, models


class CgAlchy(Alchy, api.CoreHandler):
    pass


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


cors = CORS(resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
db = CgAlchy(Model=models.Model)
admin = Admin(name="Clinical Genomics")
lims = FlaskLims()
osticket = OsTicket()
