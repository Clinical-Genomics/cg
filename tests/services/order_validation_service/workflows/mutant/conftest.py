"""Fixtures for testing specific conditions in Mutant orders."""

from datetime import datetime

import pytest

from cg.models.orders.constants import OrderType
from cg.models.orders.sample_base import ContainerEnum, ControlEnum, PriorityEnum
from cg.services.order_validation_service.constants import (
    MINIMUM_VOLUME,
    ElutionBuffer,
    ExtractionMethod,
)
from cg.services.order_validation_service.workflows.mutant.constants import (
    MutantDeliveryType,
    OriginalLab,
    PreProcessingMethod,
    Primer,
    Region,
    SelectionCriteria,
)
from cg.services.order_validation_service.workflows.mutant.models.order import MutantOrder
from cg.services.order_validation_service.workflows.mutant.models.sample import MutantSample


def create_sample(id: int, control: ControlEnum) -> MutantSample:
    return MutantSample(
        name=f"name{id}",
        application="VWGDPTR001",
        collection_date=datetime.now().date(),
        container=ContainerEnum.plate,
        container_name="ContainerName",
        control=control,
        elution_buffer=ElutionBuffer.WATER,
        extraction_method=ExtractionMethod.MAGNAPURE_96,
        organism="other",
        original_lab=OriginalLab.UNILABS_STOCKHOLM,
        pre_processing_method=PreProcessingMethod.OTHER,
        primer=Primer.ILLUMINA,
        priority=PriorityEnum.research,
        quantity=3,
        reference_genome="NC_000001",
        region=Region.STOCKHOLM,
        selection_criteria=SelectionCriteria.ALLMAN_OVERVAKNING,
        well_position=f"A:{id}",
        volume=MINIMUM_VOLUME,
    )


def create_order(samples: list[MutantSample]) -> MutantOrder:
    return MutantOrder(
        customer="cust000",
        delivery_type=MutantDeliveryType.FASTQ_ANALYSIS,
        name="mutant_order",
        project_type=OrderType.SARS_COV_2,
        samples=samples,
        user_id=1,
    )


@pytest.fixture
def mutant_order_control_sample_same_name() -> MutantOrder:
    sample1 = create_sample(1, ControlEnum.not_control)
    sample2 = create_sample(2, ControlEnum.not_control)
    sample3 = create_sample(3, ControlEnum.positive)
    sample3.name = sample1.name
    return create_order([sample1, sample2, sample3])


@pytest.fixture
def mutant_order_with_samples_with_same_name() -> MutantOrder:
    sample1 = create_sample(1, ControlEnum.not_control)
    sample2 = create_sample(2, ControlEnum.not_control)
    sample3 = create_sample(3, ControlEnum.positive)
    sample2.name = sample1.name
    sample3.name = sample1.name
    return create_order([sample1, sample2, sample3])
