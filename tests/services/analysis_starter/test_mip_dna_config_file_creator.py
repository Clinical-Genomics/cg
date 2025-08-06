from pathlib import Path
from unittest.mock import Mock

from pytest_mock import MockerFixture

from cg.services.analysis_starter.configurator.file_creators import mip_dna_config
from cg.services.analysis_starter.configurator.file_creators.mip_dna_config import (
    MIPDNAConfigFileCreator,
)


def test_create(mocker: MockerFixture):
    file_creator = MIPDNAConfigFileCreator(lims_api=Mock(), store=Mock())

    mock_write = mocker.patch.object(mip_dna_config, "write_yaml")

    file_creator.create("case_id")

    mock_write.assert_called_once_with(content="expected_content", file_path=Path("expected_path"))
