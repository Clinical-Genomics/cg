import logging

from cg.store.api.find_basic_data import FindBasicDataHandler
from cg.store.api.find_business_data import FindBusinessDataHandler
from cg.store.api.status import StatusHandler
from cg.store.crud.create import CreateHandler
from cg.store.crud.delete import DeleteDataHandler
from cg.store.crud.update import UpdateHandler
from cg.store.database import get_session

LOG = logging.getLogger(__name__)


class CoreHandler(
    CreateHandler,
    DeleteDataHandler,
    FindBasicDataHandler,
    FindBusinessDataHandler,
    StatusHandler,
    UpdateHandler,
):
    """Aggregating class for the store api handlers."""

    def __init__(self, session):
        DeleteDataHandler(session)
        FindBasicDataHandler(session)
        FindBusinessDataHandler(session)
        StatusHandler(session)
        UpdateHandler(session)


class Store(CoreHandler):
    def __init__(self):
        self.session = get_session()
