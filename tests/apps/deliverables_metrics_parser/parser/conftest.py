"""Fixtures for the deliverables metrics parser."""
from pathlib import Path

import pytest


@pytest.fixture
def balsamic_metrics_deliverables_path(case_id: str) -> Path:
    return Path(
        f"/home/proj/production/cancer/cases/{case_id}/analysis/qc/{case_id}_metrics_deliverables.yaml"
    )


@pytest.fixture()
def mip_dna_metrics_deliverables_path(case_id: str) -> Path:
    return Path(
        f"/home/proj/production/rare-disease/cases/{case_id}/analysis/{case_id}_metrics_deliverables.yaml"
    )


@pytest.fixture()
def mip_rna_metrics_deliverables_path(case_id: str) -> Path:
    return Path(
        f"/home/proj/production/rare-disease/cases/{case_id}/analysis/{case_id}_metrics_deliverables.yaml"
    )


@pytest.fixture()
def mutant_metrics_deliverables_path(case_id: str) -> Path:
    return Path(
        f"/home/proj/production/mutant/cases/{case_id}/results/{case_id}_metrics_deliverables.yaml"
    )


@pytest.fixture()
def rna_fusion_metrics_deliverables_path(case_id: str) -> Path:
    return Path(
        f"/home/proj/production/rnafusion/cases/{case_id}/{case_id}_metrics_deliverables.yaml"
    )


@pytest.fixture()
def mip_dna_metrics_deliverables_file_path(fixtures_dir: Path) -> Path:
    """Return the path to a MIP DNA metrics deliverables file."""
    return Path(
        fixtures_dir,
        "apps",
        "deliverables_metrics_parser",
        "mip_dna_deliverables_metrics.yaml",
    )
