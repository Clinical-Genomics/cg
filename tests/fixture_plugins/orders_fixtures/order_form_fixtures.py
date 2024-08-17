"""Fixtures for the orderform tests."""

from pathlib import Path

import openpyxl
import pytest
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from cg.apps.orderform.excel_orderform_parser import ExcelOrderformParser
from cg.constants.constants import FileFormat
from cg.constants.orderforms import Orderform
from cg.io.controller import ReadFile
from cg.models.orders.constants import OrderType


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


@pytest.fixture
def minimal_excel_sample() -> dict:
    return {
        "Sample/Name": "missingwell",
        "UDF/Data Analysis": "FLUFFY",
        "UDF/Sequencing Analysis": "RMLP05R800",
        "UDF/customer": "cust000",
    }


@pytest.fixture(scope="session")
def mip_order_parser(mip_orderform: str) -> ExcelOrderformParser:
    """Return a orderform parser that have parsed a mip orderform in excel format."""
    order_form_parser: ExcelOrderformParser = ExcelOrderformParser()
    order_form_parser.parse_orderform(excel_path=mip_orderform)
    return order_form_parser


@pytest.fixture(scope="session")
def rml_order_parser(rml_orderform: str) -> ExcelOrderformParser:
    """Return a orderform parser that have parsed an orderform in excel format."""
    order_form_parser: ExcelOrderformParser = ExcelOrderformParser()
    order_form_parser.parse_orderform(excel_path=rml_orderform)
    return order_form_parser


@pytest.fixture(scope="session")
def fastq_order_parser(fastq_orderform: str) -> ExcelOrderformParser:
    """Return a orderform parser that have parsed an orderform in excel format."""
    order_form_parser: ExcelOrderformParser = ExcelOrderformParser()
    order_form_parser.parse_orderform(excel_path=fastq_orderform)
    return order_form_parser


@pytest.fixture(scope="session")
def microbial_order_parser(microbial_orderform: str) -> ExcelOrderformParser:
    """Return a orderform parser that have parsed an orderform in excel format."""
    order_form_parser: ExcelOrderformParser = ExcelOrderformParser()
    order_form_parser.parse_orderform(excel_path=microbial_orderform)
    return order_form_parser


@pytest.fixture
def nr_samples_mip_orderform(mip_orderform: str) -> int:
    """Return the number of samples in the mip orderform."""
    return get_nr_samples_excel(mip_orderform)


@pytest.fixture
def nr_samples_rml_orderform(rml_orderform: str) -> int:
    """Return the number of samples in the RML orderform."""
    return get_nr_samples_excel(rml_orderform)


@pytest.fixture
def nr_samples_fastq_orderform(fastq_orderform: str) -> int:
    """Return the number of samples in the RML orderform."""
    return get_nr_samples_excel(fastq_orderform)


@pytest.fixture
def mip_rna_orderform_sample() -> dict:
    """Return a raw parsed mip RNA sample in excel format."""
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
    """Orderform fixture for microbial samples."""
    return Path(
        orderforms,
        f"{Orderform.MICROSALT}.{Orderform.get_current_orderform_version(Orderform.MICROSALT)}.microbial.xlsx",
    ).as_posix()


@pytest.fixture
def sarscov2_orderform(orderforms: Path) -> str:
    """Orderform fixture for sarscov2 samples."""
    return Path(
        orderforms,
        f"{Orderform.SARS_COV_2}.{Orderform.get_current_orderform_version(Orderform.SARS_COV_2)}.sarscov2.xlsx",
    ).as_posix()


@pytest.fixture(scope="session")
def rml_orderform(orderforms: Path) -> str:
    """Orderform fixture for RML samples."""
    return Path(
        orderforms,
        f"{Orderform.RML}.{Orderform.get_current_orderform_version(Orderform.RML)}.rml.xlsx",
    ).as_posix()


@pytest.fixture(scope="session")
def mip_order_to_submit(cgweb_orders_dir: Path) -> dict:
    """Load an example MIP order."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=Path(cgweb_orders_dir, "mip.json")
    )


@pytest.fixture(scope="session")
def mip_rna_order_to_submit(cgweb_orders_dir: Path) -> dict:
    """Load an example RNA order."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=Path(cgweb_orders_dir, "mip_rna.json")
    )


@pytest.fixture(scope="session")
def tomte_order_to_submit(cgweb_orders_dir: Path) -> dict:
    """Load an example TOMTE order."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=Path(cgweb_orders_dir, "tomte.json")
    )


@pytest.fixture(scope="session")
def rnafusion_order_to_submit(cgweb_orders_dir: Path) -> dict:
    """Load an example RNA order."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=Path(cgweb_orders_dir, "rnafusion.json")
    )


@pytest.fixture(scope="session")
def fastq_order_to_submit(cgweb_orders_dir) -> dict:
    """Load an example FASTQ order."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=Path(cgweb_orders_dir, "fastq.json")
    )


@pytest.fixture(scope="session")
def rml_order_to_submit(cgweb_orders_dir: Path) -> dict:
    """Load an example RML order."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=Path(cgweb_orders_dir, "rml.json")
    )


@pytest.fixture(scope="session")
def metagenome_order_to_submit(cgweb_orders_dir: Path) -> dict:
    """Load an example metagenome order."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=Path(cgweb_orders_dir, "metagenome.json")
    )


@pytest.fixture(scope="session")
def microbial_order_to_submit(cgweb_orders_dir: Path) -> dict:
    """Load an example microbial order."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=Path(cgweb_orders_dir, "microsalt.json")
    )


@pytest.fixture(scope="session")
def sarscov2_order_to_submit(cgweb_orders_dir: Path) -> dict:
    """Load an example sarscov2 order."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=Path(cgweb_orders_dir, "sarscov2.json")
    )


@pytest.fixture(scope="session")
def balsamic_order_to_submit(cgweb_orders_dir: Path) -> dict:
    """Load an example cancer order."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=Path(cgweb_orders_dir, "balsamic.json")
    )


@pytest.fixture(scope="session")
def balsamic_orderform(orderforms: Path) -> str:
    """Orderform fixture for Balsamic samples."""
    return Path(
        orderforms,
        f"{Orderform.BALSAMIC}.{Orderform.get_current_orderform_version(Orderform.BALSAMIC)}.balsamic.xlsx",
    ).as_posix()


@pytest.fixture(scope="session")
def balsamic_qc_orderform(orderforms: Path) -> str:
    """Orderform fixture for Balsamic QC samples."""
    return Path(
        orderforms,
        f"{Orderform.BALSAMIC_QC}.{Orderform.get_current_orderform_version(Orderform.BALSAMIC_QC)}.balsamic_qc.xlsx",
    ).as_posix()


@pytest.fixture(scope="session")
def balsamic_umi_orderform(orderforms: Path) -> str:
    """Orderform fixture for Balsamic UMI samples."""
    return Path(
        orderforms,
        f"{Orderform.BALSAMIC_UMI}.{Orderform.get_current_orderform_version(Orderform.BALSAMIC_UMI)}.balsamic_umi.xlsx",
    ).as_posix()


@pytest.fixture(scope="session")
def fastq_orderform(orderforms: Path):
    """Orderform fixture for FASTQ samples."""
    return Path(
        orderforms,
        f"{Orderform.FASTQ}.{Orderform.get_current_orderform_version(Orderform.FASTQ)}.fastq.xlsx",
    ).as_posix()


@pytest.fixture(scope="session")
def metagenome_orderform(orderforms: Path) -> str:
    """Orderform fixture for metagenome samples."""
    return Path(
        orderforms,
        f"{Orderform.METAGENOME}.{Orderform.get_current_orderform_version(Orderform.METAGENOME)}.metagenome.xlsx",
    ).as_posix()


@pytest.fixture(scope="session")
def mip_orderform(orderforms: Path) -> str:
    """Orderform fixture for MIP samples."""
    return Path(
        orderforms,
        f"{Orderform.MIP_DNA}.{Orderform.get_current_orderform_version(Orderform.MIP_DNA)}.mip.xlsx",
    ).as_posix()


@pytest.fixture(scope="session")
def mip_rna_orderform(orderforms: Path) -> str:
    """Orderform fixture for MIP RNA samples."""
    return Path(
        orderforms,
        f"{Orderform.MIP_RNA}.{Orderform.get_current_orderform_version(Orderform.MIP_RNA)}.mip_rna.xlsx",
    ).as_posix()


@pytest.fixture(scope="session")
def rnafusion_orderform(orderforms: Path) -> str:
    """Orderform fixture for MIP RNA samples."""
    return Path(
        orderforms,
        f"{Orderform.RNAFUSION}.{Orderform.get_current_orderform_version(Orderform.RNAFUSION)}.rnafusion.xlsx",
    ).as_posix()


@pytest.fixture(scope="session")
def mip_uploaded_json_order(orderforms: Path) -> str:
    """JSON orderform fixture for MIP DNA samples."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=Path(orderforms, "mip_uploaded_json_orderform.json")
    )


@pytest.fixture(scope="session")
def balsamic_uploaded_json_order(orderforms: Path) -> str:
    """JSON orderform fixture for BALSAMIC samples."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON,
        file_path=Path(orderforms, "balsamic_uploaded_json_orderform.json"),
    )


@pytest.fixture(scope="session")
def fluffy_uploaded_json_order(orderforms: Path) -> dict:
    """Load an example Fluffy order."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=Path(orderforms, "NIPT-json.json")
    )


@pytest.fixture(scope="session")
def json_order_list(
    mip_uploaded_json_order,
    fluffy_uploaded_json_order,
    balsamic_uploaded_json_order,
) -> dict[str, dict]:
    """Return a dict of orders that can be uploaded in the json format."""
    return {
        OrderType.MIP_DNA: mip_uploaded_json_order,
        OrderType.FLUFFY: fluffy_uploaded_json_order,
        OrderType.BALSAMIC: balsamic_uploaded_json_order,
    }
