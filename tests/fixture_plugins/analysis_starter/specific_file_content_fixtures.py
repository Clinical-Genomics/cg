import pytest


@pytest.fixture
def nextflow_gene_panel_file_content() -> list[str]:
    return [
        "##genome_build=37",
        "##gene_panel=OMIM-AUTO,version=32.0,updated_at=2024-11-18,display_name=OMIM-AUTO",
    ]


@pytest.fixture
def raredisease_managed_variants_file_content() -> list[str]:
    return ["variant_from_scout1", "variant_from_scout2"]
