from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from cg.constants.gene_panel import GenePanelGenomeBuild, GenePanelMasterList
from cg.services.analysis_starter.configurator.file_creators import gene_panel as gene_panel_creator
from cg.services.analysis_starter.configurator.file_creators.gene_panel import GenePanelFileCreator


def test_gene_panel_file_content(
    nextflow_gene_panel_creator: GenePanelFileCreator,
    nextflow_case_id: str,
    nextflow_case_path: Path,
    nextflow_gene_panel_file_content,
    mocker: MockerFixture,
):
    """Test that the gene panel file content is created correctly."""
    # GIVEN a gene panel file content creator, a case id and a case path

    # GIVEN that the case has a genome build
    mocker.patch.object(
        gene_panel_creator, "get_genome_build", return_value=GenePanelGenomeBuild.hg19
    )

    # GIVEN a mock writer
    write_mock = mocker.patch.object(gene_panel_creator, "write_txt")

    # WHEN creating a gene panel file
    nextflow_gene_panel_creator.create(case_id=nextflow_case_id, case_path=nextflow_case_path)

    # THEN the gene panel file would have been written with the expected content
    write_mock.assert_called_once_with(
        content=nextflow_gene_panel_file_content,
        file_path=nextflow_gene_panel_creator.get_file_path(nextflow_case_path),
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
def test_get_agregated_gene_panels(
    mock_value: bool,
    nextflow_gene_panel_creator: GenePanelFileCreator,
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
    aggregated_panels: list[str] = nextflow_gene_panel_creator._get_aggregated_panels(
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
    nextflow_gene_panel_creator: GenePanelFileCreator,
    panels: set[str],
    expected_panels: set[str],
):
    """Test that the combo gene panels are added correctly to a panel set."""
    # GIVEN a set of gene panels

    # WHEN adding the gene panels in combo
    updated_panels: set[str] = nextflow_gene_panel_creator._add_gene_panels_in_combo(panels)

    # THEN the updated panels contain the expected panels
    assert updated_panels == expected_panels
