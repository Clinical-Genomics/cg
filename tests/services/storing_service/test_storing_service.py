from pathlib import Path

from pyfakefs.fake_filesystem import FakeFilesystem

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.io.yaml import write_yaml_stream
from cg.services.storing_service.store_analysis_service import store_analysis_output
from tests.typed_mock import TypedMock, create_typed_mock


def test_store_pipeline_output_success(fs: FakeFilesystem):
    # GIVEN a case id with all mandatory files present
    # GIVEN a case_deliverables file for that given case
    contents = [
        {
            "file_type": "a_type_of_file",
            "id": "case_id",
            "paths": ["/root_directory/case_id/file1.txt"],
            "mandatory": False,
        },
        {
            "file_type": "a_type_of_file",
            "id": "case_id",
            "paths": ["/root_directory/case_id/file2.txt", "/root_directory/case_id/file3.txt"],
            "mandatory": True,
        },
    ]
    contents = write_yaml_stream(contents)
    fs.create_file("/root_directory/case_id/case_id_deliverables.yaml", contents=contents)
    fs.create_file("/root_directory/case_id/file2.txt")
    fs.create_file("/root_directory/case_id/file3.txt")

    # GIVEN a HousekeeperAPI
    housekeeper_api: TypedMock[HousekeeperAPI] = create_typed_mock(HousekeeperAPI)

    # WHEN storing the pipeline outputs
    store_analysis_output(
        root_directory=Path("/root_directory"),
        case_id="case_id",
        housekeeper_api=housekeeper_api.as_type,
    )
    # THEN the housekeeper bundle for the case should have been created
    expected_bundle_data = {
        "name": "case_id",
        "files": [
            {
                "path": "/root_directory/case_id/file2.txt",
                "file_type": "a_type_of_file",
                "tags": ["case_id"],
            },
            {
                "path": "/root_directory/case_id/file3.txt",
                "file_type": "a_type_of_file",
                "tags": ["case_id"],
            },
        ],
    }
    housekeeper_api.as_mock.add_bundle.assert_called_once_with(bundle_data=expected_bundle_data)
