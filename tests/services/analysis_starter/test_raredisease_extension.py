from pathlib import Path
from unittest.mock import create_autospec

from pytest_mock import MockerFixture

from cg.services.analysis_starter.configurator.extensions import raredisease
from cg.services.analysis_starter.configurator.extensions.raredisease import (
    GENE_PANEL_FILE_NAME,
    MANAGED_VARIANTS_FILE_NAME,
    RarediseaseExtension,
)
from cg.services.analysis_starter.configurator.file_creators.gene_panel import GenePanelFileCreator
from cg.services.analysis_starter.configurator.file_creators.managed_variants import (
    ManagedVariantsFileCreator,
)


def test_configure_success():
    # GIVEN a raredisease pipeline extension
    raredisease_extension = RarediseaseExtension(
        gene_panel_file_creator=create_autospec(GenePanelFileCreator),
        managed_variants_file_creator=create_autospec(ManagedVariantsFileCreator),
    )
    # WHEN calling configure
    raredisease_extension.configure(case_id="case_id", case_run_directory=Path("/path/to/dir"))

    # THEN the file creators should have been called
    raredisease_extension.gene_panel_file_creator.create.assert_called_once_with(
        case_id="case_id", file_path=Path("/path/to/dir/", GENE_PANEL_FILE_NAME)
    )
    raredisease_extension.managed_variants_file_creator.create.assert_called_once_with(
        case_id="case_id", file_path=Path("/path/to/dir/", MANAGED_VARIANTS_FILE_NAME)
    )


def test_do_required_files_exist(mocker:MockerFixture):


    isfile_mock= mocker.patch.object(raredisease,"isfile")

    isfile_mock.side_effect = lambda path: True

    raredisease_extension = RarediseaseExtension(
        gene_panel_file_creator=create_autospec(GenePanelFileCreator),
        managed_variants_file_creator=create_autospec(ManagedVariantsFileCreator),
    )

    raredisease_extension.do_required_files_exist(Path("root/file"))

