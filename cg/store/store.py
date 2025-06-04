import logging

from sqlalchemy.orm import Session

from cg.store.crud.create import CreateMixin
from cg.store.crud.delete import DeleteMixin
from cg.store.crud.update import UpdateMixin
from cg.store.database import get_session

LOG = logging.getLogger(__name__)


class Store(
    CreateMixin,
    DeleteMixin,
    UpdateMixin,
):
    def __init__(self):
        self.session: Session = get_session()
        super().__init__(session=self.session)
