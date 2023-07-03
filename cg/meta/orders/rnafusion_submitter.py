from typing import List

from cg.exc import OrderError
from cg.meta.orders.case_submitter import CaseSubmitter
from cg.models.orders.order import OrderIn
from cg.models.orders.samples import Of1508Sample


class RnafusionSubmitter(CaseSubmitter):
    def validate_order(self, order: OrderIn) -> None:
        """Validates that the order is correct."""
        CaseSubmitter.validate_order(self=self, order=order)
        self._validate_one_sample_per_case(order.samples)

    @staticmethod
    def _validate_one_sample_per_case(samples: List[Of1508Sample]) -> None:
        """Validates that all samples have a unique case."""
        if len({sample.family_name for sample in samples}) != len(samples):
            raise OrderError("RNAFUSION orders only accept one sample per case.")
