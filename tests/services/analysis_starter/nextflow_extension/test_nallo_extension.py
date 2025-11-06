from pathlib import Path
from unittest.mock import Mock

from cg.constants.scout import ScoutExportFileName
from cg.services.analysis_starter.configurator.extensions.nallo import NalloExtension
from cg.services.analysis_starter.configurator.file_creators.gene_panel import GenePanelFileCreator
from tests.typed_mock import TypedMock, create_typed_mock


def test_configure():
    # GIVEN a gene panel file creator
    gene_panel_file_creator: TypedMock[GenePanelFileCreator] = create_typed_mock(
        GenePanelFileCreator
    )

    # GIVEN a Nallo extension
    nallo_extension = NalloExtension(gene_panel_file_creator=gene_panel_file_creator.as_type)

    # GIVEN a case run directory
    case_run_directory = Path("case", "run", "directory")

    # WHEN configuring a case
    nallo_extension.configure(case_id="nallo_case", case_run_directory=case_run_directory)

    # THEN a gene panel file should have been created
    gene_panel_file_creator.as_mock.create.assert_called_once_with(
        case_id="nallo_case",
        file_path=case_run_directory / ScoutExportFileName.PANELS_TSV,
        double_hashtag_filtering=True,
    )


def test_do_required_files_exist_true(tmp_path: Path):
    # GIVEN that there is a gene panel tsv file
    scout_file = tmp_path / ScoutExportFileName.PANELS_TSV
    scout_file.touch()

    # GIVEN a Nallo extension
    nallo_extension = NalloExtension(gene_panel_file_creator=Mock())

    # WHEN checking that the required files exist
    does_exist: bool = nallo_extension.do_required_files_exist(case_run_directory=tmp_path)

    # THEN the required file should exist
    assert does_exist


def test_do_required_files_exist_false(tmp_path: Path):
    # GIVEN that there is no gene panel tsv file
    scout_file = tmp_path / ScoutExportFileName.PANELS_TSV
    assert not scout_file.exists()

    # GIVEN a Nallo extension
    nallo_extension = NalloExtension(gene_panel_file_creator=Mock())

    # WHEN checking that the required files exist
    does_exist: bool = nallo_extension.do_required_files_exist(case_run_directory=tmp_path)

    # THEN the required file should not exist
    assert not does_exist
