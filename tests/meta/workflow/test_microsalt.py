"""Tests for MicroSALT analysis."""
from cg.models.cg_config import CGConfig
from pathlib import Path


def test_qc_check_fail(
    clean_context_microsalt: CGConfig, microsalt_run_dir_path: Path, microsalt_lims_project: str
):
    # GIVEN a case that is to be stored

    # WHEN performing QC check

    # THEN the QC should fail
    pass


def test_qc_check_pass(
    clean_context_microsalt: CGConfig, microsalt_run_dir_path: Path, microsalt_lims_project: str
):
    # GIVEN a case that is to be stored

    # WHEN performing QC check

    # THEN the QC should pass
    pass
