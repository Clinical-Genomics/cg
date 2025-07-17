from pathlib import Path
from unittest import mock

import pytest
from pytest_mock import MockerFixture

from cg.apps.scout.scoutapi import ScoutAPI
from cg.constants import Workflow
from cg.constants.gene_panel import GenePanelGenomeBuild, GenePanelMasterList
from cg.services.analysis_starter.configurator.file_creators.nextflow import config_file
from cg.services.analysis_starter.configurator.file_creators.nextflow import (
    gene_panel as gene_panel_creator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.config_file import (
    NextflowConfigFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.gene_panel import (
    GenePanelFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.managed_variants import (
    ManagedVariantsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet import (
    creator as samplesheet_creator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.creator import (
    NextflowSampleSheetCreator,
)


@pytest.mark.parametrize("workflow", [Workflow.RAREDISEASE, Workflow.RNAFUSION])
def test_nextflow_params_file_creator(
    workflow: Workflow,
    params_file_scenario: dict,
    nextflow_case_path: Path,
    nextflow_sample_sheet_path: Path,
    nextflow_case_id: str,
):
    """Test that the Raredisease params file creator is initialized correctly."""
    # GIVEN a params file creator, an expected output and a mocked file writer
    file_creator, expected_content, write_yaml_mock = params_file_scenario[workflow]

    # WHEN creating the params file
    file_creator.create(
        case_id=nextflow_case_id,
        case_path=nextflow_case_path,
        sample_sheet_path=nextflow_sample_sheet_path,
    )

    # THEN the file should have been written with the expected content
    file_path: Path = file_creator.get_file_path(
        case_id=nextflow_case_id, case_path=nextflow_case_path
    )
    write_yaml_mock.assert_called_once_with(file_path=file_path, content=expected_content)


def test_nextflow_config_file_content(
    nextflow_config_file_creator: NextflowConfigFileCreator,
    nextflow_case_id: str,
    nextflow_case_path: Path,
    expected_nextflow_config_content: str,
    mocker: MockerFixture,
):
    """Test that a Nextflow config file content is created correctly for all pipelines."""
    # GIVEN a Nextflow config content creator and a case id

    # GIVEN a writer mock
    write_mock: mocker.MagicMock = mocker.patch.object(config_file, "write_txt", return_value=None)

    # WHEN creating a Nextflow config file
    nextflow_config_file_creator.create(case_id=nextflow_case_id, case_path=nextflow_case_path)

    # THEN the content of the file is the expected
    file_path = Path(nextflow_case_path, f"{nextflow_case_id}_nextflow_config.json")
    write_mock.assert_called_once_with(
        file_path=file_path, content=expected_nextflow_config_content
    )


@pytest.mark.parametrize(
    "workflow", [Workflow.RAREDISEASE, Workflow.RNAFUSION, Workflow.TAXPROFILER]
)
def test_nextflow_sample_sheet_creators(
    workflow: Workflow,
    sample_sheet_scenario: dict,
    nextflow_case_id: str,
    nextflow_case_path: Path,
    mocker: MockerFixture,
):
    # GIVEN a sample sheet creator, an expected output and a mocked file writer
    sample_sheet_creator, expected_content = sample_sheet_scenario[workflow]
    write_mock: mocker.MagicMock = mocker.patch.object(samplesheet_creator, "write_csv")

    # GIVEN a pair of Fastq files that have a header
    mocker.patch.object(
        samplesheet_creator,
        "read_gzip_first_line",
        side_effect=[
            "@ST-E00201:173:HCXXXXX:1:2106:22516:34834/1",
            "@ST-E00201:173:HCXXXXX:1:2106:22516:34834/2",
        ],
    )
    # GIVEN that the files exist
    mocker.patch.object(Path, "is_file", return_value=True)

    # WHEN creating the sample sheet
    sample_sheet_creator.create(case_id=nextflow_case_id, case_path=nextflow_case_path)

    # THEN the sample sheet should have been written to the correct path with the correct content
    write_mock.assert_called_with(
        content=expected_content,
        file_path=sample_sheet_creator.get_file_path(
            case_path=nextflow_case_path, case_id=nextflow_case_id
        ),
    )


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
    write_mock: mocker.MagicMock = mocker.patch.object(gene_panel_creator, "write_txt")

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


def test_managed_variants_content(
    raredisease_managed_variants_creator: ManagedVariantsFileCreator,
    raredisease_case_id: str,
    raredisease_managed_variants_file_content: list[str],
):
    """Test that the managed variants file content is created correctly."""
    # GIVEN a Raredisease managed variants file content creator and a case path

    # GIVEN a mock of Scout variants

    # WHEN creating a managed variants file
    expected_content_fixture: list[str] = raredisease_managed_variants_file_content
    with mock.patch.object(
        ScoutAPI, "export_managed_variants", return_value=expected_content_fixture
    ):
        content: list[str] = raredisease_managed_variants_creator._get_content(raredisease_case_id)

    # THEN the content of the file is the expected
    assert content == expected_content_fixture


def test_parse_fastq_header_raises_error():
    # GIVEN a faulty FASTQ Header

    with pytest.raises(TypeError):
        # WHEN parsing the header
        # THEN the correct error is raised
        NextflowSampleSheetCreator._parse_fastq_header(line="Not a Fastq header")
