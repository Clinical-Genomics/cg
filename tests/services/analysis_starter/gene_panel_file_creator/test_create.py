from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.apps.scout.scoutapi import ScoutAPI
from cg.constants.constants import Workflow
from cg.constants.gene_panel import GenePanelGenomeBuild, GenePanelMasterList
from cg.services.analysis_starter.configurator.file_creators import gene_panel
from cg.services.analysis_starter.configurator.file_creators.gene_panel import GenePanelFileCreator
from cg.store.models import Case
from cg.store.store import Store

RAREDISEASE_CASE_ID = "raredisease_case"
MIP_DNA_CASE_ID = "mip_dna_case"
NALLO_CASE_ID = "nallo_case"
TOMTE_CASE_ID = "tomte_case"


@pytest.fixture
def raredisease_case_id() -> str:
    return RAREDISEASE_CASE_ID


@pytest.fixture
def mip_dna_case_id() -> str:
    return MIP_DNA_CASE_ID


@pytest.fixture
def nallo_case_id() -> str:
    return NALLO_CASE_ID


@pytest.fixture
def tomte_case_id() -> str:
    return TOMTE_CASE_ID


@pytest.fixture
def mock_scout(nextflow_gene_panel_file_content: list[str]) -> ScoutAPI | MagicMock:
    mock_scout: ScoutAPI = create_autospec(ScoutAPI)
    mock_scout.export_panels = Mock(return_value=nextflow_gene_panel_file_content)
    return mock_scout


@pytest.fixture
def gene_panel_creator(
    raredisease_case_id: str,
    mock_scout: ScoutAPI,
    mip_dna_case_id: str,
    nallo_case_id: str,
    tomte_case_id: str,
) -> GenePanelFileCreator:
    case_dictionary: dict[str, Case] = {
        raredisease_case_id: create_autospec(
            Case, internal_id=raredisease_case_id, data_analysis=Workflow.RAREDISEASE
        ),
        mip_dna_case_id: create_autospec(
            Case, internal_id=mip_dna_case_id, data_analysis=Workflow.MIP_DNA
        ),
        nallo_case_id: create_autospec(
            Case, internal_id=nallo_case_id, data_analysis=Workflow.NALLO
        ),
        tomte_case_id: create_autospec(
            Case, internal_id=tomte_case_id, data_analysis=Workflow.TOMTE
        ),
    }

    mock_store: Store = create_autospec(Store)
    mock_store.get_case_by_internal_id = lambda internal_id: case_dictionary[internal_id]

    return GenePanelFileCreator(
        store=mock_store,
        scout_api=mock_scout,
    )


def test_gene_panel_file_content(
    gene_panel_creator: GenePanelFileCreator,
    raredisease_case_id: str,
    nextflow_case_path: Path,
    nextflow_gene_panel_file_content,
    mocker: MockerFixture,
):
    """Test that the gene panel file content is created correctly."""
    # GIVEN a gene panel file content creator, a case id and a case path

    # GIVEN that the case has a genome build
    mocker.patch.object(gene_panel, "get_genome_build", return_value=GenePanelGenomeBuild.hg19)

    # GIVEN a mock writer
    write_mock = mocker.patch.object(gene_panel, "write_txt")

    # WHEN creating a gene panel file
    gene_panel_creator.create(case_id=raredisease_case_id, case_path=nextflow_case_path)

    # THEN the gene panel file would have been written with the expected content
    write_mock.assert_called_once_with(
        content=nextflow_gene_panel_file_content,
        file_path=gene_panel_creator.get_file_path(nextflow_case_path),
    )


@pytest.mark.parametrize(
    "mock_value, expected_panels",
    [
        (True, GenePanelMasterList.get_panel_names()),
        (False, [GenePanelMasterList.PANELAPP_GREEN, GenePanelMasterList.OMIM_AUTO]),
    ],
    ids=[
        "customer is collaborator and panels in master list",
        "customer not collaborator or panels not in master list",
    ],
)
def test_get_aggregated_gene_panels(
    mock_value: bool,
    gene_panel_creator: GenePanelFileCreator,
    expected_panels: list[str],
    mocker: MockerFixture,
):
    """Test that gene panels are aggregated correctly."""
    # GIVEN a gene panel file creator

    # GIVEN a mock for the GenePanel Master List method
    mocker.patch.object(
        GenePanelMasterList,
        "is_customer_collaborator_and_panels_in_gene_panels_master_list",
        return_value=mock_value,
    )

    # WHEN getting the aggregated gene panels
    aggregated_panels: list[str] = gene_panel_creator._get_aggregated_panels(
        customer_id="cust000", default_panels=set()
    )

    # THEN the aggregated panels are what is expected
    assert set(aggregated_panels) == set(expected_panels)


@pytest.mark.parametrize(
    "panels, expected_panels",
    [
        ({"DSD", "CM"}, {"DSD", "DSD-S", "HYP", "POI", "CNM", "CM"}),
        ({"CM"}, {"CNM", "CM"}),
        ({"CM", "not_a_panel"}, {"CNM", "CM", "not_a_panel"}),
        ({"not_a_panel"}, {"not_a_panel"}),
        ({}, {}),
    ],
    ids=[
        "two panels in combo",
        "one panel in combo",
        "one panel in combo and one not in combo",
        "no panels in combo",
        "no panels",
    ],
)
def test_add_gene_panels_in_combo(
    gene_panel_creator: GenePanelFileCreator,
    panels: set[str],
    expected_panels: set[str],
):
    """Test that the combo gene panels are added correctly to a panel set."""
    # GIVEN a set of gene panels

    # WHEN adding the gene panels in combo
    updated_panels: set[str] = gene_panel_creator._add_gene_panels_in_combo(panels)

    # THEN the updated panels contain the expected panels
    assert updated_panels == expected_panels


@pytest.mark.parametrize(
    "case_id, expected_build",
    [
        (MIP_DNA_CASE_ID, GenePanelGenomeBuild.hg19),
        (RAREDISEASE_CASE_ID, GenePanelGenomeBuild.hg19),
        (NALLO_CASE_ID, GenePanelGenomeBuild.hg38),
        (TOMTE_CASE_ID, GenePanelGenomeBuild.hg38),
    ],
    ids=[
        "MIP-DNA case",
        "Raredisease case",
        "NALLO case",
        "TOMTE case",
    ],
)
def test_creating_file_for_workflows_using_correct_build(
    gene_panel_creator: GenePanelFileCreator,
    case_id: str,
    expected_build: GenePanelGenomeBuild,
    mock_scout: ScoutAPI | MagicMock,
    mocker: MockerFixture,
):
    # GIVEN a mock writer
    mocker.patch.object(gene_panel, "write_txt")

    # WHEN creating a gene panel file
    gene_panel_creator.create(case_id=case_id, case_path=Path("/"))

    cast(Mock, mock_scout.export_panels).assert_called_once_with(
        build=expected_build,
        panels=[
            GenePanelMasterList.OMIM_AUTO,
            GenePanelMasterList.PANELAPP_GREEN,
        ],
    )
