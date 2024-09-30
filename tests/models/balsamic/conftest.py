from pathlib import Path

import pytest

from cg.constants.constants import FileFormat
from cg.io.controller import ReadFile


@pytest.fixture
def balsamic_tga_config_path(fixtures_dir) -> Path:
    """Returns path to a TGA BALSAMIC case_config.json"""

    return Path(fixtures_dir, "apps", "balsamic", "tga_case", "config.json")


@pytest.fixture
def balsamic_tga_metrics_path(fixtures_dir) -> Path:
    """Returns path to a TGA BALSAMIC case_metrics_deliverables.yaml"""

    return Path(fixtures_dir, "apps", "balsamic", "tga_case", "metrics_deliverables.yaml")


@pytest.fixture
def balsamic_tga_config_raw(balsamic_tga_config_path) -> dict:
    """Returna a TGA BALSAMIC config file as a dictionary"""

    config: dict = ReadFile.get_content_from_file(
        file_format=FileFormat.YAML, file_path=balsamic_tga_config_path
    )
    return config


@pytest.fixture
def balsamic_tga_metrics_raw(balsamic_tga_metrics_path) -> dict:
    """Return a TGA BALSAMIC metrics file as a dictionary"""

    metrics: dict = ReadFile.get_content_from_file(
        file_format=FileFormat.YAML, file_path=balsamic_tga_metrics_path
    )
    return metrics


@pytest.fixture
def balsamic_wgs_config_path(fixtures_dir) -> Path:
    """Returns path to a WGS BALSAMIC case_config.json"""

    return Path(fixtures_dir, "apps", "balsamic", "wgs_case", "config.json")


@pytest.fixture
def balsamic_wgs_metrics_path(fixtures_dir) -> Path:
    """Returns path to a WGS BALSAMIC case_metrics_deliverables.yaml"""

    return Path(fixtures_dir, "apps", "balsamic", "wgs_case", "metrics_deliverables.yaml")


@pytest.fixture
def balsamic_wgs_config_raw(balsamic_wgs_config_path) -> dict:
    """Return a WGS BALSAMIC config file as a dictionary"""

    config: dict = ReadFile.get_content_from_file(
        file_format=FileFormat.YAML, file_path=balsamic_wgs_config_path
    )
    return config


@pytest.fixture
def balsamic_wgs_metrics_raw(balsamic_wgs_metrics_path) -> dict:
    """Return a WGS BALSAMIC metrics file as a dictionary"""

    metrics: dict = ReadFile.get_content_from_file(
        file_format=FileFormat.YAML, file_path=balsamic_wgs_metrics_path
    )
    return metrics
