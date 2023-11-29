"""Moldule to test the deliverables parser functions."""
from pathlib import Path

import pytest

from cg.apps.deliverables_metrics_parser.parser.deliverables_parser import (
    get_metrics_deliverables_file_path,
)
from cg.constants.pipeline import Pipeline


@pytest.mark.parametrize(
    "pipeline,expected_path",
    [
        (Pipeline.BALSAMIC, "balsamic_metrics_deliverables_path"),
        (Pipeline.MIPDNA, "mip_dna_metrics_deliverables_path"),
        (Pipeline.MIPRNA, "mip_rna_metrics_deliverables_path"),
        (Pipeline.MUTANT, "mutant_metrics_deliverables_path"),
        (Pipeline.RNAFUSION, "rna_fusion_metrics_deliverables_path"),
    ],
)
def test_get_metrics_deliverables_file_path(
    pipeline: str, expected_path: str, case_id: str, request
):
    """Test get the metrics deliverables path for a case and pipeline."""
    # GIVEN a case id and a pipeline
    file_path: Path = request.getfixturevalue(expected_path)

    # WHEN retrieving the path for the metrics deliverables file for the pipeline and case
    metrics_deliverables_file_path: Path = get_metrics_deliverables_file_path(
        pipeline=pipeline, case_id=case_id
    )

    # THEN the path is as expected
    assert metrics_deliverables_file_path == file_path
