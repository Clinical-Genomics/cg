from cg.constants import Workflow
from cg.models.lims.sample import LimsSample
from cg.services.orders.lims_service.service import OrderLimsService
from cg.services.orders.validation.order_types.balsamic.models.order import BalsamicOrder
from cg.services.orders.validation.order_types.fastq.models.order import FastqOrder
from cg.services.orders.validation.order_types.fluffy.models.order import FluffyOrder
from cg.services.orders.validation.order_types.microsalt.models.order import MicrosaltOrder
from cg.services.orders.validation.order_types.mip_dna.models.order import MIPDNAOrder
from cg.services.orders.validation.order_types.mutant.models.order import MutantOrder
from cg.services.orders.validation.order_types.rml.models.order import RMLOrder


def test_to_lims_mip(mip_dna_order: MIPDNAOrder):
    # GIVEN a scout order for a trio

    # WHEN parsing the order to format for LIMS import
    new_samples = [sample for _, _, sample in mip_dna_order.enumerated_new_samples]
    samples: list[LimsSample] = OrderLimsService._build_lims_sample(
        customer="cust003",
        samples=new_samples,
        workflow=Workflow.MIP_DNA,
        delivery_type=mip_dna_order.delivery_type,
        skip_reception_control=mip_dna_order.skip_reception_control,
    )

    # THEN it should list all samples
    assert len(samples) == 4

    # THEN container should be 96 well plate for all samples
    assert {sample.container for sample in samples} == {"96 well plate"}

    # THEN container names should be the same for all samples
    container_names = {sample.container_name for sample in samples if sample.container_name}
    assert container_names == {"MipPlate"}

    # THEN it should pick out relevant UDFs
    first_sample: LimsSample = samples[0]
    assert first_sample.well_position == "A:1"
    assert first_sample.udfs.priority == "priority"
    assert first_sample.udfs.application == "WGSPCFC030"
    assert first_sample.udfs.source == "blood"
    assert first_sample.udfs.customer == "cust003"
    assert first_sample.udfs.volume == "54"

    # THEN assert that the comment of a sample is a string
    assert isinstance(samples[1].udfs.comment, str)


def test_to_lims_fastq(fastq_order: FastqOrder):
    # GIVEN a fastq order for two samples; normal vs. tumour

    # WHEN parsing the order to format for LIMS
    samples: list[LimsSample] = OrderLimsService._build_lims_sample(
        customer="dummyCust",
        samples=fastq_order.samples,
        workflow=Workflow.RAW_DATA,
        delivery_type=fastq_order.delivery_type,
        skip_reception_control=fastq_order.skip_reception_control,
    )

    # THEN two samples should be parsed, one normal and one tumour
    assert len(samples) == 2
    normal_sample = samples[0]
    tumour_sample = samples[1]

    # THEN it should pick out relevant UDFs
    assert normal_sample.udfs.tumour is False
    assert tumour_sample.udfs.tumour is True
    assert normal_sample.udfs.volume == "54"


def test_to_lims_rml(rml_order: RMLOrder):
    # GIVEN a rml order for four samples

    # WHEN parsing for LIMS
    samples: list[LimsSample] = OrderLimsService._build_lims_sample(
        customer="cust000",
        samples=rml_order.samples,
        workflow=Workflow.RAW_DATA,
        delivery_type=rml_order.delivery_type,
        skip_reception_control=rml_order.skip_reception_control,
    )

    # THEN it should have found the same number of samples
    assert len(samples) == 4

    # THEN the relevant UDFs are parsed
    first_sample = samples[0]
    assert first_sample.udfs.pool == "pool1"
    assert first_sample.udfs.application.startswith("RML")
    assert first_sample.udfs.index == "IDT DupSeq 10 bp Set B"
    assert first_sample.udfs.index_number == "3"
    assert first_sample.udfs.rml_plate_name == "plate1"
    assert first_sample.udfs.well_position_rml == "A:1"


def test_to_lims_fluffy(fluffy_order: FluffyOrder):
    # GIVEN a Fluffy order for four samples

    # WHEN parsing for LIMS
    samples: list[LimsSample] = OrderLimsService._build_lims_sample(
        customer="cust000",
        samples=fluffy_order.samples,
        workflow=Workflow.FLUFFY,
        delivery_type=fluffy_order.delivery_type,
        skip_reception_control=fluffy_order.skip_reception_control,
    )

    # THEN it should have found the same number of samples
    assert len(samples) == 4

    # THEN the relevant UDFs are parsed
    first_sample = samples[0]
    assert first_sample.udfs.pool == "pool1"
    assert first_sample.udfs.application.startswith("RML")
    assert first_sample.udfs.index == "IDT DupSeq 10 bp Set B"
    assert first_sample.udfs.index_number == "3"
    assert first_sample.udfs.rml_plate_name == "plate1"
    assert first_sample.udfs.well_position_rml == "A:1"


def test_to_lims_microbial(microsalt_order: MicrosaltOrder):
    # GIVEN a microbial order for three samples

    # WHEN parsing for LIMS
    samples: list[LimsSample] = OrderLimsService._build_lims_sample(
        customer="cust000",
        samples=microsalt_order.samples,
        workflow=Workflow.MICROSALT,
        delivery_type=microsalt_order.delivery_type,
        skip_reception_control=microsalt_order.skip_reception_control,
    )

    # THEN 5 samples should be parsed
    assert len(samples) == 5

    # THEN it should pick out relevant UDFs
    first_sample = samples[0].dict()
    assert first_sample["udfs"]["priority"] == "research"
    assert first_sample["udfs"]["organism"] == "C. jejuni"
    assert first_sample["udfs"]["reference_genome"] == "NC_000001"
    assert first_sample["udfs"]["extraction_method"] == "MagNaPure 96"
    assert first_sample["udfs"]["volume"] == "20"


def test_to_lims_sarscov2(mutant_order: MutantOrder):
    # GIVEN a sarscov2 order for samples

    # WHEN parsing for LIMS
    samples: list[LimsSample] = OrderLimsService._build_lims_sample(
        customer="cust000",
        samples=mutant_order.samples,
        workflow=Workflow.MUTANT,
        delivery_type=mutant_order.delivery_type,
        skip_reception_control=mutant_order.skip_reception_control,
    )

    # THEN it should have found the same number of samples
    assert len(samples) == 6

    # THEN it should pick out relevant UDFs
    first_sample = samples[0].dict()
    assert first_sample["udfs"]["collection_date"] == "2021-05-05"
    assert first_sample["udfs"]["extraction_method"] == "MagNaPure 96"
    assert first_sample["udfs"]["lab_code"] == "SE100 Karolinska"
    assert first_sample["udfs"]["organism"] == "SARS-CoV-2"
    assert first_sample["udfs"]["original_lab"] == "Karolinska University Hospital Solna"
    assert first_sample["udfs"]["original_lab_address"] == "171 76 Stockholm"
    assert first_sample["udfs"]["pre_processing_method"] == "COVIDSeq"
    assert first_sample["udfs"]["priority"] == "research"
    assert first_sample["udfs"]["reference_genome"] == "NC_111"
    assert first_sample["udfs"]["region"] == "Stockholm"
    assert first_sample["udfs"]["region_code"] == "01"
    assert first_sample["udfs"]["selection_criteria"] == "Allmän övervakning"
    assert first_sample["udfs"]["volume"] == "20"


def test_to_lims_balsamic(balsamic_order: BalsamicOrder):
    # GIVEN a cancer order for a sample

    new_samples = [sample for _, _, sample in balsamic_order.enumerated_new_samples]
    # WHEN parsing the order to format for LIMS import
    samples: list[LimsSample] = OrderLimsService._build_lims_sample(
        customer="cust000",
        samples=new_samples,
        workflow=Workflow.BALSAMIC,
        delivery_type=balsamic_order.delivery_type,
        skip_reception_control=balsamic_order.skip_reception_control,
    )

    # THEN it should list all samples
    assert len(samples) == 1

    # THEN it should determine the container, container name, and well position
    container_names = {sample.container_name for sample in samples if sample.container_name}

    # THEN it should pick out relevant UDFs
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
    assert first_sample["udfs"]["capture_kit"] == "GIcfDNA"
    assert first_sample["udfs"]["tumour_purity"] == "13"
    assert first_sample["udfs"]["formalin_fixation_time"] == "15"
    assert first_sample["udfs"]["post_formalin_fixation_time"] == "3"
    assert first_sample["udfs"]["tissue_block_size"] == "large"
    assert first_sample["udfs"]["comment"] == "This is a sample comment"


def test_order_with_skip_reception_control(balsamic_order: BalsamicOrder):
    """Test that an order set to skip reception control can be parsed correctly by LIMS."""
    # GIVEN a Balsamic order with one case and one sample set to skip reception control
    balsamic_order.skip_reception_control = True

    # WHEN parsing the order to format for LIMS import
    new_samples = [sample for _, _, sample in balsamic_order.enumerated_new_samples]
    samples: list[LimsSample] = OrderLimsService._build_lims_sample(
        customer="cust000",
        samples=new_samples,
        workflow=Workflow.BALSAMIC,
        delivery_type=balsamic_order.delivery_type,
        skip_reception_control=balsamic_order.skip_reception_control,
    )

    # THEN the parsed samples should have the skip reception control flag set
    first_sample = samples[0].dict()
    assert first_sample["udfs"]["skip_reception_control"] is True
