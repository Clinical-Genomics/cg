"""Fixtures for the orderform tests"""
import json
from pathlib import Path

import openpyxl
import pytest
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from cg.apps.orderform.excel_orderform_parser import ExcelOrderformParser
from cg.constants.orderforms import Orderform, ORDERFORM_VERSIONS


def get_nr_samples_excel(orderform_path: str) -> int:
    """Parse a excel orderform file and return the number of sample rows"""
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


@pytest.fixture(name="minimal_excel_sample")
def fixture_minimal_excel_sample() -> dict:
    return {
        "Sample/Name": "missingwell",
        "UDF/Data Analysis": "FLUFFY",
        "UDF/Sequencing Analysis": "RMLP05R800",
        "UDF/customer": "cust000",
    }


@pytest.fixture(scope="session", name="mip_order_parser")
def fixture_mip_order_parser(mip_orderform: str) -> ExcelOrderformParser:
    """Return a orderform parser that have parsed a mip orderform in excel format"""
    order_form_parser: ExcelOrderformParser = ExcelOrderformParser()
    order_form_parser.parse_orderform(excel_path=mip_orderform)
    return order_form_parser


@pytest.fixture(scope="session", name="rml_order_parser")
def fixture_rml_order_parser(rml_orderform: str) -> ExcelOrderformParser:
    """Return a orderform parser that have parsed an orderform in excel format"""
    order_form_parser: ExcelOrderformParser = ExcelOrderformParser()
    order_form_parser.parse_orderform(excel_path=rml_orderform)
    return order_form_parser


@pytest.fixture(scope="session", name="fastq_order_parser")
def fixture_fastq_order_parser(fastq_orderform: str) -> ExcelOrderformParser:
    """Return a orderform parser that have parsed an orderform in excel format"""
    order_form_parser: ExcelOrderformParser = ExcelOrderformParser()
    order_form_parser.parse_orderform(excel_path=fastq_orderform)
    return order_form_parser


@pytest.fixture(scope="session", name="microbial_order_parser")
def fixture_microbial_order_parser(microbial_orderform: str) -> ExcelOrderformParser:
    """Return a orderform parser that have parsed an orderform in excel format"""
    order_form_parser: ExcelOrderformParser = ExcelOrderformParser()
    order_form_parser.parse_orderform(excel_path=microbial_orderform)
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
        "UDF/Capture Library version": "GMCKsolid",
        "UDF/Sample Buffer": 'Other (specify in "Comments")',
        "UDF/Formalin Fixation Time": "2",
        "UDF/Post Formalin Fixation Time": "3",
        "UDF/Tissue Block Size": "small",
        "UDF/Quantity": "4",
        "UDF/tumour purity": "5",
        "UDF/Comment": "other Elution buffer",
    }


# Orderform fixtures


@pytest.fixture(scope="session")
def microbial_orderform(orderforms: Path) -> str:
    """Orderform fixture for microbial samples"""
    return Path(
        orderforms,
        f"{Orderform.MICROSALT}.{ORDERFORM_VERSIONS[Orderform.MICROSALT]}.microbial.xlsx",
    ).as_posix()


@pytest.fixture
def sarscov2_orderform(orderforms: Path) -> str:
    """Orderform fixture for sarscov2 samples"""
    return Path(
        orderforms,
        f"{Orderform.SARS_COV_2}.{ORDERFORM_VERSIONS[Orderform.SARS_COV_2]}.sarscov2.xlsx",
    ).as_posix()


@pytest.fixture(scope="session")
def rml_orderform(orderforms: Path) -> str:
    """Orderform fixture for RML samples"""
    return Path(
        orderforms, f"{Orderform.RML}.{ORDERFORM_VERSIONS[Orderform.RML]}.rml.xlsx"
    ).as_posix()


@pytest.fixture(scope="session")
def mip_order_to_submit(orderforms: Path) -> dict:
    """Load an example scout order."""
    return json.load(open(Path(orderforms, "mip.json")))


@pytest.fixture(scope="session")
def mip_rna_order_to_submit(orderforms: Path) -> dict:
    """Load an example rna order."""
    return json.load(open(Path(orderforms, "mip_rna.json")))


@pytest.fixture(scope="session")
def fastq_order_to_submit(orderforms) -> dict:
    """Load an example fastq order."""
    return json.load(open(Path(orderforms, "fastq.json")))


@pytest.fixture(scope="session")
def rml_order_to_submit(orderforms: Path) -> dict:
    """Load an example rml order."""
    return json.load(open(Path(orderforms, "rml.json")))


@pytest.fixture(scope="session")
def fluffy_order_to_submit(orderforms: Path) -> dict:
    """Load an example fluffy order."""
    return json.load(open(Path(orderforms, "rml.json")))


@pytest.fixture(scope="session")
def metagenome_order_to_submit(orderforms: Path) -> dict:
    """Load an example metagenome order."""
    return json.load(open(Path(orderforms, "metagenome.json")))


@pytest.fixture(scope="session")
def microbial_order_to_submit(orderforms: Path) -> dict:
    """Load an example microbial order."""
    return json.load(open(Path(orderforms, "microsalt.json")))


@pytest.fixture(scope="session")
def sarscov2_order_to_submit(orderforms: Path) -> dict:
    """Load an example sarscov2 order."""
    return json.load(open(Path(orderforms, "sarscov2.json")))


@pytest.fixture(scope="session")
def balsamic_order_to_submit(orderforms: Path) -> dict:
    """Load an example cancer order."""
    return json.load(open(Path(orderforms, "balsamic.json")))


@pytest.fixture(scope="session")
def balsamic_orderform(orderforms: Path) -> str:
    """Orderform fixture for Balsamic samples"""
    _file = Path(
        orderforms, f"{Orderform.BALSAMIC}.{ORDERFORM_VERSIONS[Orderform.BALSAMIC]}.balsamic.xlsx"
    )
    return str(_file)


@pytest.fixture(scope="session")
def balsamic_qc_orderform(orderforms: Path) -> str:
    """Orderform fixture for Balsamic QC samples"""
    _file = Path(
        orderforms,
        f"{Orderform.BALSAMIC_QC}.{ORDERFORM_VERSIONS[Orderform.BALSAMIC_QC]}.balsamic_qc.xlsx",
    )
    return str(_file)


@pytest.fixture(scope="session")
def balsamic_umi_orderform(orderforms: Path) -> str:
    """Orderform fixture for Balsamic UMI samples"""
    _file = Path(
        orderforms,
        f"{Orderform.BALSAMIC_UMI}.{ORDERFORM_VERSIONS[Orderform.BALSAMIC_UMI]}.balsamic_umi.xlsx",
    )
    return str(_file)


@pytest.fixture(scope="session")
def fastq_orderform(orderforms: Path):
    """Orderform fixture for fastq samples"""
    _file = Path(orderforms, f"{Orderform.FASTQ}.{ORDERFORM_VERSIONS[Orderform.FASTQ]}.fastq.xlsx")
    return str(_file)


@pytest.fixture(scope="session")
def metagenome_orderform(orderforms: Path) -> str:
    """Orderform fixture for metagenome samples"""
    _file = Path(
        orderforms,
        f"{Orderform.METAGENOME}.{ORDERFORM_VERSIONS[Orderform.METAGENOME]}.metagenome.xlsx",
    )
    return str(_file)


@pytest.fixture(scope="session")
def mip_orderform(orderforms: Path) -> str:
    """Orderform fixture for MIP samples"""
    _file = Path(
        orderforms, f"{Orderform.MIP_DNA}.{ORDERFORM_VERSIONS[Orderform.MIP_DNA]}.mip.xlsx"
    )
    return str(_file)


@pytest.fixture(scope="session")
def mip_rna_orderform(orderforms: Path) -> str:
    """Orderform fixture for MIP RNA samples"""
    _file = Path(
        orderforms, f"{Orderform.MIP_RNA}.{ORDERFORM_VERSIONS[Orderform.MIP_RNA]}.mip_rna.xlsx"
    )
    return str(_file)
