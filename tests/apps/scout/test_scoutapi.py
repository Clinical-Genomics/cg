from unittest.mock import Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.apps.scout import scoutapi
from cg.apps.scout.scoutapi import ScoutAPI
from cg.exc import ScoutExportError
from cg.models.cg_config import CommonAppConfig
from cg.services.slurm_upload_service.slurm_upload_service import SlurmUploadService
from cg.utils.commands import Process


def test_export_panels_with_panel_output(mocker: MockerFixture):
    # GIVEN scout returns panel output
    process = create_autospec(
        Process,
        stdout="exported_1 exported_2",
    )
    process.stdout_lines = Mock(return_value=["exported_1", "exported_2"])
    mocker.patch.object(scoutapi, "Process", return_value=process)

    scout_api = ScoutAPI(
        scout_config=CommonAppConfig(binary_path="scout/binary", config_path="scout/config"),
        slurm_upload_service=create_autospec(SlurmUploadService),
    )

    # WHEN exporting panels
    result = scout_api.export_panels(panels=["some_panel", "another_panel"])

    # THEN the exported panel names are returned
    assert result == ["exported_1", "exported_2"]


def test_export_panels_with_empty_output(mocker: MockerFixture):
    # GIVEN scout returns no output
    process = create_autospec(Process, stdout=None)
    mocker.patch.object(scoutapi, "Process", return_value=process)

    scout_api = ScoutAPI(
        scout_config=CommonAppConfig(binary_path="scout/binary", config_path="scout/config"),
        slurm_upload_service=create_autospec(SlurmUploadService),
    )

    # WHEN exporting panels
    # THEN a ScoutExportError is raised
    with pytest.raises(ScoutExportError):
        scout_api.export_panels(panels=["some_panel", "another_panel"])
