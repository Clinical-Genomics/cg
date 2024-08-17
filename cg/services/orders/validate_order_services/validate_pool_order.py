from cg.exc import OrderError
from cg.models.orders.order import OrderIn
from cg.models.orders.samples import RmlSample
from cg.services.orders.submitters.order_submitter import ValidateOrderService
from cg.store.models import Customer
from cg.store.store import Store


class ValidatePoolOrderService(ValidateOrderService):

    def __init__(self, status_db: Store):
        self.status_db = status_db

    def validate_order(self, order: OrderIn) -> None:
        self._validate_case_names_are_available(
            customer_id=order.customer, samples=order.samples, ticket=order.ticket
        )

    def _validate_case_names_are_available(
        self, customer_id: str, samples: list[RmlSample], ticket: str
    ):
        """Validate names of all samples are not already in use."""
        customer: Customer = self.status_db.get_customer_by_internal_id(
            customer_internal_id=customer_id
        )
        for sample in samples:
            case_name: str = self.create_case_name(pool_name=sample.pool, ticket=ticket)
            if self.status_db.get_case_by_name_and_customer(customer=customer, case_name=case_name):
                raise OrderError(
                    f"Case name {case_name} already in use for customer {customer.name}"
                )

    @staticmethod
    def create_case_name(ticket: str, pool_name: str) -> str:
        return f"{ticket}-{pool_name}"
