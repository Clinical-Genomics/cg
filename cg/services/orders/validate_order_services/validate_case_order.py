from cg.exc import OrderError
from cg.models.orders.constants import OrderType
from cg.models.orders.order import OrderIn
from cg.models.orders.samples import Of1508Sample, OrderInSample
from cg.services.orders.submitters.order_submitter import ValidateOrderService
from cg.store.models import Sample, Customer
from cg.store.store import Store


class ValidateCaseOrderService(ValidateOrderService):

    def __init__(self, status_db: Store):
        self.status_db = status_db

    def validate_order(self, order: OrderIn) -> None:
        self._validate_subject_sex(samples=order.samples, customer_id=order.customer)
        self._validate_samples_available_to_customer(
            samples=order.samples, customer_id=order.customer
        )
        self._validate_case_names_are_unique(samples=order.samples, customer_id=order.customer)
        if order.order_type == OrderType.RNAFUSION:
            self._validate_only_one_sample_per_case(samples=order.samples)

    def _validate_subject_sex(self, samples: [Of1508Sample], customer_id: str):
        """Validate that sex is consistent with existing samples, skips samples of unknown sex

        Args:
            samples     (list[dict]):   Samples to validate
            customer_id (str):          Customer that the samples belong to
        Returns:
            Nothing
        """
        sample: Of1508Sample
        for sample in samples:
            subject_id: str = sample.subject_id
            if not subject_id:
                continue
            new_gender: str = sample.sex
            if new_gender == "unknown":
                continue

            existing_samples: list[Sample] = self.status_db.get_samples_by_customer_and_subject_id(
                customer_internal_id=customer_id, subject_id=subject_id
            )
            existing_sample: Sample
            for existing_sample in existing_samples:
                previous_gender = existing_sample.sex
                if previous_gender == "unknown":
                    continue

                if previous_gender != new_gender:
                    raise OrderError(
                        f"Sample gender inconsistency for subject_id: {subject_id}: previous gender {previous_gender}, new gender {new_gender}"
                    )

    def _validate_samples_available_to_customer(
        self, samples: list[OrderInSample], customer_id: str
    ) -> None:
        """Validate that the customer have access to all samples"""
        sample: Of1508Sample
        for sample in samples:
            if not sample.internal_id:
                continue

            existing_sample: Sample = self.status_db.get_sample_by_internal_id(
                internal_id=sample.internal_id
            )

            data_customer: Customer = self.status_db.get_customer_by_internal_id(
                customer_internal_id=customer_id
            )

            if existing_sample.customer not in data_customer.collaborators:
                raise OrderError(f"Sample not available: {sample.name}")

    def _validate_case_names_are_unique(
        self, samples: list[OrderInSample], customer_id: str
    ) -> None:
        """Validate that the names of all cases are unused for all samples"""

        customer: Customer = self.status_db.get_customer_by_internal_id(
            customer_internal_id=customer_id
        )

        sample: Of1508Sample
        for sample in samples:
            if self._is_rerun_of_existing_case(sample=sample):
                continue
            if self.status_db.get_case_by_name_and_customer(
                customer=customer, case_name=sample.family_name
            ):
                raise OrderError(f"Case name {sample.family_name} already in use")

    @staticmethod
    def _is_rerun_of_existing_case(sample: Of1508Sample) -> bool:
        return sample.case_internal_id is not None

    @staticmethod
    def _validate_only_one_sample_per_case(samples: list[Of1508Sample]) -> None:
        """Validates that each case contains only one sample."""
        if len({sample.family_name for sample in samples}) != len(samples):
            raise OrderError("Each case in an RNAFUSION order must have exactly one sample.")
