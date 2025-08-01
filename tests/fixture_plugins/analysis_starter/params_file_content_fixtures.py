from pathlib import Path

import pytest


@pytest.fixture
def nextflow_workflow_params_content() -> dict:
    """Return a dictionary with some parameters for the Nextflow params file."""
    return {"someparam": "something"}


@pytest.fixture
def expected_raredisease_params_file_content(
    nextflow_case_path: Path,
    nextflow_sample_sheet_path: Path,
    raredisease_gene_panel_path2: Path,
    raredisease_managed_variants_path: Path,
    nextflow_case_id: str,
    nextflow_workflow_params_content: dict,
) -> dict:
    case_parameters = {
        "input": nextflow_sample_sheet_path,
        "outdir": nextflow_case_path,
        "target_bed_file": "bed_version_file.bed",
        "analysis_type": "wgs",
        "save_mapped_as_cram": True,
        "vcfanno_extra_resources": raredisease_managed_variants_path.as_posix(),
        "vep_filters_scout_fmt": raredisease_gene_panel_path2.as_posix(),
        "sample_id_map": Path(
            nextflow_case_path, f"{nextflow_case_id}_customer_internal_mapping.csv"
        ),
    }
    return case_parameters | nextflow_workflow_params_content


@pytest.fixture
def expected_rnafusion_params_file_content(
    nextflow_case_path: Path,
    nextflow_sample_sheet_path: Path,
    nextflow_workflow_params_content: dict,
) -> dict:
    """Return a dictionary with parameters for the RNAFUSION params file."""
    case_parameters = {
        "input": nextflow_sample_sheet_path,
        "outdir": nextflow_case_path,
    }
    return case_parameters | nextflow_workflow_params_content


@pytest.fixture
def expected_taxprofiler_params_file_content(
    nextflow_case_path: Path,
    nextflow_sample_sheet_path: Path,
    nextflow_workflow_params_content: dict,
) -> dict:
    """Return a dictionary with parameters for the Taxprofiler params file."""
    case_parameters = {
        "input": nextflow_sample_sheet_path,
        "outdir": nextflow_case_path,
    }
    return case_parameters | nextflow_workflow_params_content


@pytest.fixture
def expected_raredisease_workflow_params_content() -> dict:
    """Return a dictionary with some parameters for the raredisease params file."""
    return {
        "input": "/path/to/samplesheet/case_samplesheet.csv",
        "outdir": "/path/to/case",
        "genomes_base": "/path/to/pipeline/version",
        "all": False,
        "arriba": True,
        "cram": "arriba,starfusion",
        "fastp_trim": True,
        "fusioncatcher": True,
        "starfusion": True,
        "trim_tail": 50,
    }
