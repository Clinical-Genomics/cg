from pathlib import Path
from unittest.mock import create_autospec

from pytest_mock import MockerFixture

from cg.constants.scout import ScoutExportFileName
from cg.services.analysis_starter.configurator.extensions import tomte_extension
from cg.services.analysis_starter.configurator.extensions.tomte_extension import TomteExtension
from cg.services.analysis_starter.configurator.file_creators.gene_panel import GenePanelFileCreator


def test_tomte_extension_configure():
    # GIVEN a Tomte pipeline extension
    gene_panel_file_creator = create_autospec(GenePanelFileCreator)
    extension = TomteExtension(gene_panel_file_creator=gene_panel_file_creator)
    case_run_directory = Path("best", "case")

    # WHEN configuring a case
    extension.configure(case_id="case_id", case_run_directory=case_run_directory)

    # THEN the gene panel file creator should have been called
    gene_panel_file_creator.create.assert_called_once_with(
        case_id="case_id",
        file_path=case_run_directory / ScoutExportFileName.PANELS,
        double_hashtag_filtering=False,
    )


def test_tomte_extension_do_required_files_exist_exists(mocker: MockerFixture):
    # GIVEN a Tomte pipeline extension
    gene_panel_file_creator = create_autospec(GenePanelFileCreator)
    extension = TomteExtension(gene_panel_file_creator=gene_panel_file_creator)
    case_run_directory = Path("best", "case")

    # GIVEN that the required files do exist
    mocker.patch.object(tomte_extension, "isfile", return_value=True)

    # WHEN calling do_required_files_exist
    do_required_files_exist = extension.do_required_files_exist(
        case_run_directory=case_run_directory
    )

    # THEN the file should exist
    assert do_required_files_exist


def test_tomte_extension_do_required_files_exist_missing_file(mocker: MockerFixture):
    # GIVEN a Tomte pipeline extension
    gene_panel_file_creator = create_autospec(GenePanelFileCreator)
    extension = TomteExtension(gene_panel_file_creator=gene_panel_file_creator)
    case_run_directory = Path("best", "case")

    # GIVEN that the required files do not exist
    mocker.patch.object(tomte_extension, "isfile", return_value=False)

    # WHEN calling do_required_files_exist
    do_required_files_exist = extension.do_required_files_exist(
        case_run_directory=case_run_directory
    )

    # THEN the file should not exist
    assert not do_required_files_exist
