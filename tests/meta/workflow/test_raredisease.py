from unittest.mock import create_autospec

from pytest_mock import MockerFixture

from cg.apps.coverage import ChanjoAPI
from cg.apps.scout.scoutapi import ScoutAPI
from cg.constants import SexOptions
from cg.constants.constants import GenomeBuild
from cg.meta.workflow import raredisease as raredisease_analysis_api
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.models.analysis import NextflowAnalysis
from cg.models.cg_config import CGConfig
from cg.models.deliverables.metric_deliverables import MetricsBase
from cg.store.models import Case, Sample


def test_parse_analysis(
    raredisease_context: CGConfig,
    raredisease_case_id: str,
    sample_id: str,
    raredisease_multiqc_json_metrics: dict,
    raredisease_mock_analysis_finish,
):
    """Test Raredisease output analysis files parsing."""

    # GIVEN a Raredisease analysis API and a list of QC metrics
    analysis_api: RarediseaseAnalysisAPI = raredisease_context.meta_apis["analysis_api"]
    qc_metrics: list[MetricsBase] = analysis_api.get_multiqc_json_metrics(
        case_id=raredisease_case_id
    )

    # WHEN extracting the analysis model
    analysis_model: NextflowAnalysis = analysis_api.parse_analysis(qc_metrics)

    # THEN the analysis model and its content should have been correctly extracted
    assert analysis_model.sample_metrics[sample_id].model_dump() == {
        "mapped_reads": 582035646,
        "percent_duplication": 0.0438,
        "predicted_sex_sex_check": SexOptions.FEMALE,
        "total_reads": 582127482,
    }


def test_get_sample_coverage(raredisease_context: CGConfig, mocker: MockerFixture):
    # GIVEN Raredisease case
    sample: Sample = create_autospec(Sample, internal_id="internal_id")
    case: Case = create_autospec(Case, internal_id="case_id", panels=["omim-auto"])

    # GIVEN a mocked chanjo API
    chanjo_api = create_autospec(ChanjoAPI)
    mock_chanjo_factory = mocker.patch.object(
        raredisease_analysis_api, "chanjo_api_for_genome_build", return_value=chanjo_api
    )

    # GIVEN Raredisease analysis API
    analysis_api: RarediseaseAnalysisAPI = RarediseaseAnalysisAPI(
        config=raredisease_context,
    )

    # GIVEN a response from ScoutAPI
    mocker.patch.object(ScoutAPI, "get_genes", return_value=[])

    # GIVEN some gene ids
    gene_ids: list[int] = analysis_api.get_gene_ids_from_scout(case.panels)

    # WHEN getting the chanjo coverage for the sample
    analysis_api.get_sample_coverage(
        case_id=case.internal_id, sample_id=sample.internal_id, gene_ids=gene_ids
    )

    # THEN chanjo was configured with the correct config
    mock_chanjo_factory.assert_called_once_with(raredisease_context, GenomeBuild.hg19)

    # THEN the sample coverage should have been called with the right information
    chanjo_api.sample_coverage.assert_called_once_with(sample_id="internal_id", panel_genes=[])
