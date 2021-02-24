import logging
from pathlib import Path
from typing import Dict, List, Optional

from cg.exc import OrderError, OrderFormError
from cg.models.orders.orderform_schema import OrderCase, Orderform, OrderPool
from cg.models.orders.sample_base import OrderSample

LOG = logging.getLogger(__name__)


class OrderformParser:
    """Class to parse orderforms"""

    def __init__(self):
        self.samples: List[OrderSample] = []
        self.project_type: Optional[str] = None
        self.delivery_type: Optional[str] = None
        self.customer_id: Optional[str] = None
        self.order_comment: Optional[str] = None
        self.order_name: Optional[str] = None

    def parse_orderform(self, orderform_file: Path) -> None:
        """Parse the orderform information"""
        raise NotImplementedError

    def group_cases(self) -> Dict[str, List[OrderSample]]:
        """Group samples in cases."""
        LOG.info("Group samples under respective case")
        cases = {}
        for sample in self.samples:
            case_id = sample.case_id
            if not case_id:
                continue
            if case_id not in cases:
                cases[case_id] = []
            cases[case_id].append(sample)
        if cases:
            LOG.info("Found cases %s", ", ".join(cases.keys()))
        else:
            LOG.info("Could not find any cases")
        return cases

    def get_pools(self) -> List[OrderPool]:
        """create pools from samples

        Check that all samples from one pool has the same application
        """
        pools: Dict[str, OrderPool] = {}
        sample: OrderSample
        for sample in self.samples:
            pool_name = sample.pool
            if not pool_name:
                continue
            application = sample.application
            if pool_name not in pools:
                pools[pool_name] = OrderPool(
                    name=pool_name,
                    data_analysis=sample.data_analysis,
                    data_delivery=sample.data_delivery,
                    application=application,
                    samples=[sample],
                )
                continue
            # each pool must only have one application type
            pool = pools[pool_name]
            if str(pool.application) != application:
                raise OrderError(
                    f"different application in pool: {pool_name} - {[pools[pool_name].application, application]}"
                )
            pool.samples.append(sample)

        return [pools[pool_name] for pool_name in pools]

    def expand_case(self, case_id: str, case_samples: List[OrderSample]) -> OrderCase:
        """Fill-in information about case."""

        priorities = {sample.priority for sample in case_samples if sample.priority}
        if len(priorities) != 1:
            raise OrderFormError(f"multiple values for 'Priority' for case: {case_id}")

        gene_panels = set()
        for sample in case_samples:
            if not sample.panels:
                continue
            gene_panels.update(set(sample.panels))

        return OrderCase(
            name=case_id,
            samples=case_samples,
            require_qcok=any(sample.require_qcok for sample in case_samples),
            priority=priorities.pop(),
            panels=list(gene_panels),
        )

    def generate_orderform(self) -> Orderform:
        """Generate an orderform"""
        cases_map: Dict[str, List[OrderSample]] = self.group_cases()
        case_objs: List[OrderCase] = []
        for case_id in cases_map:
            case_objs.append(self.expand_case(case_id=case_id, case_samples=cases_map[case_id]))
        return Orderform(
            comment=self.order_comment,
            samples=self.samples,
            cases=case_objs,
            name=self.order_name,
            customer=self.customer_id,
            delivery_type=self.delivery_type,
            project_type=self.project_type,
            pools=self.get_pools(),
        )

    def __repr__(self):
        return (
            f"OrderformParser(project_type={self.project_type},delivery_type={self.delivery_type},customer_id="
            f"{self.customer_id},order_name={self.order_name})"
        )
