from unittest.mock import create_autospec

from pytest_mock import MockerFixture

from cg.apps.coverage import ChanjoAPI
from cg.apps.scout.scoutapi import ScoutAPI
from cg.constants import SexOptions
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.models.analysis import NextflowAnalysis
from cg.models.cg_config import CGConfig
from cg.models.deliverables.metric_deliverables import MetricsBase
from cg.store.models import Case, Sample
from tests.typed_mock import TypedMock, create_typed_mock


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
    sample: Sample = create_autospec(Sample)
    case: Case = create_autospec(Case, panels=["omim-auto"])

    # GIVEN Raredisease analysis API
    analysis_api: RarediseaseAnalysisAPI = RarediseaseAnalysisAPI(
        config=raredisease_context,
    )
    chanjo_api: TypedMock[ChanjoAPI] = create_typed_mock(ChanjoAPI)
    analysis_api.chanjo_api = chanjo_api.as_type

    # GIVEN
    mocker.patch.object(ScoutAPI, "get_genes", return_value=[])

    # GIVEN some gene ids
    gene_ids: list[int] = analysis_api.get_gene_ids_from_scout(case.panels)

    # WHEN
    analysis_api.get_sample_coverage(
        case_id=case.internal_id, sample_id=sample.internal_id, gene_ids=gene_ids
    )

    # THEN
    chanjo_api.as_mock.sample_coverage.assert_called_once_with()
