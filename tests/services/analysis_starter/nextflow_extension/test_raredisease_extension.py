from pathlib import Path
from unittest.mock import Mock

from cg.models.cg_config import RarediseaseConfig
from cg.services.analysis_starter.configurator.extensions.raredisease_extension import (
    GENE_PANEL_FILE_NAME,
    MANAGED_VARIANTS_FILE_NAME,
    RarediseaseExtension,
)
from cg.services.analysis_starter.configurator.file_creators.gene_panel import GenePanelFileCreator
from cg.services.analysis_starter.configurator.file_creators.managed_variants import (
    ManagedVariantsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.rank_model_file_copier import (
    RankModelFileCopier,
)
from tests.typed_mock import TypedMock, create_typed_mock


def test_configure(raredisease_config_object: RarediseaseConfig):
    # GIVEN a gene panel file creator
    gene_panel_file_creator: TypedMock[GenePanelFileCreator] = create_typed_mock(
        GenePanelFileCreator
    )

    # GIVEN a managed variants file creator
    managed_variants_file_creator: TypedMock[ManagedVariantsFileCreator] = create_typed_mock(
        ManagedVariantsFileCreator
    )

    # GIVEN a rank model file copier
    rank_model_file_copier: TypedMock[RankModelFileCopier] = create_typed_mock(RankModelFileCopier)

    # GIVEN a Raredisease extension
    raredisease_extension = RarediseaseExtension(
        gene_panel_file_creator=gene_panel_file_creator.as_type,
        managed_variants_file_creator=managed_variants_file_creator.as_type,
        rank_model_file_copier=rank_model_file_copier.as_type,
        raredisease_config=raredisease_config_object,
    )

    # GIVEN a case run directory
    case_run_directory = Path("case", "run", "directory")

    # WHEN configuring a case
    raredisease_extension.configure(case_id="case_id", case_run_directory=case_run_directory)

    # THEN a gene panel file should have been created
    gene_panel_file_creator.as_mock.create.assert_called_once_with(
        case_id="case_id", file_path=case_run_directory / GENE_PANEL_FILE_NAME
    )

    # THEN a managed variants file should have been created
    managed_variants_file_creator.as_mock.create.assert_called_once_with(
        case_id="case_id", file_path=case_run_directory / MANAGED_VARIANTS_FILE_NAME
    )

    # THEN the rank model files should have been copied to the case run directory
    rank_model_file_copier.as_mock.copy.assert_called_once_with(
        source_snv_file=raredisease_config_object.rank_model_snv,
        source_sv_file=raredisease_config_object.rank_model_sv,
        target_directory=case_run_directory,
    )


def test_do_required_files_exist_true(tmp_path: Path, raredisease_config_object: RarediseaseConfig):
    # GIVEN that there is a gene panel file, a managed variants file and rank model files
    (tmp_path / GENE_PANEL_FILE_NAME).touch()
    (tmp_path / MANAGED_VARIANTS_FILE_NAME).touch()
    (tmp_path / raredisease_config_object.rank_model_snv.name).touch()
    (tmp_path / raredisease_config_object.rank_model_sv.name).touch()

    # GIVEN a Raredisease extension
    raredisease_extension = RarediseaseExtension(
        gene_panel_file_creator=Mock(),
        managed_variants_file_creator=Mock(),
        rank_model_file_copier=Mock(),
        raredisease_config=raredisease_config_object,
    )

    # WHEN checking that the required files exist
    does_exist: bool = raredisease_extension.do_required_files_exist(case_run_directory=tmp_path)

    # THEN the required files should exist
    assert does_exist


def test_do_required_files_exist_false(
    tmp_path: Path, raredisease_config_object: RarediseaseConfig
):
    # GIVEN that there is no gene panel file
    gene_panel_file = tmp_path / GENE_PANEL_FILE_NAME
    assert not gene_panel_file.exists()

    # GIVEN a Raredisease extension
    raredisease_extension = RarediseaseExtension(
        gene_panel_file_creator=Mock(),
        managed_variants_file_creator=Mock(),
        rank_model_file_copier=Mock(),
        raredisease_config=raredisease_config_object,
    )

    # WHEN checking that the required files exist
    does_exist: bool = raredisease_extension.do_required_files_exist(case_run_directory=tmp_path)

    # THEN the required files should not exist
    assert not does_exist
