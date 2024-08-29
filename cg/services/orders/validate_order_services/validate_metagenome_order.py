from cg.exc import OrderError
from cg.models.orders.order import OrderIn
from cg.models.orders.samples import MetagenomeSample
from cg.services.orders.submitters.order_submitter import ValidateOrderService
from cg.store.models import Customer
from cg.store.store import Store


class ValidateMetagenomeOrderService(ValidateOrderService):

    def __init__(self, status_db: Store):
        self.status_db = status_db

    def validate_order(self, order: OrderIn) -> None:
        self._validate_sample_names_are_unique(samples=order.samples, customer_id=order.customer)

    def _validate_sample_names_are_unique(
        self, samples: list[MetagenomeSample], customer_id: str
    ) -> None:
        """Validate that the names of all samples are unused."""
        customer: Customer = self.status_db.get_customer_by_internal_id(
            customer_internal_id=customer_id
        )
        for sample in samples:
            if sample.control:
                continue
            if self.status_db.get_sample_by_customer_and_name(
                customer_entry_id=[customer.id], sample_name=sample.name
            ):
                raise OrderError(f"Sample name {sample.name} already in use")
