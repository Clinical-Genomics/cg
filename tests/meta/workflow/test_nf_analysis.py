"""Module for nextflow analysis API tests."""

import logging
from typing import Any

import pytest
from _pytest.fixtures import FixtureRequest
from _pytest.logging import LogCaptureFixture

from cg.constants import Workflow
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.models.cg_config import CGConfig
from tests.cli.workflow.conftest import deliverables_template_content


@pytest.mark.parametrize(
    "workflow",
    [Workflow.RAREDISEASE, Workflow.RNAFUSION, Workflow.TAXPROFILER, Workflow.TOMTE],
)
def test_create_metrics_deliverables_content(
    workflow: Workflow,
    caplog: LogCaptureFixture,
    request: FixtureRequest,
):
    """Test metrics deliverables file content function for nextflow pipelines."""
    caplog.set_level(logging.INFO)

    # GIVEN each fixture is being initialised
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")

    metrics_deliverables: dict = request.getfixturevalue(f"{workflow}_metrics_deliverables")
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")
    request.getfixturevalue(f"{workflow}_mock_analysis_finish")

    # GIVEN a Nextflow workflow analysis API and a list of QC metrics
    analysis_api: NfAnalysisAPI = context.meta_apis["analysis_api"]

    # WHEN writing the metrics deliverables file
    metrics_deliverables_content: dict[str, list[dict[str, Any]]] = (
        analysis_api.create_metrics_deliverables_content(case_id)
    )

    # THEN assert that the content created is correct
    assert metrics_deliverables_content == metrics_deliverables


@pytest.mark.parametrize(
    "workflow",
    [Workflow.RNAFUSION, Workflow.TAXPROFILER, Workflow.TOMTE],
)
def test_get_formatted_file_deliverable(
    workflow: Workflow,
    sample_id: str,
    sample_name: str,
    caplog: LogCaptureFixture,
    deliverables_template_content,
    request: FixtureRequest,
):
    """Test the formatted file deliverable with the case and sample attributes for nextflow pipelines."""

    caplog.set_level(logging.INFO)

    # GIVEN each fixture is being initialised
    context: CGConfig = request.getfixturevalue(f"{workflow}_context")
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")

    caplog.set_level(logging.INFO)
    analysis_api: NfAnalysisAPI = context.meta_apis["analysis_api"]

    # WHEN formatting the template
    for field in deliverables_template_content:
        formatted_file_deliverable = analysis_api.get_formatted_file_deliverable(
            field,
            case_id,
            sample_id,
            sample_name,
            "get_case_path",
        )

        # THEN assert that the new path is correct
        assert "get_case_path" in formatted_file_deliverable.path
