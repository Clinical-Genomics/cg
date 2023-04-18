from flask_admin import Admin
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect

from cg.apps.lims import LimsAPI
from cg.apps.osticket import OsTicket
from cg.store import api, models


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
csrf = CSRFProtect()

session_factory = sessionmaker(autocommit=False, autoflush=False)
db_session = scoped_session(session_factory)
db = api.CoreHandler(session=db_session)

admin = Admin(name="Clinical Genomics")
lims = FlaskLims()
osticket = OsTicket()
