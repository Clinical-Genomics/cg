from cg.apps.tb import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.exc import OrderNotDeliverableError
from cg.server.dto.delivery_message.delivery_message_request import (
    DeliveryMessageRequest,
)
from cg.server.dto.delivery_message.delivery_message_response import (
    DeliveryMessageOrderResponse,
    DeliveryMessageResponse,
)
from cg.services.delivery_message.utils import get_message, validate_cases
from cg.store.models import Case, Order
from cg.store.store import Store


class DeliveryMessageService:
    def __init__(self, store: Store, trailblazer_api: TrailblazerAPI) -> None:
        self.store = store
        self.trailblazer_api = trailblazer_api

    def get_cases_message(
        self, delivery_message_request: DeliveryMessageRequest
    ) -> DeliveryMessageResponse:
        case_ids: list[str] = delivery_message_request.case_ids
        message: str = self._get_delivery_message(set(case_ids))
        return DeliveryMessageResponse(message=message)

    def get_order_message(self, order_id: int) -> DeliveryMessageOrderResponse:
        order: Order = self.store.get_order_by_id(order_id)
        analyses: list[TrailblazerAnalysis] = self.trailblazer_api.get_analyses_to_deliver(order_id)
        uploaded_analyses_with_matching_workflow = [
            analysis
            for analysis in analyses
            if analysis.uploaded_at and analysis.workflow == order.workflow
        ]
        if not uploaded_analyses_with_matching_workflow:
            raise OrderNotDeliverableError(
                f"No analyses ready to be delivered for order {order_id}"
            )
        case_ids: set[str] = {
            analysis.case_id for analysis in uploaded_analyses_with_matching_workflow
        }
        message: str = self._get_delivery_message(case_ids)
        analysis_ids: list[int] = [
            analysis.id for analysis in uploaded_analyses_with_matching_workflow
        ]
        return DeliveryMessageOrderResponse(message=message, analysis_ids=analysis_ids)

    def _get_delivery_message(self, case_ids: set[str]) -> str:
        cases: list[Case] = self.store.get_cases_by_internal_ids(case_ids)
        validate_cases(cases=cases, case_ids=case_ids)
        message: str = get_message(cases)
        return message
