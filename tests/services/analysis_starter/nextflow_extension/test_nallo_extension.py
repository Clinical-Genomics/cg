from pathlib import Path
from unittest.mock import Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.constants.scout import ScoutExportFileName
from cg.models.cg_config import NalloConfig
from cg.services.analysis_starter.configurator.extensions import nallo
from cg.services.analysis_starter.configurator.extensions.nallo import NalloExtension
from cg.services.analysis_starter.configurator.file_creators.gene_panel import GenePanelFileCreator
from tests.typed_mock import TypedMock, create_typed_mock


@pytest.fixture
def nallo_config() -> NalloConfig:
    return create_autospec(
        NalloConfig,
        rank_model_snv="path/to/snv_rank_model.ini",
        rank_model_sv="path/to/sv_rank_model.ini",
    )


def test_configure(nallo_config: NalloConfig, mocker: MockerFixture):
    # GIVEN a gene panel file creator
    gene_panel_file_creator: TypedMock[GenePanelFileCreator] = create_typed_mock(
        GenePanelFileCreator
    )

    # GIVEN a Nallo extension
    nallo_extension = NalloExtension(
        gene_panel_file_creator=gene_panel_file_creator.as_type,
        nallo_config=nallo_config,
    )

    # GIVEN a case run directory
    case_run_directory = Path("case", "run", "directory")

    # WHEN configuring a case
    copy_mock = mocker.patch.object(nallo.shutil, "copy2")
    nallo_extension.configure(case_id="nallo_case", case_run_directory=case_run_directory)

    # THEN a gene panel file should have been created
    gene_panel_file_creator.as_mock.create.assert_called_once_with(
        case_id="nallo_case",
        file_path=case_run_directory / ScoutExportFileName.PANELS_TSV,
        double_hashtag_filtering=True,
    )

    # THEN the rank model files were copied to the case directory
    copy_mock.assert_any_call(
        Path("path/to/snv_rank_model.ini"), case_run_directory / "snv_rank_model.ini"
    )
    copy_mock.assert_any_call(
        Path("path/to/sv_rank_model.ini"), case_run_directory / "sv_rank_model.ini"
    )


def test_do_required_files_exist_true(nallo_config: NalloConfig, tmp_path: Path):
    # GIVEN that there is a gene panel tsv, a snv and sv rank model files
    gene_panels_file = tmp_path / ScoutExportFileName.PANELS_TSV
    gene_panels_file.touch()
    snv_rank_model_file = tmp_path / "snv_rank_model.ini"
    snv_rank_model_file.touch()
    sv_rank_model_file = tmp_path / "sv_rank_model.ini"
    sv_rank_model_file.touch()

    # GIVEN a Nallo extension
    nallo_extension = NalloExtension(gene_panel_file_creator=Mock(), nallo_config=nallo_config)

    # WHEN checking that the required files exist
    does_exist: bool = nallo_extension.do_required_files_exist(case_run_directory=tmp_path)

    # THEN the required file should exist
    assert does_exist


@pytest.mark.parametrize(
    "file_existence_array",
    [
        [False, True, True],
        [True, False, True],
        [True, True, False],
    ],
    ids=[
        "missing gene panel scenario",
        "missing snv rank model scenario",
        "missing sv rank model  scenario",
    ],
)
def test_do_required_files_exist_false(
    file_existence_array: list[bool], nallo_config: NalloConfig, tmp_path: Path
):
    # GIVEN a case run directory
    case_run_directory = tmp_path

    # GIVEN that one required file does not exist
    file_map: dict[Path, bool] = {
        Path(case_run_directory, ScoutExportFileName.PANELS): file_existence_array[0],
        Path(case_run_directory, "snv_rank_model.ini"): file_existence_array[1],
        Path(case_run_directory, "sv_rank_model.ini"): file_existence_array[2],
    }
    for file, should_exist in file_map.items():
        if should_exist:
            file.touch()

    # GIVEN a Nallo extension
    nallo_extension = NalloExtension(gene_panel_file_creator=Mock(), nallo_config=nallo_config)

    # WHEN calling do_required_files_exist
    does_exist: bool = nallo_extension.do_required_files_exist(case_run_directory)

    # THEN one of the files is marked as missing
    assert not does_exist
