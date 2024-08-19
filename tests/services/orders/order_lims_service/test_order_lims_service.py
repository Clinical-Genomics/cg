import pytest

from cg.constants import Workflow
from cg.services.orders.order_lims_service.order_lims_service import OrderLimsService
from cg.models.lims.sample import LimsSample
from cg.models.orders.constants import OrderType
from cg.models.orders.order import OrderIn


def test_to_lims_mip(mip_order_to_submit):
    # GIVEN a scout order for a trio
    order_data = OrderIn.parse_obj(obj=mip_order_to_submit, project=OrderType.MIP_DNA)
    # WHEN parsing the order to format for LIMS import
    samples: list[LimsSample] = OrderLimsService._build_lims_sample(
        customer="cust003", samples=order_data.samples
    )

    # THEN it should list all samples
    assert len(samples) == 4

    # THEN container should be 96 well plate for all samples
    assert {sample.container for sample in samples} == {"96 well plate"}

    # THEN container names should be the same for all samples
    container_names = {sample.container_name for sample in samples if sample.container_name}
    assert container_names == {"CMMS"}

    # ... and pick out relevant UDFs
    first_sample: LimsSample = samples[0]
    assert first_sample.well_position == "A:1"
    assert first_sample.udfs.family_name == "family1"
    assert first_sample.udfs.priority == "standard"
    assert first_sample.udfs.application == "WGSPCFC030"
    assert first_sample.udfs.source == "tissue (fresh frozen)"
    assert first_sample.udfs.quantity == "220"
    assert first_sample.udfs.customer == "cust003"
    assert first_sample.udfs.volume == "1.0"

    # THEN assert that the comment of a sample is a string
    assert isinstance(samples[1].udfs.comment, str)


def test_to_lims_fastq(fastq_order_to_submit):
    # GIVEN a fastq order for two samples; normal vs. tumour
    order_data = OrderIn.parse_obj(obj=fastq_order_to_submit, project=OrderType.FASTQ)

    # WHEN parsing the order to format for LIMS
    samples: list[LimsSample] = OrderLimsService._build_lims_sample(
        customer="dummyCust", samples=order_data.samples
    )

    # THEN should "work"
    assert len(samples) == 2
    normal_sample = samples[0]
    tumor_sample = samples[1]
    # ... and pick out relevant UDF values
    assert normal_sample.udfs.tumour is False
    assert tumor_sample.udfs.tumour is True
    assert normal_sample.udfs.volume == "1"


def test_to_lims_rml(rml_order_to_submit):
    # GIVEN a rml order for four samples
    order_data = OrderIn.parse_obj(obj=rml_order_to_submit, project=OrderType.RML)

    # WHEN parsing for LIMS
    samples: list[LimsSample] = OrderLimsService._build_lims_sample(
        customer="dummyCust", samples=order_data.samples
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


def test_to_lims_microbial(microbial_order_to_submit):
    # GIVEN a microbial order for three samples
    order_data = OrderIn.parse_obj(obj=microbial_order_to_submit, project=OrderType.MICROSALT)

    # WHEN parsing for LIMS
    samples: list[LimsSample] = OrderLimsService._build_lims_sample(
        customer="cust000", samples=order_data.samples
    )
    # THEN it should "work"

    assert len(samples) == 5
    # ... and pick out relevant UDFs
    first_sample = samples[0].dict()
    assert first_sample["udfs"]["priority"] == "research"
    assert first_sample["udfs"]["organism"] == "M.upium"
    assert first_sample["udfs"]["reference_genome"] == "NC_111"
    assert (
        first_sample["udfs"]["extraction_method"] == "MagNaPure 96 (contact Clinical Genomics "
        "before submission)"
    )
    assert first_sample["udfs"]["volume"] == "1"


def test_to_lims_sarscov2(sarscov2_order_to_submit):
    # GIVEN a sarscov2 order for samples
    order_data = OrderIn.parse_obj(obj=sarscov2_order_to_submit, project=OrderType.SARS_COV_2)

    # WHEN parsing for LIMS
    samples: list[LimsSample] = OrderLimsService._build_lims_sample(
        customer="cust000", samples=order_data.samples
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


@pytest.mark.parametrize(
    "project", [OrderType.BALSAMIC, OrderType.BALSAMIC_UMI, OrderType.BALSAMIC_QC]
)
def test_to_lims_balsamic(balsamic_order_to_submit, project):
    # GIVEN a cancer order for a sample
    order_data = OrderIn.parse_obj(obj=balsamic_order_to_submit, project=project)

    # WHEN parsing the order to format for LIMS import
    samples: list[LimsSample] = OrderLimsService._build_lims_sample(
        customer="cust000", samples=order_data.samples
    )
    # THEN it should list all samples

    assert len(samples) == 1
    # ... and determine the container, container name, and well position

    container_names = {sample.container_name for sample in samples if sample.container_name}

    # ... and pick out relevant UDFs
    first_sample = samples[0].dict()
    assert first_sample["name"] == "s1"
    assert {sample.container for sample in samples} == set(["96 well plate"])
    assert first_sample["udfs"]["data_analysis"] in [
        Workflow.BALSAMIC,
        Workflow.BALSAMIC_QC,
        Workflow.BALSAMIC_UMI,
    ]
    assert first_sample["udfs"]["application"] == "WGSPCFC030"
    assert first_sample["udfs"]["sex"] == "M"
    assert first_sample["udfs"]["family_name"] == "family1"
    assert first_sample["udfs"]["customer"] == "cust000"
    assert first_sample["udfs"]["source"] == "blood"
    assert first_sample["udfs"]["volume"] == "1.0"
    assert first_sample["udfs"]["priority"] == "standard"

    assert container_names == set(["p1"])
    assert first_sample["well_position"] == "A:1"
    assert first_sample["udfs"]["tumour"] is True
    assert first_sample["udfs"]["capture_kit"] == "other"
    assert first_sample["udfs"]["tumour_purity"] == "75"

    assert first_sample["udfs"]["formalin_fixation_time"] == "1"
    assert first_sample["udfs"]["post_formalin_fixation_time"] == "2"
    assert first_sample["udfs"]["tissue_block_size"] == "small"

    assert first_sample["udfs"]["quantity"] == "2"
    assert first_sample["udfs"]["comment"] == "other Elution buffer"
