from pathlib import Path

import pytest

from cg.constants.constants import FileFormat
from cg.io.controller import ReadFile
from cg.models.orders.constants import OrderType
from cg.models.orders.order import OrderIn


@pytest.fixture(scope="session")
def balsamic_order_to_submit(cgweb_orders_dir: Path) -> dict:
    """Load an example cancer order."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=Path(cgweb_orders_dir, "balsamic.json")
    )


@pytest.fixture(scope="session")
def fastq_order_to_submit(cgweb_orders_dir) -> dict:
    """Load an example FASTQ order."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=Path(cgweb_orders_dir, "fastq.json")
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


@pytest.fixture
def microbial_fastq_order_to_submit(cgweb_orders_dir: Path) -> dict:
    """Load an example microbial order."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=Path(cgweb_orders_dir, "microbial_fastq.json")
    )


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
def pacbio_order_to_submit(cgweb_orders_dir) -> dict:
    """Load an example PacBio order."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=Path(cgweb_orders_dir, "pacbio.json")
    )


@pytest.fixture(scope="session")
def rnafusion_order_to_submit(cgweb_orders_dir: Path) -> dict:
    """Load an example RNA order."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=Path(cgweb_orders_dir, "rnafusion.json")
    )


@pytest.fixture(scope="session")
def rml_order_to_submit(cgweb_orders_dir: Path) -> dict:
    """Load an example RML order."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=Path(cgweb_orders_dir, "rml.json")
    )


@pytest.fixture(scope="session")
def sarscov2_order_to_submit(cgweb_orders_dir: Path) -> dict:
    """Load an example sarscov2 order."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=Path(cgweb_orders_dir, "sarscov2.json")
    )


@pytest.fixture(scope="session")
def tomte_order_to_submit(cgweb_orders_dir: Path) -> dict:
    """Load an example TOMTE order."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=Path(cgweb_orders_dir, "tomte.json")
    )


@pytest.fixture(scope="session")
def all_orders_to_submit(
    balsamic_order_to_submit: dict,
    fastq_order_to_submit: dict,
    metagenome_order_to_submit: dict,
    microbial_order_to_submit: dict,
    mip_order_to_submit: dict,
    mip_rna_order_to_submit: dict,
    pacbio_order_to_submit: dict,
    rml_order_to_submit: dict,
    rnafusion_order_to_submit: dict,
    sarscov2_order_to_submit: dict,
) -> dict[str, OrderIn]:
    """Returns a dict of parsed order for each order type."""
    return {
        OrderType.BALSAMIC: OrderIn.parse_obj(balsamic_order_to_submit, project=OrderType.BALSAMIC),
        OrderType.FASTQ: OrderIn.parse_obj(fastq_order_to_submit, project=OrderType.FASTQ),
        OrderType.FLUFFY: OrderIn.parse_obj(rml_order_to_submit, project=OrderType.FLUFFY),
        OrderType.METAGENOME: OrderIn.parse_obj(
            metagenome_order_to_submit, project=OrderType.METAGENOME
        ),
        OrderType.MICROSALT: OrderIn.parse_obj(
            microbial_order_to_submit, project=OrderType.MICROSALT
        ),
        OrderType.MIP_DNA: OrderIn.parse_obj(mip_order_to_submit, project=OrderType.MIP_DNA),
        OrderType.MIP_RNA: OrderIn.parse_obj(mip_rna_order_to_submit, project=OrderType.MIP_RNA),
        OrderType.PACBIO_LONG_READ: OrderIn.parse_obj(
            pacbio_order_to_submit, project=OrderType.PACBIO_LONG_READ
        ),
        OrderType.RML: OrderIn.parse_obj(rml_order_to_submit, project=OrderType.RML),
        OrderType.RNAFUSION: OrderIn.parse_obj(
            rnafusion_order_to_submit, project=OrderType.RNAFUSION
        ),
        OrderType.SARS_COV_2: OrderIn.parse_obj(
            sarscov2_order_to_submit, project=OrderType.SARS_COV_2
        ),
    }
