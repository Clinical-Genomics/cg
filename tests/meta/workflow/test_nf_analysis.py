"""Module for nf-core analysis API tests."""

import logging
from typing import Any

import pytest
from _pytest.logging import LogCaptureFixture
from pathlib import Path

from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.models.cg_config import CGConfig
from tests.cli.workflow.conftest import deliverables_template_content


@pytest.mark.parametrize(
    ("context", "metrics_deliverables", "case_id", "analysis_finish"),
    [
        (
            "rnafusion_context",
            "rnafusion_metrics_deliverables",
            "rnafusion_case_id",
            "rnafusion_mock_analysis_finish",
        ),
        (
            "taxprofiler_context",
            "taxprofiler_metrics_deliverables",
            "taxprofiler_case_id",
            "taxprofiler_mock_analysis_finish",
        ),
    ],
)
def test_create_metrics_deliverables_content(
    context: str,
    case_id: str,
    metrics_deliverables: str,
    caplog: LogCaptureFixture,
    analysis_finish,
    request,
):
    """Test metrics deliverables file content function for Taxprofiler and Rnafusion."""

    caplog.set_level(logging.INFO)

    # GIVEN each fixture is being initialised
    context: CGConfig = request.getfixturevalue(context)
    metrics_deliverables: dict = request.getfixturevalue(metrics_deliverables)
    case_id: str = request.getfixturevalue(case_id)
    request.getfixturevalue(analysis_finish)

    # GIVEN a Nextflow workflow analysis API and a list of QC metrics
    analysis_api: NfAnalysisAPI = context.meta_apis["analysis_api"]

    # WHEN writing the metrics deliverables file
    metrics_deliverables_content: dict[str, list[dict[str, Any]]] = (
        analysis_api.create_metrics_deliverables_content(case_id)
    )

    # THEN assert that the content created is correct
    assert metrics_deliverables_content == metrics_deliverables


@pytest.mark.parametrize(
    ("context", "case_id"),
    [
        (
            "rnafusion_context",
            "rnafusion_case_id",
        ),
        (
            "taxprofiler_context",
            "taxprofiler_case_id",
        ),
    ],
)
def test_get_formatted_file_deliverable(
    context: str,
    case_id: str,
    sample_id: str,
    sample_name: str,
    caplog: LogCaptureFixture,
    deliverables_template_content,
    request,
):
    """Test the formatted file deliverable with the case and sample attributes for Taxprofiler and Rnafusion."""

    caplog.set_level(logging.INFO)

    # GIVEN each fixture is being initialised
    context: CGConfig = request.getfixturevalue(context)
    case_id: str = request.getfixturevalue(case_id)

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
