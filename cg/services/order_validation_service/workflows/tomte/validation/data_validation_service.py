from cg.services.order_validation_service.models.validation_error import ValidationErrors
from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder
from cg.store.store import Store


class TomteDataValidationService:
    def __init__(self, store: Store) -> None:
        self.store = store

    def validate(self, order: TomteOrder) -> ValidationErrors:
        pass
