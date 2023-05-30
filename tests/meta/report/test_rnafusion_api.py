"""Test module for the Rnafusion delivery report API."""
from typing import Dict

from cg.models.report.metadata import RnafusionSampleMetadataModel
from cg.models.rnafusion.analysis import RnafusionAnalysis

from cg.meta.report.rnafusion import RnafusionReportAPI

from cg.store.models import Sample, Family

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


def test_get_sample_metadata(
    report_api_rnafusion: RnafusionReportAPI,
    rnafusion_sample_id: str,
    rnafusion_case_id: str,
    rnafusion_validated_metrics: Dict[str, str],
    mock_analysis_finish,
):
    """Test Rnafusion sample metadata extraction."""

    # GIVEN a Rnafusion case and associated sample
    case: Family = report_api_rnafusion.status_db.get_case_by_internal_id(
        internal_id=rnafusion_case_id
    )
    sample: Sample = report_api_rnafusion.status_db.get_sample_by_internal_id(
        internal_id=rnafusion_sample_id
    )

    # GIVEN an analysis metadata object
    latest_metadata: RnafusionAnalysis = report_api_rnafusion.analysis_api.get_latest_metadata(
        case_id=rnafusion_case_id
    )

    # WHEN getting the sample metadata
    sample_metadata: RnafusionSampleMetadataModel = report_api_rnafusion.get_sample_metadata(
        case=case, sample=sample, analysis_metadata=latest_metadata
    )

    # THEN the sample metadata should be correctly retrieved and match the expected validated metrics
    assert sample_metadata.dict() == rnafusion_validated_metrics
