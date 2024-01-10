"""Module to test the deliverables parser functions."""
from pathlib import Path

import pytest
from _pytest.fixtures import FixtureRequest

from cg.apps.deliverables_metrics_parser.models.pipeline_metrics_deliverables import (
    MIPDNAMetricsDeliverables,
)
from cg.apps.deliverables_metrics_parser.parser.deliverables_parser import (
    get_metrics_deliverables_file_path,
    parse_metrics_deliverables_file,
    read_metrics_deliverables,
)
from cg.constants.constants import Pipeline


@pytest.mark.parametrize(
    "pipeline, expected_path",
    [
        (Pipeline.BALSAMIC, "balsamic_metrics_deliverables_path"),
        (Pipeline.MIP_DNA, "mip_dna_metrics_deliverables_path"),
        (Pipeline.MIP_RNA, "mip_rna_metrics_deliverables_path"),
        (Pipeline.SARS_COV_2, "mutant_metrics_deliverables_path"),
        (Pipeline.RNAFUSION, "rna_fusion_metrics_deliverables_path"),
    ],
)
def test_get_metrics_deliverables_file_path(
    pipeline: str, expected_path: str, case_id: str, request: FixtureRequest
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


def test_read_metrics_deliverables_file(mip_dna_metrics_deliverables_file_path: Path):
    """Test to read the content of a metrics deliverables file."""
    # GIVEN a file path to a metrics deliverables file

    # WHEN reading the content
    content: list[dict] = read_metrics_deliverables(
        file_path=mip_dna_metrics_deliverables_file_path
    )

    # THEN the content has been read
    assert content


def test_parse_metrics_deliverables_file(mip_dna_metrics_deliverables_file_path: Path, mocker):
    """Test parsing of the metrics deliverables file."""
    # GIVEN a file path to a metrics deliverables file

    # WHEN parsing the metrics deliverables file
    mocker.patch(
        "cg.apps.deliverables_metrics_parser.parser.deliverables_parser.get_metrics_deliverables_file_path",
        return_value=mip_dna_metrics_deliverables_file_path,
    )
    parsed_metrics: list[MIPDNAMetricsDeliverables] = parse_metrics_deliverables_file(
        pipeline=Pipeline.MIPDNA, case_id="some_case"
    )

    # THEN a list of metrics deliverables models is returned
    assert isinstance(parsed_metrics[0], MIPDNAMetricsDeliverables)
