"""Module for nextflow analysis API tests."""

import logging
from pathlib import Path
from typing import Any, Type
from unittest.mock import MagicMock, Mock, create_autospec

import pytest
from _pytest.fixtures import FixtureRequest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockerFixture

from cg.constants import Workflow
from cg.meta.workflow import nf_analysis as nf_analysis_module
from cg.meta.workflow.nallo import NalloAnalysisAPI
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.meta.workflow.rnafusion_analysis_api import RnafusionAnalysisAPI
from cg.meta.workflow.taxprofiler import TaxprofilerAnalysisAPI
from cg.meta.workflow.tomte import TomteAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.nf_analysis import WorkflowDeliverables
from cg.store.models import Sample
from cg.store.store import Store


@pytest.mark.parametrize(
    "workflow",
    [
        Workflow.RAREDISEASE,
        Workflow.RNAFUSION,
        Workflow.TAXPROFILER,
        Workflow.TOMTE,
    ],
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


def test_create_metrics_deliverables_content_nallo(
    nallo_case_id: str,
    nallo_context: CGConfig,
    nallo_metrics_deliverables: dict,
    nallo_mock_analysis_finish,
):
    """Test metrics deliverables file content function for nextflow pipelines."""

    # GIVEN a Nallo context and Nallo case id

    # GIVEN a Nextflow workflow analysis API and a list of QC metrics
    analysis_api: NfAnalysisAPI = nallo_context.meta_apis["analysis_api"]

    # WHEN writing the metrics deliverables file
    metrics_deliverables_content: dict[str, list[dict[str, Any]]] = (
        analysis_api.create_metrics_deliverables_content(nallo_case_id)
    )

    # THEN assert that the content created is correct
    assert metrics_deliverables_content == nallo_metrics_deliverables


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


@pytest.mark.parametrize(
    "analysis_api_class",
    [
        NalloAnalysisAPI,
        RarediseaseAnalysisAPI,
        RnafusionAnalysisAPI,
        TaxprofilerAnalysisAPI,
        TomteAnalysisAPI,
    ],
    ids=["Nallo", "raredisease", "rnafusion", "taxprofiler", "tomte"],
)
def test_get_deliverables_for_case(
    analysis_api_class: Type, context_config: dict, mocker: MockerFixture
):
    """Test getting the deliverables for a case with multiple samples for nextflow pipelines."""
    # GIVEN a database with two samples associated with a case
    sample_1 = create_autospec(Sample, internal_id="sample_1")
    sample_1.name = "Sample 1"
    sample_2 = create_autospec(Sample, internal_id="sample_2")
    sample_2.name = "Sample 2"
    status_db = create_autospec(Store)
    status_db.get_samples_by_case_id = Mock(return_value=[sample_1, sample_2])

    # GIVEN a Nf AnalysisAPI
    nf_analysis_api = analysis_api_class(config=CGConfig(**context_config))
    nf_analysis_api.status_db = status_db

    # GIVEN that the bundle_filenames file is read
    mock_yaml_reader: MagicMock = mocker.patch.object(
        nf_analysis_module,
        "read_yaml",
        return_value=[
            {
                "format": "json",
                "id": "SAMPLEID",
                "path": "PATHTOCASE/SAMPLENAME",
                "step": "step",
                "tag": "tag",
            },
            {"format": "json", "id": "CASEID", "path": "PATHTOCASE", "step": "step", "tag": "tag"},
        ],
    )

    # WHEN getting the workflow deliverables for a case
    deliverables: WorkflowDeliverables = nf_analysis_api.get_deliverables_for_case(
        case_id="test_case_id"
    )

    # THEN assert that the bundle_filenames file is read
    mock_yaml_reader.assert_called_once_with(Path("path/to/bundle/filenames.yaml"))

    # THEN assert that the returned workflow deliverables object has three entries
    assert len(deliverables.files) == 3

    # THEN the returned workflow deliverables object has the correct content
    assert deliverables.files[0].id == "sample_1"
    assert deliverables.files[1].id == "test_case_id"
    assert deliverables.files[2].id == "sample_2"
