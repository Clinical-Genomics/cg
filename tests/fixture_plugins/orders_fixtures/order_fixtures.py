"""Fixtures for orders parsed into their respective models."""

import pytest

from cg.services.orders.validation.models.existing_sample import ExistingSample
from cg.services.orders.validation.workflows.balsamic.models.order import BalsamicOrder
from cg.services.orders.validation.workflows.fastq.models.order import FastqOrder
from cg.services.orders.validation.workflows.fluffy.models.order import FluffyOrder
from cg.services.orders.validation.workflows.metagenome.models.order import MetagenomeOrder
from cg.services.orders.validation.workflows.microbial_fastq.models.order import MicrobialFastqOrder
from cg.services.orders.validation.workflows.microsalt.models.order import MicrosaltOrder
from cg.services.orders.validation.workflows.mip_dna.models.order import MipDnaOrder
from cg.services.orders.validation.workflows.mip_rna.models.order import MipRnaOrder
from cg.services.orders.validation.workflows.mutant.models.order import MutantOrder
from cg.services.orders.validation.workflows.pacbio_long_read.models.order import PacbioOrder
from cg.services.orders.validation.workflows.rml.models.order import RmlOrder
from cg.services.orders.validation.workflows.rna_fusion.models.order import RnaFusionOrder
from cg.services.orders.validation.workflows.taxprofiler.models.order import TaxprofilerOrder
from cg.services.orders.validation.workflows.tomte.models.order import TomteOrder


@pytest.fixture
def balsamic_order(balsamic_order_to_submit: dict) -> BalsamicOrder:
    balsamic_order_to_submit["user_id"] = 1
    balsamic_order = BalsamicOrder.model_validate(balsamic_order_to_submit)
    balsamic_order._generated_ticket_id = 123456
    for case_index, sample_index, sample in balsamic_order.enumerated_new_samples:
        sample._generated_lims_id = f"ACC{case_index}-{sample_index}"
    return balsamic_order


@pytest.fixture
def fastq_order(fastq_order_to_submit: dict) -> FastqOrder:
    fastq_order = FastqOrder.model_validate(fastq_order_to_submit)
    fastq_order._generated_ticket_id = 123456
    return fastq_order


@pytest.fixture
def fluffy_order(fluffy_order_to_submit: dict, ticket_id_as_int: int) -> FluffyOrder:
    """Parse Fluffy order example."""
    fluffy_order = FluffyOrder.model_validate(fluffy_order_to_submit)
    fluffy_order._generated_ticket_id = ticket_id_as_int
    return fluffy_order


@pytest.fixture
def metagenome_order(
    metagenome_order_to_submit: dict,
    ticket_id_as_int: int,
) -> MetagenomeOrder:
    """Parse metagenome order example."""
    order = MetagenomeOrder.model_validate(metagenome_order_to_submit)
    order._generated_ticket_id = ticket_id_as_int
    return order


@pytest.fixture
def microbial_fastq_order(
    microbial_fastq_order_to_submit: dict, ticket_id_as_int: int
) -> MicrobialFastqOrder:
    order = MicrobialFastqOrder.model_validate(microbial_fastq_order_to_submit)
    order._generated_ticket_id = ticket_id_as_int
    return order


@pytest.fixture
def microsalt_order(microbial_order_to_submit: dict) -> MicrosaltOrder:
    order = MicrosaltOrder.model_validate(microbial_order_to_submit)
    order._generated_ticket_id = 123456
    return order


@pytest.fixture
def mip_dna_order(mip_dna_order_to_submit: dict) -> MipDnaOrder:
    mip_dna_order_to_submit["user_id"] = 1
    mip_dna_order = MipDnaOrder.model_validate(mip_dna_order_to_submit)
    for case_index, sample_index, sample in mip_dna_order.enumerated_new_samples:
        sample._generated_lims_id = f"ACC{case_index}-{sample_index}"
    mip_dna_order._generated_ticket_id = 123456
    return mip_dna_order


@pytest.fixture
def mip_rna_order(mip_rna_order_to_submit: dict) -> MipRnaOrder:
    mip_rna_order_to_submit["user_id"] = 1
    mip_rna_order = MipRnaOrder.model_validate(mip_rna_order_to_submit)
    for case_index, sample_index, sample in mip_rna_order.enumerated_new_samples:
        sample._generated_lims_id = f"ACC{case_index}-{sample_index}"
    mip_rna_order._generated_ticket_id = 123456
    return mip_rna_order


@pytest.fixture
def mutant_order(sarscov2_order_to_submit: dict, ticket_id_as_int: int) -> MutantOrder:
    """Parse mutant order example."""
    order = MutantOrder.model_validate(sarscov2_order_to_submit)
    order._generated_ticket_id = ticket_id_as_int
    return order


@pytest.fixture
def pacbio_order(pacbio_order_to_submit: dict, ticket_id_as_int: int) -> PacbioOrder:
    order = PacbioOrder.model_validate(pacbio_order_to_submit)
    order._generated_ticket_id = ticket_id_as_int
    return order


@pytest.fixture
def rml_order(rml_order_to_submit: dict, ticket_id_as_int: int) -> RmlOrder:
    """Parse rml order example."""
    rml_order = RmlOrder.model_validate(rml_order_to_submit)
    rml_order._generated_ticket_id = ticket_id_as_int
    return rml_order


@pytest.fixture
def rnafusion_order(rnafusion_order_to_submit: dict) -> RnaFusionOrder:
    """Parse RNAFusion order example."""
    rnafusion_order = RnaFusionOrder.model_validate(rnafusion_order_to_submit)
    rnafusion_order._generated_ticket_id = 123456
    return rnafusion_order


@pytest.fixture
def taxprofiler_order(taxprofiler_order_to_submit: dict, ticket_id_as_int: int) -> TaxprofilerOrder:
    """Parse Taxprofiler order example."""
    taxprofiler_order = TaxprofilerOrder.model_validate(taxprofiler_order_to_submit)
    taxprofiler_order._generated_ticket_id = ticket_id_as_int
    return taxprofiler_order


@pytest.fixture
def tomte_order(tomte_order_to_submit: dict, ticket_id_as_int: int) -> TomteOrder:
    """Parse Tomte order example."""
    tomte_order = TomteOrder.model_validate(tomte_order_to_submit)
    tomte_order._generated_ticket_id = ticket_id_as_int
    return tomte_order


@pytest.fixture
def mip_dna_order_with_existing_samples(mip_dna_order_to_submit: dict) -> MipDnaOrder:
    """Returns a MIP DNA order containing an existing sample."""
    mip_dna_order_to_submit["user_id"] = 1
    mip_dna_order_with_existing_samples = MipDnaOrder.model_validate(mip_dna_order_to_submit)
    mip_dna_order_with_existing_samples.cases[0].samples.append(
        ExistingSample(internal_id="ACC1234")
    )
    return mip_dna_order_with_existing_samples


@pytest.fixture
def mip_dna_order_with_only_existing_samples(mip_dna_order_to_submit: dict) -> MipDnaOrder:
    """Returns a MIP DNA order containing only existing samples."""
    mip_dna_order_to_submit["user_id"] = 1
    mip_dna_order_with_only_existing_samples = MipDnaOrder.model_validate(mip_dna_order_to_submit)
    for case in mip_dna_order_with_only_existing_samples.cases:
        case.samples = [ExistingSample(internal_id="ACC1234")]
    return mip_dna_order_with_only_existing_samples
