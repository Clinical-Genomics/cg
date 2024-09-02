from cg.exc import OrderError
from cg.meta.orders.case_submitter import CaseSubmitter
from cg.models.orders.order import OrderIn
from cg.models.orders.samples import Of1508Sample


class RnafusionSubmitter(CaseSubmitter):
    def validate_order(self, order: OrderIn) -> None:
        super().validate_order(order=order)
        self._validate_only_one_sample_per_case(order.samples)

    @staticmethod
    def _validate_only_one_sample_per_case(samples: list[Of1508Sample]) -> None:
        """Validates that each case contains only one sample."""
        if len({sample.family_name for sample in samples}) != len(samples):
            raise OrderError("Each case in an RNAFUSION order must have exactly one sample.")
