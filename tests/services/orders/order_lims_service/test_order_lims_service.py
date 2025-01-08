import pytest

from cg.constants import Workflow
from cg.models.lims.sample import LimsSample
from cg.services.order_validation_service.workflows.balsamic.models.order import BalsamicOrder
from cg.services.order_validation_service.workflows.fastq.models.order import FastqOrder
from cg.services.order_validation_service.workflows.microsalt.models.order import MicrosaltOrder
from cg.services.order_validation_service.workflows.mip_dna.models.order import MipDnaOrder
from cg.services.order_validation_service.workflows.mutant.models.order import MutantOrder
from cg.services.order_validation_service.workflows.rml.models.order import RmlOrder
from cg.services.orders.order_lims_service.order_lims_service import OrderLimsService


def test_to_lims_mip(mip_order_to_submit):
    # GIVEN a scout order for a trio
    order_data = MipDnaOrder.model_validate(mip_order_to_submit)
    # WHEN parsing the order to format for LIMS import
    new_samples = [sample for _, _, sample in order_data.enumerated_new_samples]
    samples: list[LimsSample] = OrderLimsService._build_lims_sample(
        customer="cust003",
        samples=new_samples,
        workflow=Workflow.MIP_DNA,
        delivery_type=order_data.delivery_type,
    )

    # THEN it should list all samples
    assert len(samples) == 4

    # THEN container should be 96 well plate for all samples
    assert {sample.container for sample in samples} == {"96 well plate"}

    # THEN container names should be the same for all samples
    container_names = {sample.container_name for sample in samples if sample.container_name}
    assert container_names == {"MipPlate"}

    # ... and pick out relevant UDFs
    first_sample: LimsSample = samples[0]
    assert first_sample.well_position == "A:1"
    assert first_sample.udfs.priority == "standard"
    assert first_sample.udfs.application == "WGSPCFC030"
    assert first_sample.udfs.source == "blood"
    assert first_sample.udfs.customer == "cust003"
    assert first_sample.udfs.volume == "54"

    # THEN assert that the comment of a sample is a string
    assert isinstance(samples[1].udfs.comment, str)


def test_to_lims_fastq(fastq_order_to_submit):
    # GIVEN a fastq order for two samples; normal vs. tumour
    order_data = FastqOrder.model_validate(fastq_order_to_submit)

    # WHEN parsing the order to format for LIMS
    samples: list[LimsSample] = OrderLimsService._build_lims_sample(
        customer="dummyCust",
        samples=order_data.samples,
        workflow=Workflow.RAW_DATA,
        delivery_type=order_data.delivery_type,
    )

    # THEN should "work"
    assert len(samples) == 2
    normal_sample = samples[0]
    tumour_sample = samples[1]
    # ... and pick out relevant UDF values
    assert normal_sample.udfs.tumour is False
    assert tumour_sample.udfs.tumour is True
    assert normal_sample.udfs.volume == "54"


@pytest.mark.xfail(reason="RML sample container validation not working")
def test_to_lims_fluffy(fluffy_order_to_submit: dict):
    # GIVEN a Fluffy order for four samples
    order_data = RmlOrder.model_validate(fluffy_order_to_submit)

    # WHEN parsing for LIMS
    samples: list[LimsSample] = OrderLimsService._build_lims_sample(
        customer="dummyCust",
        samples=order_data.samples,
        workflow=Workflow.RAW_DATA,
        delivery_type=order_data.delivery_type,
    )

    # THEN it should have found the same number of samples
    assert len(samples) == 4
    # ... and pick out relevant UDFs
    first_sample = samples[0]
    assert first_sample.udfs.pool == "pool-1"
    assert first_sample.udfs.volume == "30"
    assert first_sample.udfs.concentration == "5.0"
    assert first_sample.udfs.index == "IDT DupSeq 10 bp Set B"
    assert first_sample.udfs.index_number == "1"


def test_to_lims_microbial(microbial_order_to_submit: dict):
    # GIVEN a microbial order for three samples
    order_data = MicrosaltOrder.model_validate(microbial_order_to_submit)

    # WHEN parsing for LIMS
    samples: list[LimsSample] = OrderLimsService._build_lims_sample(
        customer="cust000",
        samples=order_data.samples,
        workflow=Workflow.MICROSALT,
        delivery_type=order_data.delivery_type,
    )
    # THEN it should "work"

    assert len(samples) == 5
    # ... and pick out relevant UDFs
    first_sample = samples[0].dict()
    assert first_sample["udfs"]["priority"] == "research"
    assert first_sample["udfs"]["organism"] == "C. jejuni"
    assert first_sample["udfs"]["reference_genome"] == "NC_000001"
    assert first_sample["udfs"]["extraction_method"] == "MagNaPure 96"
    assert first_sample["udfs"]["volume"] == "20"


@pytest.mark.xfail(reason="Mutant extraction methods need a new enum")
def test_to_lims_sarscov2(sarscov2_order_to_submit: dict):
    # GIVEN a sarscov2 order for samples
    order_data = MutantOrder.model_validate(sarscov2_order_to_submit)

    # WHEN parsing for LIMS
    samples: list[LimsSample] = OrderLimsService._build_lims_sample(
        customer="cust000",
        samples=order_data.samples,
        workflow=Workflow.MUTANT,
        delivery_type=order_data.delivery_type,
    )

    # THEN it should have found the same number of samples
    assert len(samples) == 6
    # ... and pick out relevant UDFs
    first_sample = samples[0].dict()
    assert first_sample["udfs"]["collection_date"] == "2021-05-05"
    assert first_sample["udfs"]["extraction_method"] == "MagNaPure 96"
    assert first_sample["udfs"]["lab_code"] == "SE100 Karolinska"
    assert first_sample["udfs"]["organism"] == "SARS CoV-2"
    assert first_sample["udfs"]["original_lab"] == "Karolinska University Hospital Solna"
    assert first_sample["udfs"]["original_lab_address"] == "171 76 Stockholm"
    assert first_sample["udfs"]["pre_processing_method"] == "COVIDSeq"
    assert first_sample["udfs"]["priority"] == "research"
    assert first_sample["udfs"]["reference_genome"] == "NC_111"
    assert first_sample["udfs"]["region"] == "Stockholm"
    assert first_sample["udfs"]["region_code"] == "01"
    assert first_sample["udfs"]["selection_criteria"] == "1. Allmän övervakning"
    assert first_sample["udfs"]["volume"] == "1"


def test_to_lims_balsamic(balsamic_order_to_submit: dict):
    # GIVEN a cancer order for a sample
    order_data = BalsamicOrder.model_validate(balsamic_order_to_submit)

    new_samples = [sample for _, _, sample in order_data.enumerated_new_samples]
    # WHEN parsing the order to format for LIMS import
    samples: list[LimsSample] = OrderLimsService._build_lims_sample(
        customer="cust000",
        samples=new_samples,
        workflow=Workflow.BALSAMIC,
        delivery_type=order_data.delivery_type,
    )
    # THEN it should list all samples

    assert len(samples) == 1
    # ... and determine the container, container name, and well position

    container_names = {sample.container_name for sample in samples if sample.container_name}

    # ... and pick out relevant UDFs
    first_sample = samples[0].dict()
    assert first_sample["name"] == "BalsamicSample"
    assert {sample.container for sample in samples} == set(["96 well plate"])
    assert first_sample["udfs"]["data_analysis"] == Workflow.BALSAMIC
    assert first_sample["udfs"]["application"] == "PANKTTR100"
    assert first_sample["udfs"]["sex"] == "M"
    assert first_sample["udfs"]["customer"] == "cust000"
    assert first_sample["udfs"]["source"] == "cytology (FFPE)"
    assert first_sample["udfs"]["volume"] == "42"
    assert first_sample["udfs"]["priority"] == "standard"

    assert container_names == set(["BalsamicPlate"])
    assert first_sample["well_position"] == "A:1"
    assert first_sample["udfs"]["tumour"] is True
    assert first_sample["udfs"]["capture_kit"] == "GMCKsolid"
    assert first_sample["udfs"]["tumour_purity"] == "13"

    assert first_sample["udfs"]["formalin_fixation_time"] == "15"
    assert first_sample["udfs"]["post_formalin_fixation_time"] == "3"
    assert first_sample["udfs"]["tissue_block_size"] == "large"

    assert first_sample["udfs"]["comment"] == "This is a sample comment"
