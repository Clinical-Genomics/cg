"""Module for Rnafusion analysis API tests."""

from unittest.mock import Mock, create_autospec

import pytest

from cg.constants.nf_analysis import (
    RNAFUSION_METRIC_CONDITIONS,
    RNAFUSION_METRIC_CONDITIONS_DEPLETION,
)
from cg.meta.workflow.rnafusion_analysis_api import RnafusionAnalysisAPI
from cg.models.analysis import NextflowAnalysis
from cg.models.cg_config import (
    CGConfig,
    IlluminaConfig,
    RnafusionConfig,
    RunInstruments,
    SlurmConfig,
)
from cg.models.deliverables.metric_deliverables import MetricsBase
from cg.store.models import Sample
from cg.store.store import Store


@pytest.fixture
def config() -> CGConfig:
    return create_autospec(
        CGConfig,
        tower_binary_path="/path/to/tower",
        rnafusion=RnafusionConfig(
            binary_path="/path/to/nextflow",
            conda_env="S_rnafusion",
            platform="slurm",
            params="/path/to/params.yaml",
            config="/path/to/nextflow.config",
            resources="/path/to/resources.yaml",
            launch_directory="/path/to/launch",
            profile="singularity",
            repository="https://repo",
            revision="3.0.1",
            root="/path/to/root",
            slurm=SlurmConfig(account="development", mail_user="test@test.com"),
            tower_workflow="nf-core/rnafusion",
            workflow_bin_path="/path/to/workflow/bin",
        ),
        run_instruments=create_autospec(
            RunInstruments,
            illumina=create_autospec(IlluminaConfig, demultiplexed_runs_dir="/some/dir"),
        ),
    )


def test_parse_analysis(
    rnafusion_context: CGConfig,
    rnafusion_case_id: str,
    sample_id: str,
    rnafusion_metrics: dict,
    rnafusion_mock_analysis_finish,
):
    """Test Rnafusion output analysis files parsing."""

    # GIVEN a Rnafusion analysis API and a list of QC metrics
    analysis_api: RnafusionAnalysisAPI = rnafusion_context.meta_apis["analysis_api"]
    qc_metrics: list[MetricsBase] = analysis_api.get_multiqc_json_metrics(case_id=rnafusion_case_id)

    # WHEN extracting the analysis model
    analysis_model: NextflowAnalysis = analysis_api.parse_analysis(qc_metrics)

    # THEN the analysis model and its content should have been correctly extracted
    assert analysis_model.sample_metrics[sample_id].model_dump() == rnafusion_metrics


def test_get_latest_metadata(
    rnafusion_context: CGConfig, rnafusion_case_id: str, rnafusion_mock_analysis_finish
):
    """Test retrieval of Rnafusion latest metadata."""

    # GIVEN a Rnafusion analysis API and a list of QC metrics
    analysis_api: RnafusionAnalysisAPI = rnafusion_context.meta_apis["analysis_api"]

    # WHEN collecting the latest metadata
    latest_metadata: NextflowAnalysis = analysis_api.get_latest_metadata(case_id=rnafusion_case_id)

    # THEN the latest metadata should have been parsed
    assert latest_metadata
    assert latest_metadata.sample_metrics


def test_get_qc_conditions_for_workflow(config):
    # GIVEN a cg config

    # GIVEN a RNA Fusion API
    rna_fusion_analysis_api = RnafusionAnalysisAPI(config=config)

    # WHEN calling
    metrics = rna_fusion_analysis_api.get_qc_conditions_for_workflow("sample_id")

    # THEN we get the default metric conditions for RNAFusion
    assert metrics == RNAFUSION_METRIC_CONDITIONS


def test_get_qc_conditions_for_workflow_with_special_apptag(config):
    # GIVEN a cg config

    # GIVEN a status db connection
    status_db = create_autospec(Store)
    config.status_db = status_db

    # GIVEN a sample with the apptag RNAWDPR100
    sample: Sample = create_autospec(
        Sample,
        application_tag="RNAWDPR100",
        internal_id="sample1",
    )

    status_db.get_sample_by_internal_id_strict = Mock(return_value=sample)

    # GIVEN a RNA Fusion API
    rna_fusion_analysis_api = RnafusionAnalysisAPI(config=config)

    # WHEN calling
    metrics = rna_fusion_analysis_api.get_qc_conditions_for_workflow(sample.internal_id)

    # THEN the correct conditions are given for the apptag
    assert metrics == RNAFUSION_METRIC_CONDITIONS_DEPLETION
