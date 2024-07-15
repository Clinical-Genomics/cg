from cg.services.order_validation_service.models.validation_error import (
    ValidationError,
    ValidationErrors,
)


def _create_order_error(message: str, field: str) -> ValidationErrors:
    error: ValidationError = _create_error(field=field, message=message)
    return _create_errors(error)


def _create_errors(error: ValidationError) -> ValidationErrors:
    return ValidationErrors(errors=[error])


def _create_error(field: str, message: str) -> ValidationError:
    return ValidationError(field=field, message=message)
