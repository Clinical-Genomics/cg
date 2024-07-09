from cg.services.order_validation_service.models.validation_error import ValidationErrors
from cg.services.order_validation_service.order_validation_service import OrderValidationService
from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder
from cg.services.order_validation_service.workflows.tomte.validation.data_validation_service import (
    TomteDataValidationService,
)
from cg.services.order_validation_service.workflows.tomte.validation.field_validation_service import (
    TomteFieldValidationService,
)
from cg.services.order_validation_service.workflows.tomte.validation.inter_field_validation_service import (
    TomteInterFieldValidationService,
)


class TomteValidationService(OrderValidationService):

    def __init__(
        self,
        field_validation_service: TomteFieldValidationService,
        inter_field_validation_service: TomteInterFieldValidationService,
        data_validation_service: TomteDataValidationService,
    ):
        self.field_service = field_validation_service
        self.inter_field_service = inter_field_validation_service
        self.data_service = data_validation_service

    def validate(self, order_json: str) -> ValidationErrors:
        order, field_errors = self.field_service.validate(order_json)
        inter_field_errors = self.inter_field_service.validate(order)
        data_errors = self.data_service.validate(order)

        return ValidationErrors(
            field_errors.errors + inter_field_errors.errors + data_errors.errors
        )
