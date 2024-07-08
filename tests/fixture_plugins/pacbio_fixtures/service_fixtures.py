"""Module for PacBio fixtures returning service objects."""

from pathlib import Path

import pytest

from cg.services.pacbio.metrics.metrics_parser import MetricsParser


@pytest.fixture
def pac_bio_metrics_parser(pac_bio_smrt_cell_dir: Path) -> MetricsParser:
    """Return a PacBio metrics parser."""
    return MetricsParser(pac_bio_smrt_cell_dir)
