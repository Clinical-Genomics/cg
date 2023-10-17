import logging

from cg.store.api.delete import DeleteDataHandler
from cg.store.api.find_business_data import FindBusinessDataHandler
from cg.store.database import get_scoped_session_registry

from .add import AddHandler
from .find_basic_data import FindBasicDataHandler
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

    def __init__(self, session):
        DeleteDataHandler(session)
        FindBasicDataHandler(session)
        FindBusinessDataHandler(session)
        StatusHandler(session)


class Store(CoreHandler):
    def __init__(self):
        self._session = get_scoped_session_registry()
        super().__init__(self.session)

    @property
    def session(self):
        return self._session()
