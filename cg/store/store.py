"""Store class that combines all CRUD operations for the CG database."""

from cg.store.crud.create import CreateMixin
from cg.store.crud.delete import DeleteMixin
from cg.store.crud.update import UpdateMixin


class Store(
    CreateMixin,
    DeleteMixin,
    UpdateMixin,
):
    pass
