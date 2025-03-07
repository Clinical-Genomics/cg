import pytest


@pytest.fixture
def raredisease_gene_panel_file_content() -> str:
    return "content"


@pytest.fixture
def raredisease_managed_variants_file_content() -> list[str]:
    return ["variant_from_scout1", "variant_from_scout2"]
