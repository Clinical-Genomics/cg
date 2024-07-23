"""Module for PacBio fixtures returning service objects."""

from pathlib import Path

import pytest

from cg.services.pacbio.metrics.metrics_parser import PacBioMetricsParser


@pytest.fixture
def pac_bio_metrics_parser(pac_bio_smrt_cell_dir_1_a01: Path) -> PacBioMetricsParser:
    """Return a PacBio metrics parser."""
    return PacBioMetricsParser(pac_bio_smrt_cell_dir_1_a01)
