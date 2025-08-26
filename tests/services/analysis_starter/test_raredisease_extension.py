from pathlib import Path
from unittest.mock import create_autospec

import pytest
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


@pytest.mark.parametrize(
    "does_gene_panel_exist, does_managed_variants_exist, expected_value",
    [
        (False, False, False),
        (False, True, False),
        (True, False, False),
        (True, True, True),
    ],
    ids=[
        "neither file exists",
        "only managed variants file exists",
        "only gene panel file exists",
        "both files exist",
    ],
)
def test_do_required_files_exist(
    does_gene_panel_exist: bool,
    does_managed_variants_exist: bool,
    expected_value: bool,
    mocker: MockerFixture,
):
    # GIVEN a case run directory
    case_run_directory = Path("root")
    file_map: dict[Path, bool] = {
        Path(case_run_directory, GENE_PANEL_FILE_NAME): does_gene_panel_exist,
        Path(case_run_directory, MANAGED_VARIANTS_FILE_NAME): does_managed_variants_exist,
    }

    # GIVEN that one required file exists and one does not
    isfile_mock = mocker.patch.object(raredisease, "isfile")
    isfile_mock.side_effect = lambda path: file_map.get(path, False)

    # GIVEN a raredisease extension
    raredisease_extension = RarediseaseExtension(
        gene_panel_file_creator=create_autospec(GenePanelFileCreator),
        managed_variants_file_creator=create_autospec(ManagedVariantsFileCreator),
    )

    # WHEN calling do_required_files_exist
    do_files_exist: bool = raredisease_extension.do_required_files_exist(case_run_directory)

    # THEN the return values should be as expected
    assert do_files_exist == expected_value
