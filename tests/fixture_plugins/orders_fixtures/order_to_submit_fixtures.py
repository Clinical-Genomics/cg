"""Fixtures for orders parsed from JSON files into dictionaries."""

from pathlib import Path

import pytest

from cg.constants.constants import FileFormat
from cg.io.controller import ReadFile


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
def fluffy_order_to_submit(cgweb_orders_dir: Path) -> dict:
    """Load an example Fluffy order."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=Path(cgweb_orders_dir, "fluffy.json")
    )


@pytest.fixture(scope="session")
def metagenome_order_to_submit(cgweb_orders_dir: Path) -> dict:
    """Load an example metagenome order."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=Path(cgweb_orders_dir, "metagenome.json")
    )


@pytest.fixture(scope="session")
def microbial_fastq_order_to_submit(cgweb_orders_dir: Path) -> dict:
    """Load an example microbial order."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=Path(cgweb_orders_dir, "microbial_fastq.json")
    )


@pytest.fixture(scope="session")
def microbial_order_to_submit(cgweb_orders_dir: Path) -> dict:
    """Load an example microbial order."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=Path(cgweb_orders_dir, "microsalt.json")
    )


@pytest.fixture(scope="session")
def mip_dna_order_to_submit(cgweb_orders_dir: Path) -> dict:
    """Load an example MIP-DNA order."""
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
def rml_order_to_submit(cgweb_orders_dir: Path) -> dict:
    """Load an example RML order."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=Path(cgweb_orders_dir, "rml.json")
    )


@pytest.fixture(scope="session")
def rnafusion_order_to_submit(cgweb_orders_dir: Path) -> dict:
    """Load an example RNA order."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=Path(cgweb_orders_dir, "rnafusion.json")
    )


@pytest.fixture(scope="session")
def sarscov2_order_to_submit(cgweb_orders_dir: Path) -> dict:
    """Load an example sarscov2 order."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=Path(cgweb_orders_dir, "sarscov2.json")
    )


@pytest.fixture(scope="session")
def taxprofiler_order_to_submit(cgweb_orders_dir: Path) -> dict:
    """Load an example Taxprofiler order."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=Path(cgweb_orders_dir, "taxprofiler.json")
    )


@pytest.fixture(scope="session")
def tomte_order_to_submit(cgweb_orders_dir: Path) -> dict:
    """Load an example TOMTE order."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=Path(cgweb_orders_dir, "tomte.json")
    )
