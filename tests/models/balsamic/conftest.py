from pathlib import Path
import pytest
import yaml


@pytest.fixture(name="balsamic_config_path")
def fixture_balsamic_config_path(fixtures_dir) -> Path:
    """Returns path to BALSAMIC case_config.json"""

    return Path(fixtures_dir, "apps", "balsamic", "case", "config.json")


@pytest.fixture(name="balsamic_metrics_path")
def fixture_balsamic_metrics_path(fixtures_dir) -> Path:
    """Returns path to BALSAMIC case_metrics_deliverables.yaml"""

    return Path(fixtures_dir, "apps", "balsamic", "case", "metrics_deliverables.yaml")


@pytest.fixture(name="balsamic_config_raw")
def fixture_balsamic_config(balsamic_config_path) -> dict:
    """Return BALSAMIC config file as a dictionary"""

    with open(Path(balsamic_config_path), "r") as stream:
        config = yaml.safe_load(stream)

    return config


@pytest.fixture(name="balsamic_metrics_raw")
def fixture_balsamic_metrics(balsamic_metrics_path) -> dict:
    """Return BALSAMIC metrics file as a dictionary"""

    with open(Path(balsamic_metrics_path), "r") as stream:
        metrics = yaml.safe_load(stream)

    return metrics
