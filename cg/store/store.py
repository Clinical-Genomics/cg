import logging

from sqlalchemy.orm import Session

from cg.store.crud.create import CreateHandler
from cg.store.crud.delete import DeleteDataHandler
from cg.store.crud.read import ReadHandler
from cg.store.crud.update import UpdateHandler
from cg.store.database import get_session

LOG = logging.getLogger(__name__)


class Store(
    CreateHandler,
    DeleteDataHandler,
    ReadHandler,
    UpdateHandler,
):
    def __init__(self):
        self.session: Session = get_session()
        DeleteDataHandler(self.session)
        ReadHandler(self.session)
        UpdateHandler(self.session)

    def commit_to_store(self):
        """Commit pending changes to the store."""
        self.session.commit()
