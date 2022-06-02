import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Hashable, Iterable

from pydantic import constr, BaseModel

from cg.constants import DataDelivery
from cg.exc import OrderFormError
from cg.models.orders.order import OrderType
from cg.models.orders.orderform_schema import OrderCase, Orderform, OrderPool
from cg.models.orders.sample_base import OrderSample
from cg.store import models

LOG = logging.getLogger(__name__)


class OrderformParser(BaseModel):
    """Class to parse orderforms"""

    samples: List[OrderSample] = []
    project_type: Optional[OrderType] = None
    delivery_type: Optional[DataDelivery] = None
    customer_id: constr(
        min_length=1, max_length=models.Customer.internal_id.property.columns[0].type.length
    ) = None
    order_comment: Optional[str] = None
    order_name: Optional[str] = None

    class Config:
        validate_assignment = True

    def parse_orderform(self, orderform_file: Path) -> None:
        """Parse the orderform information"""
        raise NotImplementedError

    def group_cases(self) -> Dict[str, List[OrderSample]]:
        """Group samples in cases."""
        LOG.info("Group samples under respective case")
        cases = {}
        for sample in self.samples:
            case_id = sample.family_name
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
                raise OrderFormError(
                    f"different applications in pool: {pool_name} - {[pools[pool_name].application, application]}"
                )
            pool.samples.append(sample)

        return [pools[pool_name] for pool_name in pools]

    @staticmethod
    def _get_single_value(
        items_id: str, items: Iterable, attr: str, default_value: Hashable = None
    ) -> Hashable:
        """
        Get single value from a bunch of items, will raise if value not same on all items
        @param items_id:        id of items group (e.g. case-id)
        @param items:           some items (e.g. samples)
        @param attr:            one attribute of item containing a value (e.g. synopsis)
        @param default_value:   default value to use if item has an empty value of attr
        @return:                a value with the attribute of item in items
        """
        values: Set[Hashable] = set(getattr(item, attr, default_value) for item in items)
        if len(values) > 1:
            raise OrderFormError(f"multiple values [{values}] for '{attr}' for '{items_id}'")

        return values.pop()

    @staticmethod
    def _get_single_set(items_id: str, items: Iterable, attr: str) -> Set[Hashable]:
        """
        Get single value (set) from a bunch of items, will raise if value not same on all items
        @param items_id: id of items group (e.g. case-id)
        @param items:    some items (e.g. samples)
        @param attr:     one attribute of item containing a list (e.g. panels)
        @return:         a set with the attribute of item in items
        """
        values: Set[Hashable] = set()
        for item_idx, item in enumerate(items):
            if item_idx == 0:
                values = set(getattr(item, attr)) if getattr(item, attr) else set()
            elif values != set(getattr(item, attr)) if getattr(item, attr) else set():
                raise OrderFormError(f"multiple values [{values}] for '{attr}' for '{items_id}'")
        return values

    @staticmethod
    def expand_case(case_id: str, case_samples: List[OrderSample]) -> OrderCase:
        """Fill-in information about case."""

        priority: Hashable[str] = OrderformParser._get_single_value(
            items_id=case_id, items=case_samples, attr="priority"
        )
        synopsis: Hashable[str] = OrderformParser._get_single_value(
            items_id=case_id, items=case_samples, attr="synopsis"
        )
        cohorts: Set[Hashable[str]] = OrderformParser._get_single_set(
            items_id=case_id, items=case_samples, attr="cohorts"
        )
        panels: Set[Hashable[str]] = OrderformParser._get_single_set(
            items_id=case_id, items=case_samples, attr="panels"
        )

        return OrderCase(
            cohorts=list(cohorts),
            name=case_id,
            samples=case_samples,
            priority=priority,
            panels=list(panels),
            synopsis=synopsis,
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
