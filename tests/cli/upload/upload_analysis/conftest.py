"""Fixtures for upload analysis tests"""

import json
from pathlib import Path

import pytest

from tests.mocks.process_mock import ProcessMock


@pytest.fixture(name="fluffy_sample_id")
def fixture_fluffy_sample_id() -> str:
    return "2020-23219-05"


@pytest.fixture(name="fluffy_dir")
def fixture_fluffy_dir(apps_dir: Path) -> Path:
    return apps_dir / "fluffy"


@pytest.fixture(name="fluffy_deliverables_file")
def fixture_fluffy_deliverables_file(fluffy_dir: Path) -> Path:
    return fluffy_dir / "deliverables.yaml"


@pytest.fixture(name="fluffy_summary_file")
def fixture_fluffy_summary_file(fluffy_dir: Path) -> Path:
    return fluffy_dir / "summary.csv"


@pytest.fixture(name="fluffy_report_file")
def fixture_fluffy_report_file(fluffy_dir: Path) -> Path:
    return fluffy_dir / "multiqc_report.html"


@pytest.fixture(name="fluffy_analysis_file")
def fixture_fluffy_analysis_file(fluffy_dir: Path, fluffy_sample_id: str) -> Path:
    return fluffy_dir / fluffy_sample_id / f"{fluffy_sample_id}.WCXpredict_aberrations.filt.bed"


@pytest.fixture(name="fluffy_hermes_output")
def fixture_fluffy_hermes_output(
    case_id: str,
    fluffy_sample_id: str,
    fluffy_summary_file: Path,
    fluffy_report_file: Path,
    fluffy_analysis_file: Path,
) -> dict:
    """Return converted deliverables output from hermes to fluffy"""
    _output = {
        "bundle_id": case_id,
        "files": [
            {
                "path": str(fluffy_summary_file),
                "tags": ["metrics", case_id, "nipt"],
            },
            {
                "path": str(fluffy_report_file),
                "tags": ["multiqc-html", case_id, "nipt"],
            },
            {
                "path": str(fluffy_analysis_file),
                "tags": ["wisecondor", "cnv", fluffy_sample_id, "nipt"],
            },
        ],
        "pipeline": "fluffy",
    }
    return _output


@pytest.fixture(name="hermes_process")
def fixture_hermes_process() -> ProcessMock:
    """Return a mocked hermes process"""
    return ProcessMock(binary="hermes")


@pytest.fixture(name="fluffy_process")
def fixture_fluffy_process(hermes_process: ProcessMock, fluffy_hermes_output: dict) -> ProcessMock:
    """Return a process mock populated with some fluffy hermes output"""
    hermes_process.set_stdout(text=json.dumps(fluffy_hermes_output))
    return hermes_process
