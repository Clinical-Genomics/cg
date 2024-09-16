from cg.exc import OrderError
from cg.models.orders.order import OrderIn
from cg.models.orders.samples import PacBioSample
from cg.services.orders.submitters.order_submitter import ValidateOrderService
from cg.store.models import ApplicationVersion, Customer
from cg.store.store import Store


class ValidatePacbioOrderService(ValidateOrderService):

    def __init__(self, status_db: Store):
        self.status_db = status_db

    def validate_order(self, order: OrderIn) -> None:
        self._validate_customer_exists(order.customer)
        self._validate_applications_exist(order.samples)
        self._validate_sample_names_available(samples=order.samples, customer_id=order.customer)

    def _validate_customer_exists(self, customer_id: str) -> None:
        customer: Customer = self.status_db.get_customer_by_internal_id(
            customer_internal_id=customer_id
        )
        if not customer:
            raise OrderError(f"Unknown customer: {customer_id}")

    def _validate_applications_exist(self, samples: list[PacBioSample]) -> None:
        for sample in samples:
            application_tag = sample.application
            application_version: ApplicationVersion = (
                self.status_db.get_current_application_version_by_tag(tag=application_tag)
            )
            if application_version is None:
                raise OrderError(f"Invalid application: {sample.application}")

    def _validate_sample_names_available(
        self, samples: list[PacBioSample], customer_id: str
    ) -> None:
        customer: Customer = self.status_db.get_customer_by_internal_id(customer_id)
        for sample in samples:
            if self.status_db.get_sample_by_customer_and_name(
                customer_entry_id=[customer.id], sample_name=sample.name
            ):
                raise OrderError(
                    f"Sample name already used in a previous order by the same customer: {sample.name}"
                )
