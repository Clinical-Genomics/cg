import pytest
from cg.constants import DataDelivery
from cg.models.orders.excel_sample import ExcelSample
from pydantic import ValidationError


def test_excel_minimal_sample_schema(minimal_excel_sample: dict):
    """Test instantiate a minimal sample"""
    # GIVEN some simple sample info from the simplest sample possible

    # WHEN creating a excel sample
    excel_sample: ExcelSample = ExcelSample(**minimal_excel_sample)

    # THEN assert that the sample name info was correctly parsed
    assert excel_sample.name == minimal_excel_sample["Sample/Name"]


def test_excel_swedish_priority(minimal_excel_sample: dict):
    """Test instantiate a sample with swedish priority"""
    # GIVEN some sample where the priority is in swedish
    minimal_excel_sample["UDF/priority"] = "förtur"

    # WHEN creating a excel sample
    excel_sample: ExcelSample = ExcelSample(**minimal_excel_sample)

    # THEN assert that the sample priority info was correctly parsed
    assert excel_sample.priority == "priority"


def test_excel_source_type(minimal_excel_sample: dict):
    """Test instantiate a sample with source type"""
    # GIVEN some sample with a known source type
    source_type = "blood"
    minimal_excel_sample["UDF/Source"] = source_type

    # WHEN creating a excel sample
    excel_sample: ExcelSample = ExcelSample(**minimal_excel_sample)

    # THEN assert that the source type info was correctly parsed
    assert excel_sample.source == source_type


def test_excel_unknown_source_type(minimal_excel_sample: dict):
    """Test instantiate a sample with a unknown source type

    ValidationError should be raised since the source type does not exist
    """
    # GIVEN some sample with a known source type
    source_type = "flagalella"
    minimal_excel_sample["UDF/Source"] = source_type

    # WHEN creating a excel sample
    with pytest.raises(ValidationError):
        # THEN assert that a validation error is raised since source does not exist
        excel_sample: ExcelSample = ExcelSample(**minimal_excel_sample)


def test_excel_with_panels(minimal_excel_sample: dict):
    """Test instantiate a sample with some gene panels set"""
    # GIVEN some sample with two gene panels in a semi colon separated string
    panel_1 = "OMIM"
    panel_2 = "PID"
    minimal_excel_sample["UDF/Gene List"] = ";".join([panel_1, panel_2])

    # WHEN creating a excel sample
    excel_sample: ExcelSample = ExcelSample(**minimal_excel_sample)

    # THEN assert that the panels was parsed into a list
    assert set(excel_sample.panels) == set([panel_1, panel_2])


def test_mip_rna_sample_is_correct(mip_rna_orderform_sample: dict):
    """Test that a mip rna orderform sample in parsed correct"""
    # GIVEN sample data about a known balsamic sample

    # WHEN parsing the sample
    mip_rna_sample: ExcelSample = ExcelSample(**mip_rna_orderform_sample)

    # THEN assert that the sample information is parsed correct
    assert mip_rna_sample.name == "s1"
    assert mip_rna_sample.container == "96 well plate"
    assert mip_rna_sample.data_analysis == "MIP RNA"
    assert mip_rna_sample.data_delivery.lower() == str(DataDelivery.ANALYSIS_FILES)
    assert mip_rna_sample.application == "RNAPOAR025"
    assert mip_rna_sample.sex == "male"
    # case-id on the case
    # customer on the order (data)
    # require-qc-ok on the case
    assert mip_rna_sample.source == "tissue (FFPE)"

    assert mip_rna_sample.container_name == "plate1"
    assert mip_rna_sample.well_position == "A:1"
    assert mip_rna_sample.tumour is True
    assert mip_rna_sample.quantity == "4"
    assert mip_rna_sample.comment == "other Elution buffer"
    assert mip_rna_sample.from_sample == "s1"
    assert mip_rna_sample.time_point == "0"


def test_balsamic_sample_is_correct(balsamic_orderform_sample: dict):
    """Test that a balsamic orderform sample is parsed correct"""
    # GIVEN sample data about a known balsamic sample

    # WHEN parsing the sample
    balsamic_sample: ExcelSample = ExcelSample(**balsamic_orderform_sample)

    # THEN assert that the sample information is parsed correct
    assert balsamic_sample.name == "s1"
    assert balsamic_sample.container == "96 well plate"
    assert balsamic_sample.data_analysis == "Balsamic"
    assert balsamic_sample.data_delivery == str(DataDelivery.ANALYSIS_BAM_FILES)
    assert balsamic_sample.application == "PANKTTR010"
    assert balsamic_sample.sex == "male"
    assert balsamic_sample.volume == "1"
    assert balsamic_sample.source == "tissue (FFPE)"
    assert balsamic_sample.container_name == "plate1"
    assert balsamic_sample.well_position == "A:1"
    assert balsamic_sample.elution_buffer == 'Other (specify in "Comments")'
    assert balsamic_sample.tumour is True
    assert balsamic_sample.capture_kit == "GMCKsolid"
    assert balsamic_sample.tumour_purity == "5"
    assert balsamic_sample.formalin_fixation_time == "2"
    assert balsamic_sample.post_formalin_fixation_time == "3"
    assert balsamic_sample.tissue_block_size == "small"
    assert balsamic_sample.quantity == "4"
    assert balsamic_sample.comment == "other Elution buffer"


def test_microsalt_sample_is_correct(microbial_orderform_sample: dict):
    """Test that a microbial orderform sample is parsed correct"""
    # GIVEN sample data about a known microbial sample

    # WHEN parsing the sample
    microbial_sample: ExcelSample = ExcelSample(**microbial_orderform_sample)

    # THEN assert that the sample information is parsed correct
    assert microbial_sample.name == "s1"
    assert microbial_sample.organism == "other"
    assert microbial_sample.reference_genome == "NC_00001"
    assert microbial_sample.data_analysis == "fastq"
    assert microbial_sample.application == "MWRNXTR003"
    # customer on order (data)
    assert microbial_sample.require_qcok is True
    assert microbial_sample.elution_buffer == 'Other (specify in "Comments")'
    assert microbial_sample.extraction_method == "other (specify in comment field)"
    assert microbial_sample.container == "96 well plate"
    assert microbial_sample.priority in "research"
    assert microbial_sample.container_name == "plate1"
    assert microbial_sample.well_position == "A:1"
    assert microbial_sample.organism_other == "other species"
    assert microbial_sample.concentration_sample == "1"
    assert microbial_sample.quantity == "2"
    assert microbial_sample.comment == "comment"


def test_metagenome_sample_is_correct(metagenome_orderform_sample: dict):
    """Test that a metagenome orderform sample is parsed correct"""
    # GIVEN sample data about a know metagenome sample

    # WHEN parsing the sample
    metagenome_sample: ExcelSample = ExcelSample(**metagenome_orderform_sample)

    assert metagenome_sample.name == "sample1"
    assert metagenome_sample.source == "other"
    assert metagenome_sample.data_analysis == "fastq"
    assert metagenome_sample.application == "METPCFR030"
    assert metagenome_sample.customer == "cust000"
    assert metagenome_sample.require_qcok is True
    assert metagenome_sample.elution_buffer == 'Other (specify in "Comments")'
    assert metagenome_sample.extraction_method == "other (specify in comment field)"
    assert metagenome_sample.container == "96 well plate"
    assert metagenome_sample.priority == "research"

    # Required if Plate
    assert metagenome_sample.container_name == "plate1"
    assert metagenome_sample.well_position == "A:1"

    # These fields are not required
    assert metagenome_sample.concentration_sample == "1"
    assert metagenome_sample.quantity == "2"
    assert metagenome_sample.comment == "comment"


def test_mip_sample_is_correct(mip_orderform_sample: dict):
    """Tests that a mip sample is parsed correct"""
    # GIVEN sample data about a known sample

    # WHEN parsing the sample
    proband_sample: ExcelSample = ExcelSample(**mip_orderform_sample)
    assert proband_sample.name == "s1"
    assert proband_sample.container == "96 well plate"
    assert proband_sample.data_analysis == "MIP DNA"
    assert proband_sample.data_delivery == str(DataDelivery.SCOUT)
    assert proband_sample.application == "PANKTTR010"
    assert proband_sample.sex == "male"
    assert proband_sample.source == "tissue (FFPE)"
    assert proband_sample.tumour is True
    assert proband_sample.container_name == "plate1"
    assert proband_sample.well_position == "A:1"
    assert proband_sample.status == "affected"
    assert proband_sample.mother == "s2"
    assert proband_sample.father == "s3"
    assert proband_sample.quantity == "4"
    assert proband_sample.comment == "other Elution buffer"


def test_rml_sample_is_correct(rml_excel_sample: dict):
    """Test that one of the rml samples is on the correct format"""
    # GIVEN a sample with known values
    sample_obj: ExcelSample = ExcelSample(**rml_excel_sample)

    # WHEN fetching the sample

    # THEN assert that all the known values are correct
    assert sample_obj.pool == "pool1"
    assert sample_obj.application == "RMLP10R300"
    assert sample_obj.data_analysis == "FLUFFY"
    assert sample_obj.volume == "1"
    assert sample_obj.concentration == "2"
    assert sample_obj.index == "IDT DupSeq 10 bp Set B"
    assert sample_obj.index_number == "1"

    assert sample_obj.container_name is None
    assert sample_obj.rml_plate_name == "plate"
    assert sample_obj.well_position is None
    assert sample_obj.well_position_rml == "A:1"

    assert sample_obj.reagent_label == "A01 IDT_10nt_541 (ATTCCACACT-AACAAGACCA)"

    assert sample_obj.custom_index == "GATACA"

    assert sample_obj.comment == "comment"
    assert sample_obj.concentration_sample == "3"


def test_tumor_sample_schema(tumor_fastq_sample: dict):
    """Test to validate a tumor fastq sample"""
    # GIVEN some simple sample info from a fastq tumor sample

    # WHEN creating a excel sample
    excel_sample: ExcelSample = ExcelSample(**tumor_fastq_sample)

    # THEN assert that sample information was correctly parsed
    assert excel_sample.tumour is True
    assert excel_sample.source == "tissue (FFPE)"
    assert excel_sample.quantity == "4"
    assert excel_sample.comment == "other Elution buffer"
    assert excel_sample.tumour is True


def test_normal_sample_schema(normal_fastq_sample: dict):
    """Test to validate a normal fastq sample"""
    # GIVEN some simple sample info from a fastq normal sample

    # WHEN creating a excel sample
    excel_sample: ExcelSample = ExcelSample(**normal_fastq_sample)

    # THEN assert that the sample information was correctly parsed
    assert excel_sample.container == "Tube"
    assert excel_sample.data_analysis == "No analysis"
    assert excel_sample.data_delivery == "fastq"
    assert excel_sample.application == "WGTPCFC030"
    assert excel_sample.sex == "female"
    assert excel_sample.case_id == "c1"
    assert excel_sample.require_qcok is False
    assert excel_sample.source == "bone marrow"
    assert excel_sample.priority == "research"
    assert excel_sample.container_name == ""
    assert excel_sample.well_position == ""
    assert excel_sample.tumour is False
