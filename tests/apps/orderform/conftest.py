"""Fixtures for the orderform tests"""

import openpyxl
import pytest
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from cg.apps.orderform.excel_orderform_parser import ExcelOrderformParser


def get_nr_samples_excel(orderform_path: str) -> int:
    """Parse a excel orderform file and return the number of sample rows"""
    orderform_parser = ExcelOrderformParser()
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


@pytest.fixture(name="minimal_excel_sample")
def fixture_minimal_excel_sample() -> dict:
    return {
        "Sample/Name": "missingwell",
        "UDF/Data Analysis": "FLUFFY",
        "UDF/Sequencing Analysis": "RMLP05R800",
        "UDF/customer": "cust000",
    }


@pytest.fixture(name="mip_order_parser")
def fixture_mip_order_parser(mip_orderform: str) -> ExcelOrderformParser:
    """Return a orderform parser that have parsed a mip orderform in excel format"""
    order_form_parser = ExcelOrderformParser()
    order_form_parser.parse_orderform(excel_path=mip_orderform)
    return order_form_parser


@pytest.fixture(name="rml_order_parser")
def fixture_rml_order_parser(rml_orderform: str) -> ExcelOrderformParser:
    """Return a orderform parser that have parsed an orderform in excel format"""
    order_form_parser = ExcelOrderformParser()
    order_form_parser.parse_orderform(excel_path=rml_orderform)
    return order_form_parser


@pytest.fixture(name="fastq_order_parser")
def fixture_fastq_order_parser(fastq_orderform: str) -> ExcelOrderformParser:
    """Return a orderform parser that have parsed an orderform in excel format"""
    order_form_parser = ExcelOrderformParser()
    order_form_parser.parse_orderform(excel_path=fastq_orderform)
    return order_form_parser


@pytest.fixture(name="nr_samples_mip_orderform")
def fixture_nr_samples_mip_orderform(mip_orderform: str) -> int:
    """Return the number of samples in the mip orderform"""
    return get_nr_samples_excel(mip_orderform)


@pytest.fixture(name="nr_samples_rml_orderform")
def fixture_nr_samples_rml_orderform(rml_orderform: str) -> int:
    """Return the number of samples in the rml orderform"""
    return get_nr_samples_excel(rml_orderform)


@pytest.fixture(name="nr_samples_fastq_orderform")
def fixture_nr_samples_fastq_orderform(fastq_orderform: str) -> int:
    """Return the number of samples in the rml orderform"""
    return get_nr_samples_excel(fastq_orderform)


@pytest.fixture(name="mip_rna_orderform_sample")
def fixture_mip_rna_orderform_sample() -> dict:
    """Return a raw parsed mip rna sample in excel format"""
    return {
        "Sample/Name": "s1",
        "UDF/customer": "cust000",
        "UDF/Data Analysis": "MIP RNA",
        "UDF/Data Delivery": "Analysis",
        "UDF/Sequencing Analysis": "RNAPOAR025",
        "UDF/familyID": "c1",
        "UDF/Gender": "M",
        "UDF/tumor": "yes",
        "UDF/Source": "tissue (FFPE)",
        "UDF/priority": "research",
        "UDF/Process only if QC OK": "yes",
        "UDF/Volume (uL)": "1",
        "Container/Type": "96 well plate",
        "Container/Name": "plate1",
        "Sample/Well Location": "A:1",
        "UDF/Gene List": "",
        "UDF/Status": "",
        "UDF/motherID": "",
        "UDF/fatherID": "",
        "UDF/is_for_sample": "s1",
        "UDF/time_point": "0",
        "UDF/Capture Library version": "GMCKsolid",
        "UDF/Sample Buffer": 'Other (specify in "Comments")',
        "UDF/Formalin Fixation Time": "2",
        "UDF/Post Formalin Fixation Time": "3",
        "UDF/Tissue Block Size": "small",
        "UDF/Quantity": "4",
        "UDF/tumour purity": "5",
        "UDF/Comment": "other Elution buffer",
    }
