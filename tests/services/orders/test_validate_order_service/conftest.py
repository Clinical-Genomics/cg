import pytest

from cg.constants import DataDelivery, Workflow
from cg.models.orders.order import OrderIn
from cg.models.orders.sample_base import SexEnum
from cg.models.orders.samples import PacBioSample
from cg.services.orders.validate_order_services.validate_pacbio_order import (
    ValidatePacbioOrderService,
)
from cg.store.store import Store


@pytest.fixture
def pacbio_sample() -> PacBioSample:
    return PacBioSample(
        application="WGSPCFC060",
        data_analysis=Workflow.RAW_DATA,
        data_delivery=DataDelivery.NO_DELIVERY,
        name="PacbioSample",
        sex=SexEnum.unknown,
        tumour=False,
        volume="50",
        buffer="buffer",
        source="source",
        subject_id="subject_id",
        container="Tube",
    )


@pytest.fixture
def pacbio_order(pacbio_sample: PacBioSample) -> OrderIn:
    return OrderIn(
        customer="cust000",
        name="PacbioOrder",
        samples=[pacbio_sample],
    )


@pytest.fixture
def validate_pacbio_order_service(sample_store: Store) -> ValidatePacbioOrderService:
    return ValidatePacbioOrderService(sample_store)
