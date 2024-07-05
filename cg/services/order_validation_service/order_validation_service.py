from workflows.tomte.validation_service import TomteOrderValidationService


class OrderValidationService:
    """Service to orchestrate the order validation."""

    def __init__(self, tomte_service: TomteOrderValidationService):
        self.tomte_service = tomte_service
