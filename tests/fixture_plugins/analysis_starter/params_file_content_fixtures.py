from pathlib import Path

import pytest


@pytest.fixture
def expected_raredisease_params_file_content(
    raredisease_case_path2: Path,
    raredisease_sample_sheet_path2: Path,
    raredisease_gene_panel_path2: Path,
    raredisease_managed_variants_path: Path,
) -> dict:
    return {
        "someparam": "something",
        "input": raredisease_sample_sheet_path2,
        "outdir": raredisease_case_path2,
        "target_bed_file": "bed_version_file.bed",
        "analysis_type": "wgs",
        "save_mapped_as_cram": True,
        "vcfanno_extra_resources": raredisease_managed_variants_path.as_posix(),
        "vep_filters_scout_fmt": raredisease_gene_panel_path2.as_posix(),
        "sample_id_map": Path(
            raredisease_case_path2, "raredisease_case_id_customer_internal_mapping.csv"
        ),
    }
