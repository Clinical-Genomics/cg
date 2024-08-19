from pydantic_core import ValidationError

from cg.services.order_validation_service.models.errors import ValidationErrors


def convert_errors(pydantic_errors: ValidationError) -> ValidationErrors:
    pass
