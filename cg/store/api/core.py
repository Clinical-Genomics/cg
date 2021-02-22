import logging

import alchy
from cg.store import models
from cg.store.api.findbusinessdata import FindBusinessDataHandler
from cg.store.api.reset import ResetHandler

from .add import AddHandler
from .findbasicdata import FindBasicDataHandler
from .status import StatusHandler

LOG = logging.getLogger(__name__)


class CoreHandler(
    AddHandler,
    FindBasicDataHandler,
    FindBusinessDataHandler,
    ResetHandler,
    StatusHandler,
):
    """Aggregating class for the store api handlers"""

    pass


class Store(alchy.Manager, CoreHandler):
    def __init__(self, config_dict: dict):
        self.uri = config_dict["database"]
        super(Store, self).__init__(
            config=dict(SQLALCHEMY_DATABASE_URI=self.uri), Model=models.Model
        )
