from pathlib import Path

import openpyxl
import pytest
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from cg.apps.orderform.excel_orderform_parser import ExcelOrderformParser
from cg.models.orders.constants import OrderType
from cg.models.orders.excel_sample import ExcelSample
from cg.models.orders.orderform_schema import Orderform


def get_sample_obj(order_form_parser: ExcelOrderformParser, sample_id: str) -> ExcelSample | None:
    for sample_obj in order_form_parser.samples:
        if sample_obj.name == sample_id:
            return sample_obj


def is_excel(file_path: Path) -> bool:
    return Path(file_path).suffix == ".xlsx"


def get_nr_samples_excel(orderform_path: str) -> int:
    """Parse a excel orderform file and return the number of sample rows."""
    orderform_parser: ExcelOrderformParser = ExcelOrderformParser()
    workbook: Workbook = openpyxl.load_workbook(
        filename=orderform_path, read_only=True, data_only=True
    )
    sheet_name: str = orderform_parser.get_sheet_name(workbook.sheetnames)
    orderform_sheet: Worksheet = workbook[sheet_name]
    nr_samples = 0
    current_row = "unknown"
    for row in orderform_sheet.rows:
        if row[0].value == "</SAMPLE ENTRIES>":
            # End of samples
            break
        elif row[0].value == "<SAMPLE ENTRIES>":
            # Samples start here
            current_row = "samples"
            continue
        if current_row == "samples":
            values = []
            for cell in row:
                value = str(cell.value)
                if value == "None":
                    value = ""
                values.append(value)

            # skip empty rows
            if values[0]:
                nr_samples += 1
    return nr_samples


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


@pytest.mark.parametrize(
    "orderform_fixture, ordertype",
    [
        ("balsamic_orderform", OrderType.BALSAMIC),
        ("balsamic_umi_orderform", OrderType.BALSAMIC_UMI),
        ("fastq_orderform", OrderType.FASTQ),
        ("metagenome_orderform", OrderType.METAGENOME),
        ("microsalt_orderform", OrderType.MICROSALT),
        ("mip_orderform", OrderType.MIP_DNA),
        ("mip_rna_orderform", OrderType.MIP_RNA),
        ("nallo_order_form", OrderType.NALLO),
        ("raredisease_orderform", OrderType.RAREDISEASE),
        ("rml_orderform", OrderType.FLUFFY),
        ("rnafusion_orderform", OrderType.RNAFUSION),
        ("sarscov2_orderform", OrderType.SARS_COV_2),
        ("pacbio_revio_sequencing_orderform", OrderType.PACBIO_LONG_READ),
        ("microbial_sequencing_orderform", OrderType.MICROBIAL_FASTQ),
        ("taxprofiler_orderform", OrderType.TAXPROFILER),
        ("tomte_orderform", OrderType.TOMTE),
    ],
    ids=[
        "balsamic",
        "balsamic_umi",
        "fastq",
        "metagenome",
        "microsalt",
        "mip_dna",
        "mip_rna",
        "nallo",
        "raredisease",
        "fluffy",
        "rnafusion",
        "sarscov2",
        "pacbio_long_read",
        "microbial_fastq",
        "taxprofiler",
        "tomte",
    ],
)
def test_parse_orderform(
    orderform_fixture: str, ordertype: OrderType, request: pytest.FixtureRequest
):
    """Test to parse an order form in excel format"""
    # GIVEN a orderform in excel format
    orderform: str = request.getfixturevalue(orderform_fixture)
    assert is_excel(Path(orderform))

    # GIVEN the correct orderform name
    order_name: str = Path(orderform).stem

    # GIVEN a orderform API
    order_form_parser: ExcelOrderformParser = ExcelOrderformParser()

    # WHEN parsing the orderform
    order_form_parser.parse_orderform(excel_path=orderform)

    # THEN assert that the project type is correct
    assert order_form_parser.project_type == ordertype

    # THEN assert that samples are parsed
    assert order_form_parser.samples
    assert len(order_form_parser.samples) == get_nr_samples_excel(orderform)

    # THEN assert that the correct name was set
    assert order_form_parser.order_name == order_name

    # THEN it should determine the correct customer should have been parsed
    assert order_form_parser.customer_id == "cust000"
