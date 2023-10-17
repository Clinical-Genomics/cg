from pathlib import Path

import pytest

from cg.constants.constants import FileFormat
from cg.io.controller import ReadFile


@pytest.fixture(name="balsamic_config_path")
def balsamic_config_path(fixtures_dir) -> Path:
    """Returns path to BALSAMIC case_config.json"""

    return Path(fixtures_dir, "apps", "balsamic", "case", "config.json")


@pytest.fixture(name="balsamic_metrics_path")
def balsamic_metrics_path(fixtures_dir) -> Path:
    """Returns path to BALSAMIC case_metrics_deliverables.yaml"""

    return Path(fixtures_dir, "apps", "balsamic", "case", "metrics_deliverables.yaml")


@pytest.fixture(name="balsamic_config_raw")
def balsamic_config(balsamic_config_path) -> dict:
    """Return BALSAMIC config file as a dictionary"""

    config: dict = ReadFile.get_content_from_file(
        file_format=FileFormat.YAML, file_path=balsamic_config_path
    )
    return config


@pytest.fixture(name="balsamic_metrics_raw")
def balsamic_metrics(balsamic_metrics_path) -> dict:
    """Return BALSAMIC metrics file as a dictionary"""

    metrics: dict = ReadFile.get_content_from_file(
        file_format=FileFormat.YAML, file_path=balsamic_metrics_path
    )
    return metrics
