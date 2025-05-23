from pathlib import Path

from cg.apps.orderform.excel_orderform_parser import ExcelOrderformParser
from cg.constants.constants import DataDelivery
from cg.models.orders.constants import OrderType
from cg.models.orders.excel_sample import ExcelSample
from cg.models.orders.orderform_schema import Orderform


def get_sample_obj(order_form_parser: ExcelOrderformParser, sample_id: str) -> ExcelSample | None:
    for sample_obj in order_form_parser.samples:
        if sample_obj.name == sample_id:
            return sample_obj


def is_excel(file_path: Path) -> bool:
    return Path(file_path).suffix == ".xlsx"


def test_parse_mip_rna_orderform(mip_rna_orderform: str):
    """Test to parse an mip rna orderform in excel format"""
    # GIVEN a orderform in excel format
    assert is_excel(Path(mip_rna_orderform))
    # GIVEN a orderform API
    orderform_parser: ExcelOrderformParser = ExcelOrderformParser()

    # WHEN parsing the orderform
    orderform_parser.parse_orderform(excel_path=mip_rna_orderform)

    # THEN assert that the project type is correct
    assert orderform_parser.project_type == OrderType.MIP_RNA


def test_parse_rnafusion_orderform(rnafusion_orderform: str):
    """Test to parse an rnafusion orderform in excel format"""
    # GIVEN a orderform in excel format
    assert is_excel(Path(rnafusion_orderform))
    # GIVEN a orderform API
    orderform_parser: ExcelOrderformParser = ExcelOrderformParser()

    # WHEN parsing the orderform
    orderform_parser.parse_orderform(excel_path=rnafusion_orderform)

    # THEN assert that the project type is correct
    assert orderform_parser.project_type == OrderType.RNAFUSION


def test_parse_balsamic_orderform(balsamic_orderform: str):
    """Test to parse a balsamic orderform in Excel format"""
    # GIVEN a orderform in excel format
    assert is_excel(Path(balsamic_orderform))
    # GIVEN a orderform API
    orderform_parser: ExcelOrderformParser = ExcelOrderformParser()

    # WHEN parsing the orderform
    orderform_parser.parse_orderform(excel_path=balsamic_orderform)

    # THEN assert that the project type is correct
    assert orderform_parser.project_type == OrderType.BALSAMIC


def test_parse_balsamic_umi_orderform(balsamic_umi_orderform: str):
    """Test to parse a balsamic orderform in excel format"""
    # GIVEN a orderform in excel format
    assert is_excel(Path(balsamic_umi_orderform))
    # GIVEN a orderform API
    orderform_parser: ExcelOrderformParser = ExcelOrderformParser()

    # WHEN parsing the orderform
    orderform_parser.parse_orderform(excel_path=balsamic_umi_orderform)

    # THEN assert that the project type is correct
    assert orderform_parser.project_type == OrderType.BALSAMIC_UMI


def test_parse_microbial_orderform(microsalt_orderform: str):
    """Test to parse a microbial orderform in excel format"""
    # GIVEN a order form in excel format
    assert is_excel(Path(microsalt_orderform))
    # GIVEN a orderform API
    orderform_parser: ExcelOrderformParser = ExcelOrderformParser()

    # WHEN parsing the orderform
    orderform_parser.parse_orderform(excel_path=microsalt_orderform)

    # THEN assert that the project type is correct
    assert orderform_parser.project_type == OrderType.MICROSALT


def test_parse_pacbio_sequencing_orderform(pacbio_revio_sequencing_orderform: str):
    """Test to parse a pacbio orderform in excel format"""
    # GIVEN a order form in excel format
    assert is_excel(Path(pacbio_revio_sequencing_orderform))
    # GIVEN a orderform API
    orderform_parser: ExcelOrderformParser = ExcelOrderformParser()

    # WHEN parsing the orderform
    orderform_parser.parse_orderform(excel_path=pacbio_revio_sequencing_orderform)

    # THEN assert that the project type is correct
    assert orderform_parser.project_type == OrderType.PACBIO_LONG_READ


def test_parse_nallo_sequencing_orderform(nallo_order_form: str):
    """Test to parse a Nallo order form in Excel format"""
    # GIVEN a Nallo order form in Excel format
    assert is_excel(Path(nallo_order_form))

    # GIVEN a orderform API
    orderform_parser: ExcelOrderformParser = ExcelOrderformParser()

    # WHEN parsing the orderform
    orderform_parser.parse_orderform(excel_path=nallo_order_form)

    # THEN assert that the project type is correct
    assert orderform_parser.project_type == OrderType.NALLO


def test_parse_sarscov2_orderform(sarscov2_orderform: str):
    """Test to parse a sarscov2 orderform in excel format"""

    # GIVEN a order form in excel format
    assert is_excel(Path(sarscov2_orderform))
    # GIVEN a orderform API
    orderform_parser: ExcelOrderformParser = ExcelOrderformParser()

    # WHEN parsing the orderform
    orderform_parser.parse_orderform(excel_path=sarscov2_orderform)

    # THEN assert that the project type is correct
    assert orderform_parser.project_type == OrderType.SARS_COV_2


def test_parse_metagenome_orderform(metagenome_orderform: str):
    """Test to parse an metagenome orderform in excel format"""
    # GIVEN a order form in excel format
    assert is_excel(Path(metagenome_orderform))
    # GIVEN a orderform API
    orderform_parser: ExcelOrderformParser = ExcelOrderformParser()

    # WHEN parsing the orderform
    orderform_parser.parse_orderform(excel_path=metagenome_orderform)

    # THEN assert that the project type is correct
    assert orderform_parser.project_type == OrderType.METAGENOME


def test_generate_mip_orderform_with_cases(mip_order_parser: ExcelOrderformParser):
    """Test to parse a mip orderform with cases"""
    # GIVEN a mip orderform parser

    # WHEN generating a orderform
    orderform: Orderform = mip_order_parser.generate_orderform()

    # THEN assert that there where cases in the order
    assert len(orderform.cases) > 0

    case_obj = orderform.cases[0]
    assert len(case_obj.samples) == 3
    assert case_obj.name == "mipdnacase1"
    assert case_obj.priority == "standard"
    assert set(case_obj.panels) == set(["Actionable"])


def test_parse_mip_orderform(mip_orderform: str, nr_samples_mip_orderform: int):
    """Test to parse a mip orderform in xlsx format"""
    # GIVEN a orderform in excel format
    assert is_excel(Path(mip_orderform))
    # GIVEN a orderform API
    order_form_parser = ExcelOrderformParser()
    # GIVEN the correct orderform name
    order_name: str = Path(mip_orderform).stem

    # WHEN parsing the mip orderform
    order_form_parser.parse_orderform(excel_path=mip_orderform)

    # THEN assert that the correct name was set
    assert order_form_parser.order_name == order_name

    # THEN assert the number of samples parsed are correct
    assert len(order_form_parser.samples) == nr_samples_mip_orderform

    # THEN assert that the project type is correct
    assert order_form_parser.project_type == OrderType.MIP_DNA


def test_parse_mip_orderform_no_delivery(
    mip_orderform_no_delivery: str, nr_samples_mip_orderform: int
):
    """Test to parse a mip orderform in xlsx format"""
    # GIVEN a orderform in excel format
    assert is_excel(Path(mip_orderform_no_delivery))
    # GIVEN a orderform API
    order_form_parser = ExcelOrderformParser()
    # GIVEN the correct orderform name
    order_name: str = Path(mip_orderform_no_delivery).stem

    # WHEN parsing the mip orderform
    order_form_parser.parse_orderform(excel_path=mip_orderform_no_delivery)

    # THEN assert that the correct name was set
    assert order_form_parser.order_name == order_name

    # THEN assert the number of samples parsed are correct
    assert len(order_form_parser.samples) == nr_samples_mip_orderform
    assert order_form_parser.samples[0].panels == ["Inherited cancer"]
    assert order_form_parser.samples[1].panels == ["AID", "Inherited cancer"]
    assert order_form_parser.delivery_type == DataDelivery.NO_DELIVERY

    # THEN assert that the project type is correct
    assert order_form_parser.project_type == OrderType.MIP_DNA


def test_parse_rml_orderform(rml_orderform: str, nr_samples_rml_orderform: int):
    """Test to parse an excel orderform in xlsx format"""
    # GIVEN a orderform in excel format
    assert is_excel(Path(rml_orderform))
    # GIVEN a orderform API
    order_form_parser = ExcelOrderformParser()
    # GIVEN the correct orderform name
    order_name: str = Path(rml_orderform).stem

    # WHEN parsing the RML orderform
    order_form_parser.parse_orderform(excel_path=rml_orderform)

    # THEN assert that the correct name was set
    assert order_form_parser.order_name == order_name

    # THEN assert that the number of samples was correct
    assert len(order_form_parser.samples) == nr_samples_rml_orderform


def test_parse_fastq_orderform(fastq_orderform: str, nr_samples_fastq_orderform: int):
    """Test to parse an fastq orderform in xlsx format"""
    # GIVEN a orderform in excel format
    assert is_excel(Path(fastq_orderform))
    # GIVEN a orderform API
    order_form_parser = ExcelOrderformParser()
    # GIVEN the correct orderform name
    order_name: str = Path(fastq_orderform).stem

    # WHEN parsing the fastq orderform
    order_form_parser.parse_orderform(excel_path=fastq_orderform)

    # THEN assert that the correct name was set
    assert order_form_parser.order_name == order_name

    # THEN assert that the correct number if samples where parsed
    assert len(order_form_parser.samples) == nr_samples_fastq_orderform

    # THEN it should determine the project type
    assert order_form_parser.project_type == OrderType.FASTQ

    # THEN it should determine the correct customer should have been parsed
    assert order_form_parser.customer_id == "cust000"


def test_fastq_samples_is_correct(fastq_order_parser: ExcelOrderformParser):
    """Test that everything was correctly parsed from the fastq order"""
    # GIVEN a orderform parser where a fastq order is parsed

    # GIVEN a tumor and normal sample with known information
    tumor_sample_id = "fastqsample1"
    normal_sample_id = "fastqsample2"

    # WHEN fetching the tumor and the normal sample
    tumour_sample = get_sample_obj(fastq_order_parser, tumor_sample_id)
    normal_sample = get_sample_obj(fastq_order_parser, normal_sample_id)

    # THEN assert that they where both parsed
    assert tumour_sample and normal_sample


def test_generate_parsed_rml_orderform(rml_order_parser: ExcelOrderformParser):
    """Test to generate a order from a parsed rml excel file"""
    # GIVEN a order form parser that have parsed an excel file

    # WHEN generating the order
    order: Orderform = rml_order_parser.generate_orderform()

    # THEN assert that some samples where parsed and found
    assert order.samples
    # THEN assert that no cases where found since this is an RML order
    assert not order.cases


def test_get_data_delivery(microsalt_order_parser):
    """Tests that the data_delivery field is correctly parsed and translated to a value in the
    data_delivery enum"""
    # GIVEN an excel order form
    # WHEN the function is called
    data_delivery = microsalt_order_parser.get_data_delivery()
    # THEN no errors should be raised and a data_delivery string should be returned
    assert data_delivery


def test_parse_microbial_sequencing_orderform(microbial_sequencing_orderform: str):
    """Test the parsing of a microbial sequencing orderform."""
    # GIVEN a microbial sequencing orderform in excel format

    # WHEN parsing the orderform
    order_form_parser = ExcelOrderformParser()
    order_form_parser.parse_orderform(excel_path=microbial_sequencing_orderform)

    # THEN assert that the project type is correct
    assert order_form_parser.project_type == OrderType.MICROBIAL_FASTQ
    # THEN assert that samples are parsed
    assert order_form_parser.samples


def test_parse_taxprofiler_orderform(taxprofiler_orderform: str):
    """Test to parse a Taxprofiler orderform in excel format"""

    # GIVEN an order form in Excel format
    assert is_excel(Path(taxprofiler_orderform))

    # GIVEN an ExcelOrderformParser
    orderform_parser: ExcelOrderformParser = ExcelOrderformParser()

    # WHEN parsing the orderform
    orderform_parser.parse_orderform(excel_path=taxprofiler_orderform)

    # THEN assert that the project type is correct
    assert orderform_parser.project_type == OrderType.TAXPROFILER


def test_parse_tomte_orderform(tomte_orderform: str):
    """Test to parse a Tomte orderform in excel format"""

    # GIVEN an order form in Excel format
    assert is_excel(Path(tomte_orderform))

    # GIVEN an ExcelOrderformParser
    orderform_parser: ExcelOrderformParser = ExcelOrderformParser()

    # WHEN parsing the orderform
    orderform_parser.parse_orderform(excel_path=tomte_orderform)

    # THEN assert that the project type is correct
    assert orderform_parser.project_type == OrderType.TOMTE
