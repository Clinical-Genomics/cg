from pathlib import Path
from typing import Optional

from cg.apps.orderform.excel_orderform_parser import ExcelOrderformParser
from cg.constants import Pipeline
from cg.meta.orders import OrderType
from cg.models.orders.excel_sample import ExcelSample
from cg.models.orders.orderform_schema import Orderform


def get_sample_obj(
    order_form_parser: ExcelOrderformParser, sample_id: str
) -> Optional[ExcelSample]:
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


def test_parse_balsamic_orderform(balsamic_orderform: str):
    """Test to parse an balsamic orderform in excel format"""
    # GIVEN a orderform in excel format
    assert is_excel(Path(balsamic_orderform))
    # GIVEN a orderform API
    orderform_parser: ExcelOrderformParser = ExcelOrderformParser()

    # WHEN parsing the orderform
    orderform_parser.parse_orderform(excel_path=balsamic_orderform)

    # THEN assert that the project type is correct
    assert orderform_parser.project_type == OrderType.BALSAMIC


def test_parse_microbial_orderform(microbial_orderform: str):
    """Test to parse a microbial orderform in excel format"""
    # GIVEN a order form in excel format
    assert is_excel(Path(microbial_orderform))
    # GIVEN a orderform API
    orderform_parser: ExcelOrderformParser = ExcelOrderformParser()

    # WHEN parsing the orderform
    orderform_parser.parse_orderform(excel_path=microbial_orderform)

    # THEN assert that the project type is correct
    assert orderform_parser.project_type == OrderType.MICROSALT


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


def test_parse_external_orderform(external_orderform: str):
    """Test to parse a external orderform in xlsx format"""
    # GIVEN a orderform in excel format
    assert is_excel(Path(external_orderform))
    # GIVEN a orderform API
    order_form_parser = ExcelOrderformParser()

    # WHEN parsing the mip orderform
    order_form_parser.parse_orderform(excel_path=external_orderform)

    # THEN assert that the project type is correct
    assert order_form_parser.project_type == OrderType.EXTERNAL


def test_generate_external_orderform_with_case(external_order_parser: ExcelOrderformParser):
    """Test to generate a orderform based on parsing of an external orderform"""
    # GIVEN a external orderform parser

    # WHEN generating the orderform
    orderform: Orderform = external_order_parser.generate_orderform()

    # THEN assert that the customer id was correct
    assert external_order_parser.customer_id == "cust002"
    # THEN asert that there where cases in the order
    assert len(orderform.cases) > 0

    case_obj = orderform.cases[0]
    # THEN assert that the case name is as expected
    assert case_obj.name == "fam2"
    assert case_obj.priority == "standard"
    assert set(case_obj.panels) == {"CILM", "CTD"}


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
    assert case_obj.priority == "research"
    assert set(case_obj.panels) == set(["AD-HSP", "Ataxi", "Actionable"])


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

    # THEN assert the number of samples parsed are correct
    assert len(order_form_parser.samples) == nr_samples_mip_orderform

    # THEN assert that the project type is correct
    assert order_form_parser.project_type == str(Pipeline.MIP_DNA)


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
    assert order_form_parser.project_type == str(Pipeline.FASTQ)

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


def test_generate_parsed_rml_orderform(rml_order_parser: ExcelOrderformParser, caplog):
    """Test to generate a order from a parsed rml excel file"""
    # GIVEN a order form parser that have parsed an excel file

    # WHEN generating the order
    order: Orderform = rml_order_parser.generate_orderform()

    # THEN assert that some samples where parsed and found
    assert order.samples
    # THEN assert that no cases where found since this is an RML order
    assert not order.cases
