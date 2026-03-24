from unittest.mock import Mock, create_autospec

from pytest_mock import MockerFixture

from cg.apps.coverage import ChanjoAPI
from cg.apps.scout.scoutapi import ScoutAPI
from cg.clients.chanjo2.models import CoverageMetricsChanjo1
from cg.constants import SexOptions
from cg.constants.constants import GenomeBuild
from cg.meta.workflow import raredisease as raredisease_analysis_api
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.models.analysis import NextflowAnalysis
from cg.models.cg_config import (
    CGConfig,
    ChanjoConfig,
    IlluminaConfig,
    RarediseaseConfig,
    RunInstruments,
    SlurmConfig,
)
from cg.models.deliverables.metric_deliverables import MetricsBase
from cg.store.models import Sample
from cg.store.store import Store


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
        "percent_duplication": 0.0438,
        "picard_pct_pf_reads_aligned": 0.999729,
        "predicted_sex_sex_check": SexOptions.FEMALE,
    }


def test_get_sample_coverage(raredisease_context: CGConfig, mocker: MockerFixture):
    # GIVEN Raredisease case
    sample: Sample = create_autospec(Sample, internal_id="internal_id")

    # GIVEN a mocked chanjo API
    chanjo_api: ChanjoAPI = create_autospec(ChanjoAPI)
    chanjo_api.sample_coverage = Mock(
        return_value={"mean_coverage": 28.9, "mean_completeness": 88.5}
    )
    mock_chanjo_factory = mocker.patch.object(
        raredisease_analysis_api, "chanjo_api_for_genome_build", return_value=chanjo_api
    )

    get_sample_coverage_spy = mocker.spy(raredisease_analysis_api, "chanjo1_get_sample_coverage")

    # GIVEN Raredisease analysis API
    analysis_api: RarediseaseAnalysisAPI = RarediseaseAnalysisAPI(
        config=raredisease_context,
    )

    # GIVEN a response from ScoutAPI
    mocker.patch.object(ScoutAPI, "get_genes", return_value=[])

    # GIVEN some gene ids
    gene_ids: list[int] = [1, 2, 3]

    # WHEN getting the chanjo coverage for the sample
    sample_coverage: CoverageMetricsChanjo1 | None = analysis_api.get_sample_coverage(
        case_id="case_id", sample_id=sample.internal_id, gene_ids=gene_ids
    )

    assert sample_coverage == CoverageMetricsChanjo1(
        coverage_completeness_percent=88.5, mean_coverage=28.9
    )

    # THEN chanjo was configured with the correct config
    mock_chanjo_factory.assert_called_once_with(
        config=raredisease_context, genome_build=GenomeBuild.hg19
    )

    # THEN the sample coverage should have been called with the right information
    get_sample_coverage_spy.assert_called_once_with(
        chanjo_api=chanjo_api, gene_ids=gene_ids, sample_id="internal_id"
    )


def test_get_qc_conditions_for_workflow():
    sample = create_autospec(Sample, internal_id="sample_id", sex=SexOptions.FEMALE)
    status_db = create_autospec(Store)
    status_db.get_sample_by_internal_id = Mock(return_value=sample)
    # GIVEN Raredisease analysis API
    analysis_api: RarediseaseAnalysisAPI = RarediseaseAnalysisAPI(
        config=create_autospec(
            CGConfig,
            run_instruments=create_autospec(
                RunInstruments,
                illumina=create_autospec(IlluminaConfig, demultiplexed_runs_dir="some/path"),
            ),
            chanjo=create_autospec(ChanjoConfig, config_path="some/path", binary_path="some/path"),
            raredisease=create_autospec(
                RarediseaseConfig,
                conda_binary="conda/bin",
                conda_env="conda_env",
                config="config.json",
                params="params.yaml",
                platform="platform",
                profile="profile",
                resources="a tonne",
                revision="0.0.0",
                root="root",
                slurm=create_autospec(SlurmConfig, account="account", mail_user="mail_user"),
                tower_workflow="raredisease",
                workflow_bin_path="workflow/bin",
            ),
            tower_binary_path="tower/bin",
        ),
    )
    analysis_api.status_db = status_db
    qc_conditions: dict = analysis_api.get_qc_conditions_for_workflow("sample_id")
    assert qc_conditions == {
        "PERCENT_DUPLICATION": {"norm": "lt", "threshold": 0.20},
        "PCT_PF_UQ_READS_ALIGNED": {"norm": "gt", "threshold": 0.95},
        "PCT_TARGET_BASES_10X": {"norm": "gt", "threshold": 0.95},
        "AT_DROPOUT": {"norm": "lt", "threshold": 10},
        "GC_DROPOUT": {"norm": "lt", "threshold": 10},
        "predicted_sex_sex_check": {"norm": "eq", "threshold": SexOptions.FEMALE},
        "gender": {"norm": "eq", "threshold": SexOptions.FEMALE},
    }
