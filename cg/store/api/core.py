import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from cg.store.models import Model
from cg.store.api.delete import DeleteDataHandler
from cg.store.api.find_business_data import FindBusinessDataHandler

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
        DeleteDataHandler.__init__(self, session)
        FindBasicDataHandler.__init__(self, session)
        FindBusinessDataHandler.__init__(self, session)
        StatusHandler.__init__(self, session)


class Store(CoreHandler):
    uri: str = ""

    def __init__(self, uri):
        self.uri = uri
        self.engine = create_engine(uri)
        session_factory = sessionmaker(bind=self.engine)
        self.session = session_factory()
        super(Store, self).__init__(self.session)

    def create_all(self):
        """Create all tables in the database."""
        Model.metadata.create_all(bind=self.session.get_bind())

    def drop_all(self):
        """Drop all tables in the database."""
        Model.metadata.drop_all(bind=self.session.get_bind())
