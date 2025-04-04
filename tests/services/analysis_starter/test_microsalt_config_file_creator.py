from pathlib import Path
from unittest import mock
from cg.constants.constants import FileFormat
from cg.io.controller import WriteFile
from cg.services.analysis_starter.configurator.file_creators.microsalt_config import (
    MicrosaltConfigFileCreator,
)


def test_create_success(
    microsalt_config_file_creator: MicrosaltConfigFileCreator, microsalt_case_id: str
):
    # GIVEN a microsalt_config_file_creator
    with mock.patch.object(WriteFile, "write_file_from_content", return_value=True) as file_writer:
        # WHEN creating a microsalt config file
        microsalt_config_file_creator.create(microsalt_case_id)
        # THEN it should be written to disk as json
        file_writer.assert_called_once_with(
            content=mock.ANY,
            file_format=FileFormat.JSON,
            file_path=Path(
                microsalt_config_file_creator.queries_path,
                microsalt_case_id + "." + FileFormat.JSON,
            ),
        )
