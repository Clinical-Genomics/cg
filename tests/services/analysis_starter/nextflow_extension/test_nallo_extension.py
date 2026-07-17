from pathlib import Path
from unittest.mock import Mock, create_autospec

from pytest_mock import MockerFixture

from cg.constants.scout import ScoutExportFileName
from cg.models.cg_config import NalloConfig
from cg.services.analysis_starter.configurator.extensions import nallo
from cg.services.analysis_starter.configurator.extensions.nallo import NalloExtension
from cg.services.analysis_starter.configurator.file_creators.gene_panel import GenePanelFileCreator
from tests.typed_mock import TypedMock, create_typed_mock

# TODO: create fixture for nallo config


def test_configure(mocker: MockerFixture):
    # GIVEN a gene panel file creator
    gene_panel_file_creator: TypedMock[GenePanelFileCreator] = create_typed_mock(
        GenePanelFileCreator
    )

    # GIVEN a Nallo extension
    nallo_extension = NalloExtension(
        gene_panel_file_creator=gene_panel_file_creator.as_type,
        nallo_config=create_autospec(
            NalloConfig,
            rank_model_snv="path/to/snv_rank_model.ini",
            rank_model_sv="path/to/sv_rank_model.ini",
        ),
    )

    # GIVEN a case run directory
    case_run_directory = Path("case", "run", "directory")

    # WHEN configuring a case
    link_mock = mocker.patch.object(nallo.os, "link")
    nallo_extension.configure(case_id="nallo_case", case_run_directory=case_run_directory)

    # THEN a gene panel file should have been created
    gene_panel_file_creator.as_mock.create.assert_called_once_with(
        case_id="nallo_case",
        file_path=case_run_directory / ScoutExportFileName.PANELS_TSV,
        double_hashtag_filtering=True,
    )

    # THEN the rank model files were copied to the case directory
    link_mock.assert_any_call(
        Path("path/to/snv_rank_model.ini"), case_run_directory / "snv_rank_model.ini"
    )
    link_mock.assert_any_call(
        Path("path/to/sv_rank_model.ini"), case_run_directory / "sv_rank_model.ini"
    )


def test_do_required_files_exist_true(tmp_path: Path):
    # GIVEN that there is a gene panel tsv, a snv and sv rank model files
    gene_panels_file = tmp_path / ScoutExportFileName.PANELS_TSV
    gene_panels_file.touch()
    snv_rank_model_file = tmp_path / "snv_rank_model.ini"
    snv_rank_model_file.touch()
    sv_rank_model_file = tmp_path / "sv_rank_model.ini"
    sv_rank_model_file.touch()

    # GIVEN a Nallo extension
    nallo_extension = NalloExtension(
        gene_panel_file_creator=Mock(),
        nallo_config=create_autospec(
            NalloConfig,
            rank_model_snv="path/to/snv_rank_model.ini",
            rank_model_sv="path/to/sv_rank_model.ini",
        ),
    )

    # WHEN checking that the required files exist
    does_exist: bool = nallo_extension.do_required_files_exist(case_run_directory=tmp_path)

    # THEN the required file should exist
    assert does_exist


def test_do_required_files_exist_false(tmp_path: Path):
    # GIVEN that there is no gene panel tsv file
    scout_file = tmp_path / ScoutExportFileName.PANELS_TSV
    assert not scout_file.exists()

    # GIVEN a Nallo extension
    nallo_extension = NalloExtension(
        gene_panel_file_creator=Mock(),
        nallo_config=create_autospec(
            NalloConfig,
            rank_model_snv="path/to/snv_rank_model.ini",
            rank_model_sv="path/to/sv_rank_model.ini",
        ),
    )

    # WHEN checking that the required files exist
    does_exist: bool = nallo_extension.do_required_files_exist(case_run_directory=tmp_path)

    # THEN the required file should not exist
    assert not does_exist
