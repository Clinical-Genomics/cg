"""Fixtures for orders parsed into their respective models."""

import pytest

from cg.services.orders.validation.models.existing_sample import ExistingSample
from cg.services.orders.validation.order_types.balsamic.models.order import BalsamicOrder
from cg.services.orders.validation.order_types.fastq.models.order import FastqOrder
from cg.services.orders.validation.order_types.fluffy.models.order import FluffyOrder
from cg.services.orders.validation.order_types.metagenome.models.order import MetagenomeOrder
from cg.services.orders.validation.order_types.microbial_fastq.models.order import (
    MicrobialFastqOrder,
)
from cg.services.orders.validation.order_types.microsalt.models.order import MicrosaltOrder
from cg.services.orders.validation.order_types.mip_dna.models.order import MIPDNAOrder
from cg.services.orders.validation.order_types.mip_rna.models.order import MIPRNAOrder
from cg.services.orders.validation.order_types.mutant.models.order import MutantOrder
from cg.services.orders.validation.order_types.nallo.models.order import NalloOrder
from cg.services.orders.validation.order_types.pacbio_long_read.models.order import PacbioOrder
from cg.services.orders.validation.order_types.raredisease.models.order import RarediseaseOrder
from cg.services.orders.validation.order_types.rml.models.order import RMLOrder
from cg.services.orders.validation.order_types.rna_fusion.models.order import RNAFusionOrder
from cg.services.orders.validation.order_types.taxprofiler.models.order import TaxprofilerOrder
from cg.services.orders.validation.order_types.tomte.models.order import TomteOrder


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
def mip_dna_order(mip_dna_order_to_submit: dict) -> MIPDNAOrder:
    mip_dna_order_to_submit["user_id"] = 1
    mip_dna_order = MIPDNAOrder.model_validate(mip_dna_order_to_submit)
    for case_index, sample_index, sample in mip_dna_order.enumerated_new_samples:
        sample._generated_lims_id = f"ACC{case_index}-{sample_index}"
    mip_dna_order._generated_ticket_id = 123456
    return mip_dna_order


@pytest.fixture
def mip_rna_order(mip_rna_order_to_submit: dict) -> MIPRNAOrder:
    mip_rna_order_to_submit["user_id"] = 1
    mip_rna_order = MIPRNAOrder.model_validate(mip_rna_order_to_submit)
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
def raredisease_order(raredisease_order_to_submit: dict, ticket_id_as_int: int) -> RarediseaseOrder:
    """Parse Raredisease order example."""
    raredisease_order = RarediseaseOrder.model_validate(raredisease_order_to_submit)
    raredisease_order._generated_ticket_id = ticket_id_as_int
    return raredisease_order


@pytest.fixture
def rml_order(rml_order_to_submit: dict, ticket_id_as_int: int) -> RMLOrder:
    """Parse rml order example."""
    rml_order = RMLOrder.model_validate(rml_order_to_submit)
    rml_order._generated_ticket_id = ticket_id_as_int
    return rml_order


@pytest.fixture
def rnafusion_order(rnafusion_order_to_submit: dict) -> RNAFusionOrder:
    """Parse RNAFusion order example."""
    rnafusion_order = RNAFusionOrder.model_validate(rnafusion_order_to_submit)
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
def mip_dna_order_with_existing_samples(mip_dna_order_to_submit: dict) -> MIPDNAOrder:
    """Returns a MIP DNA order containing an existing sample."""
    mip_dna_order_to_submit["user_id"] = 1
    mip_dna_order_with_existing_samples = MIPDNAOrder.model_validate(mip_dna_order_to_submit)
    mip_dna_order_with_existing_samples.cases[0].samples.append(
        ExistingSample(internal_id="ACC1234")
    )
    return mip_dna_order_with_existing_samples


@pytest.fixture
def mip_dna_order_with_only_existing_samples(mip_dna_order_to_submit: dict) -> MIPDNAOrder:
    """Returns a MIP DNA order containing only existing samples."""
    mip_dna_order_to_submit["user_id"] = 1
    mip_dna_order_with_only_existing_samples = MIPDNAOrder.model_validate(mip_dna_order_to_submit)
    for case in mip_dna_order_with_only_existing_samples.cases:
        case.samples = [ExistingSample(internal_id="ACC1234")]
    return mip_dna_order_with_only_existing_samples


@pytest.fixture
def nallo_order(nallo_order_to_submit: dict, ticket_id_as_int: int) -> NalloOrder:
    nallo_order_to_submit["user_id"] = 1
    nallo_order = NalloOrder.model_validate(nallo_order_to_submit)
    for case_index, sample_index, sample in nallo_order.enumerated_new_samples:
        sample._generated_lims_id = f"ACC{case_index}-{sample_index}"
    nallo_order._generated_ticket_id = ticket_id_as_int
    return nallo_order
