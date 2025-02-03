import logging

from sqlalchemy.orm import Session

from cg.store.crud.create import CreateHandler
from cg.store.crud.delete import DeleteDataHandler
from cg.store.crud.read import ReadHandler
from cg.store.crud.update import UpdateHandler
from cg.store.database import get_session
from cg.store.models import Base as ModelBase

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

    def add_item_to_store(self, item: ModelBase):
        """Add an item to the store."""
        self.session.add(item)

    def add_multiple_items_to_store(self, items: list[ModelBase]):
        """Add multiple items to the store."""
        self.session.add_all(items)

    def no_autoflush_context(self):
        """Return a context manager that disables autoflush for the session."""
        return self.session.no_autoflush

    def rollback(self):
        """Rollback any pending change to the store."""
        self.session.rollback()
