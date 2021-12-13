from cg.meta.orders.sars_cov_2_submitter import SarsCov2Submitter
from cg.models.orders.constants import OrderType
from cg.models.orders.order import OrderIn
from cg.models.orders.sample_base import ControlEnum
from cg.models.orders.samples import SarsCov2Sample
from cg.store import Store


def test_order_to_status_control_exists(sarscov2_order_to_submit: dict, base_store: Store):

    # GIVEN sarscov2 order with three samples
    order: OrderIn = OrderIn.parse_obj(sarscov2_order_to_submit, OrderType.SARS_COV_2)

    # WHEN transforming order to status structure
    result: dict = SarsCov2Submitter.order_to_status(order=order)

    # THEN check that control is in the result
    sample: dict
    for sample in result.get("samples"):
        assert "control" in sample


def test_order_to_status_control_has_input_value(sarscov2_order_to_submit: dict, base_store: Store):

    # GIVEN sarscov2 order with three samples with control value set
    control_value = ControlEnum.positive
    order: OrderIn = OrderIn.parse_obj(sarscov2_order_to_submit, OrderType.SARS_COV_2)
    sample: SarsCov2Sample
    for sample in order.samples:
        sample.control: ControlEnum = control_value

    # WHEN transforming order to status structure
    result: dict = SarsCov2Submitter.order_to_status(order=order)

    # THEN check that control is in the result
    sample: dict
    for sample in result.get("samples"):
        assert control_value in sample.get("control")
