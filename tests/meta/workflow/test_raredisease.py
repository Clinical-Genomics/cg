from pathlib import Path
from unittest.mock import Mock, create_autospec

from pytest_mock import MockerFixture

from cg.apps.coverage import ChanjoAPI
from cg.apps.scout.scoutapi import ScoutAPI
from cg.clients.chanjo2.models import CoverageMetricsChanjo1
from cg.constants import SexOptions, Workflow
from cg.constants.constants import GenomeBuild, GenomeVersion
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
        config=raredisease_context, genome_build=GenomeBuild.hg38
    )

    # THEN the sample coverage should have been called with the right information
    get_sample_coverage_spy.assert_called_once_with(
        chanjo_api=chanjo_api, gene_ids=gene_ids, sample_id="internal_id"
    )


def test_get_genome_build():
    # GIVEN the RarediseaseAnalysisAPI
    cg_config: CGConfig = create_autospec(
        CGConfig,
        raredisease=create_autospec(
            RarediseaseConfig,
            conda_binary="conda/bin",
            conda_env="conda/env",
            config="here/is/my/config",
            params="here/is/my/params/file",
            platform="platform",
            profile="profile",
            resources="resources",
            revision="1.0.0",
            root="/I/am/Root",
            slurm=create_autospec(SlurmConfig, account="account", mail_user="user"),
            tower_workflow=Workflow.RAREDISEASE,
            workflow_bin_path=Path("I", "am", "workflow", "bin", "path"),
        ),
        chanjo_38=ChanjoConfig(binary_path="binary/path", config_path="config/path"),
        data_flow=Mock(),
        run_instruments=create_autospec(
            RunInstruments,
            illumina=create_autospec(IlluminaConfig, demultiplexed_runs_dir="some_dir"),
        ),
        tower_binary_path="tower/path",
    )

    analysis_api = RarediseaseAnalysisAPI(config=cg_config)

    # WHEN getting the genome build
    # THEN it is hg38
    assert analysis_api.get_genome_build(case_id="ChevyCase") == GenomeVersion.HG38
