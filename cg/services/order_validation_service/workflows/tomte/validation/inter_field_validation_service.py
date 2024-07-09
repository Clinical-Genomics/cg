from cg.services.order_validation_service.models.validation_error import ValidationErrors
from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder


class TomteInterFieldValidationService:

    def validate(self, order: TomteOrder) -> ValidationErrors:
        pass
