from pathlib import Path
from unittest.mock import Mock

from cg.constants.scout import ScoutExportFileName
from cg.models.cg_config import NalloConfig
from cg.services.analysis_starter.configurator.extensions.nallo_extension import NalloExtension
from cg.services.analysis_starter.configurator.file_creators.gene_panel import GenePanelFileCreator
from cg.services.analysis_starter.configurator.file_creators.rank_model_file_copier import (
    RankModelFileCopier,
)
from tests.typed_mock import TypedMock, create_typed_mock


def test_configure(nallo_config_object: NalloConfig):
    # GIVEN a gene panel file creator
    gene_panel_file_creator: TypedMock[GenePanelFileCreator] = create_typed_mock(
        GenePanelFileCreator
    )

    # GIVEN a rank model file copier
    rank_model_file_copier: TypedMock[RankModelFileCopier] = create_typed_mock(RankModelFileCopier)

    # GIVEN a Nallo extension
    nallo_extension = NalloExtension(
        gene_panel_file_creator=gene_panel_file_creator.as_type,
        rank_model_file_copier=rank_model_file_copier.as_type,
        nallo_config=nallo_config_object,
    )

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

    # THEN the rank model files should have been copied to the case run directory
    rank_model_file_copier.as_mock.copy.assert_called_once_with(
        source_snv_file=nallo_config_object.rank_model_snv,
        source_sv_file=nallo_config_object.rank_model_sv,
        target_directory=case_run_directory,
    )


def test_do_required_files_exist_true(tmp_path: Path, nallo_config_object: NalloConfig):
    # GIVEN that there is a gene panel tsv file and rank model files
    scout_file = tmp_path / ScoutExportFileName.PANELS_TSV
    scout_file.touch()
    (tmp_path / nallo_config_object.rank_model_snv.name).touch()
    (tmp_path / nallo_config_object.rank_model_sv.name).touch()

    # GIVEN a Nallo extension
    nallo_extension = NalloExtension(
        gene_panel_file_creator=Mock(),
        rank_model_file_copier=Mock(),
        nallo_config=nallo_config_object,
    )

    # WHEN checking that the required files exist
    does_exist: bool = nallo_extension.do_required_files_exist(case_run_directory=tmp_path)

    # THEN the required file should exist
    assert does_exist


def test_do_required_files_exist_false(tmp_path: Path, nallo_config_object: NalloConfig):
    # GIVEN that there is no gene panel tsv file
    scout_file = tmp_path / ScoutExportFileName.PANELS_TSV
    assert not scout_file.exists()

    # GIVEN a Nallo extension
    nallo_extension = NalloExtension(
        gene_panel_file_creator=Mock(),
        rank_model_file_copier=Mock(),
        nallo_config=nallo_config_object,
    )

    # WHEN checking that the required files exist
    does_exist: bool = nallo_extension.do_required_files_exist(case_run_directory=tmp_path)

    # THEN the required file should not exist
    assert not does_exist
