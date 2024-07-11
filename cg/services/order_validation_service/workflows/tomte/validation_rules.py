from cg.services.order_validation_service.validators.inter_field_validators import (
    validate_ticket_number_required_if_connected,
)


TOMTE_VALIDATION_RULES = [validate_ticket_number_required_if_connected]
