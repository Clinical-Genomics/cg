from pathlib import Path

import pytest


@pytest.fixture
def expected_raredisease_params_file_content(
    raredisease_case_path: Path,
    raredisease_sample_sheet_path: Path,
    raredisease_gene_panel_path: Path,
    raredisease_managed_variants_path: Path,
) -> dict:
    return {
        "input": raredisease_sample_sheet_path,
        "outdir": raredisease_case_path,
        "target_bed_file": "twistexomecomprehensive_10.2_hg19_design.bed",
        "analysis_type": "wgs",
        "save_mapped_as_cram": True,
        "skip_germlinecnvcaller": True,
        "vcfanno_extra_resources": raredisease_managed_variants_path.as_posix(),
        "vep_filters_scout_fmt": raredisease_gene_panel_path.as_posix(),
        "someparam": "something",
    }
