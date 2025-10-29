from pathlib import Path

import pytest

from cg.constants import Workflow
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file import (
    nallo,
    rnafusion,
    taxprofiler,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.nallo import (
    NalloParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.rnafusion import (
    RNAFusionParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.taxprofiler import (
    TaxprofilerParamsFileCreator,
)


@pytest.fixture
def case_id() -> str:
    return "case_id"


@pytest.fixture
def nextflow_sample_sheet_path() -> Path:
    """Path to sample sheet."""
    return Path("samplesheet", "path")


@pytest.fixture
def case_run_dir(case_id: str) -> Path:
    return Path("/root/", case_id)


@pytest.fixture
def nextflow_workflow_params_content() -> dict:
    """Return a dictionary with some parameters for the Nextflow params file."""
    return {"workflow_param1": "some_value"}


@pytest.fixture
def expected_nallo_params_file_content(
    case_run_dir: Path, nextflow_sample_sheet_path: Path, nextflow_workflow_params_content: dict
) -> dict:
    """Return a dictionary with parameters for the Nallo params file."""
    case_parameters = {
        "input": nextflow_sample_sheet_path,
        "outdir": case_run_dir,
        "filter_variants_hgnc_ids": "/root/case_id/gene_panels.tsv",
    }
    return case_parameters | nextflow_workflow_params_content


@pytest.fixture
def expected_rnafusion_params_file_content(
    case_run_dir: Path,
    nextflow_sample_sheet_path: Path,
    nextflow_workflow_params_content: dict,
) -> dict:
    """Return a dictionary with parameters for the RNAFUSION params file."""
    case_parameters = {
        "input": nextflow_sample_sheet_path,
        "outdir": case_run_dir,
    }
    return case_parameters | nextflow_workflow_params_content


@pytest.fixture
def expected_taxprofiler_params_file_content(
    case_run_dir: Path,
    nextflow_sample_sheet_path: Path,
    nextflow_workflow_params_content: dict,
) -> dict:
    """Return a dictionary with parameters for the Taxprofiler params file."""
    case_parameters = {
        "input": nextflow_sample_sheet_path,
        "outdir": case_run_dir,
    }
    return case_parameters | nextflow_workflow_params_content


@pytest.fixture
def params_file_scenario(
    expected_nallo_params_file_content: dict,
    expected_rnafusion_params_file_content: dict,
    expected_taxprofiler_params_file_content: dict,
) -> dict:
    return {
        Workflow.NALLO: (
            NalloParamsFileCreator,
            expected_nallo_params_file_content,
            nallo,
        ),
        Workflow.RNAFUSION: (
            RNAFusionParamsFileCreator,
            expected_rnafusion_params_file_content,
            rnafusion,
        ),
        Workflow.TAXPROFILER: (
            TaxprofilerParamsFileCreator,
            expected_taxprofiler_params_file_content,
            taxprofiler,
        ),
    }
