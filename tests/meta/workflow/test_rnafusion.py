"""Module for Rnafusion analysis API tests."""
from typing import List

from cg.models.deliverables.metric_deliverables import MetricsBase

from cg.models.cg_config import CGConfig
from cg.models.rnafusion.analysis import RnafusionAnalysis

from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI
from tests.cli.workflow.rnafusion.conftest import (
    fixture_rnafusion_context,
    fixture_rnafusion_housekeeper,
    fixture_rnafusion_housekeeper_dir,
    fixture_rnafusion_multiqc_json_metrics,
    fixture_rnafusion_mock_fastq_files,
    fixture_rnafusion_fastq_file_l_1_r_1,
    fixture_rnafusion_fastq_file_l_1_r_2,
    fixture_rnafusion_sample_id,
    fixture_rnafusion_case_id,
    fixture_no_sample_case_id,
    mock_analysis_finish,
)


def test_parse_analysis(
    rnafusion_context: CGConfig,
    rnafusion_case_id: str,
    rnafusion_sample_id: str,
    rnafusion_multiqc_json_metrics: dict,
    rnafusion_metrics: dict,
    mock_analysis_finish,
):
    """Test Rnafusion output analysis files parsing."""

    # GIVEN a Rnafusion analysis API and a list of QC metrics
    analysis_api: RnafusionAnalysisAPI = rnafusion_context.meta_apis["analysis_api"]
    qc_metrics: List[MetricsBase] = analysis_api.get_multiqc_json_metrics(case_id=rnafusion_case_id)

    # WHEN extracting the analysis model
    analysis_model: RnafusionAnalysis = analysis_api.parse_analysis(qc_metrics_raw=qc_metrics)

    # THEN the analysis model and its content should have been correctly extracted
    assert analysis_model.sample_metrics[rnafusion_sample_id] == rnafusion_metrics


def test_get_latest_metadata(
    rnafusion_context: CGConfig, rnafusion_case_id: str, mock_analysis_finish
):
    """Test retrieval of Rnafusion latest metadata."""

    # GIVEN a Rnafusion analysis API and a list of QC metrics
    analysis_api: RnafusionAnalysisAPI = rnafusion_context.meta_apis["analysis_api"]

    # WHEN collecting the latest metadata
    latest_metadata: RnafusionAnalysis = analysis_api.get_latest_metadata(case_id=rnafusion_case_id)

    # THEN the latest metadata should have been parsed
    assert latest_metadata
    assert latest_metadata.sample_metrics
