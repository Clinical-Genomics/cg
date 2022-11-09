import logging

import alchy

from cg.store import models
from cg.store.api.delete import DeleteDataHandler
from cg.store.api.findbusinessdata import FindBusinessDataHandler

from .add import AddHandler
from .findbasicdata import FindBasicDataHandler
from .status import StatusHandler

LOG = logging.getLogger(__name__)


class CoreHandler(
    AddHandler,
    DeleteDataHandler,
    FindBasicDataHandler,
    FindBusinessDataHandler,
    StatusHandler,
):
    """Aggregating class for the store api handlers."""

    pass


class Store(alchy.Manager, CoreHandler):
    def __init__(self, uri):
        self.uri = uri
        super(Store, self).__init__(config=dict(SQLALCHEMY_DATABASE_URI=uri), Model=models.Model)
