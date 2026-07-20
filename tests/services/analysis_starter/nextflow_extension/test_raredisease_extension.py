from pathlib import Path
from unittest.mock import Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.constants.scout import ScoutExportFileName
from cg.models.cg_config import RarediseaseConfig
from cg.services.analysis_starter.configurator.extensions import raredisease
from cg.services.analysis_starter.configurator.extensions.raredisease import RarediseaseExtension
from cg.services.analysis_starter.configurator.file_creators.gene_panel import GenePanelFileCreator
from cg.services.analysis_starter.configurator.file_creators.managed_variants import (
    ManagedVariantsFileCreator,
)


@pytest.fixture
def raredisease_config() -> RarediseaseConfig:
    return create_autospec(
        RarediseaseConfig,
        rank_model_snv="path/to/snv_rank_model.ini",
        rank_model_sv="path/to/sv_rank_model.ini",
    )


def test_configure_success(raredisease_config: RarediseaseConfig, mocker: MockerFixture):
    # GIVEN a raredisease pipeline extension
    raredisease_extension = RarediseaseExtension(
        gene_panel_file_creator=create_autospec(GenePanelFileCreator),
        managed_variants_file_creator=create_autospec(ManagedVariantsFileCreator),
        raredisease_config=raredisease_config,
    )

    # GIVEN a case run directory
    case_run_directory = Path("/path/to/dir")

    # WHEN calling configure
    copy_mock = mocker.patch.object(raredisease.shutil, "copy2")
    raredisease_extension.configure(case_id="case_id", case_run_directory=case_run_directory)

    # THEN the file creators should have been called
    raredisease_extension.gene_panel_file_creator.create.assert_called_once_with(
        case_id="case_id", file_path=case_run_directory / ScoutExportFileName.PANELS
    )
    raredisease_extension.managed_variants_file_creator.create.assert_called_once_with(
        case_id="case_id", file_path=case_run_directory / ScoutExportFileName.MANAGED_VARIANTS
    )

    # THEN the rank model files were copied to the case directory
    copy_mock.assert_any_call(
        Path("path/to/snv_rank_model.ini"), case_run_directory / "snv_rank_model.ini"
    )
    copy_mock.assert_any_call(
        Path("path/to/sv_rank_model.ini"), case_run_directory / "sv_rank_model.ini"
    )


def test_do_required_files_exist_true(raredisease_config: RarediseaseConfig, tmp_path: Path):
    # GIVEN that there is a gene panels, managed variants, snv and sv rank model files
    gene_panels_file = tmp_path / ScoutExportFileName.PANELS
    gene_panels_file.touch()
    managed_variants_file = tmp_path / ScoutExportFileName.MANAGED_VARIANTS
    managed_variants_file.touch()
    snv_rank_model_file = tmp_path / "snv_rank_model.ini"
    snv_rank_model_file.touch()
    sv_rank_model_file = tmp_path / "sv_rank_model.ini"
    sv_rank_model_file.touch()

    # GIVEN a Nallo extension
    raredisease_extension = RarediseaseExtension(
        gene_panel_file_creator=Mock(),
        managed_variants_file_creator=Mock(),
        raredisease_config=raredisease_config,
    )

    # WHEN checking that the required files exist
    does_exist: bool = raredisease_extension.do_required_files_exist(case_run_directory=tmp_path)

    # THEN the required file should exist
    assert does_exist


@pytest.mark.parametrize(
    "file_existence_array",
    [
        [False, True, True, True],
        [True, False, True, True],
        [True, True, False, True],
        [True, True, True, False],
    ],
    ids=[
        "missing gene panel scenario",
        "missing managed variants scenario",
        "missing snv rank model scenario",
        "missing sv rank model  scenario",
    ],
)
def test_do_required_files_exist(
    file_existence_array: list[bool],
    raredisease_config: RarediseaseConfig,
    tmp_path: Path,
):
    # GIVEN a case run directory
    case_run_directory = tmp_path
    file_map: dict[Path, bool] = {
        Path(case_run_directory, ScoutExportFileName.PANELS): file_existence_array[0],
        Path(case_run_directory, ScoutExportFileName.MANAGED_VARIANTS): file_existence_array[1],
        Path(case_run_directory, "snv_rank_model.ini"): file_existence_array[2],
        Path(case_run_directory, "sv_rank_model.ini"): file_existence_array[3],
    }

    # GIVEN that one required file does not exist
    for file, should_exist in file_map.items():
        if should_exist:
            file.touch()

    # GIVEN a raredisease extension
    raredisease_extension = RarediseaseExtension(
        gene_panel_file_creator=create_autospec(GenePanelFileCreator),
        managed_variants_file_creator=create_autospec(ManagedVariantsFileCreator),
        raredisease_config=raredisease_config,
    )

    # WHEN calling do_required_files_exist
    do_files_exist: bool = raredisease_extension.do_required_files_exist(case_run_directory)

    # THEN one of the files is marked as missing
    assert not do_files_exist
