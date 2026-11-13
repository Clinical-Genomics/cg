from pathlib import Path
from unittest.mock import Mock, create_autospec

import pytest
from housekeeper.store.models import Bundle, Version
from pyfakefs.fake_filesystem import FakeFilesystem

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.exc import MandatoryFileMissingError
from cg.io.yaml import write_yaml_stream
from cg.services.storing_service.store_analysis_service import store_analysis_output
from cg.store.models import Analysis
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock


def test_store_pipeline_output_success(fs: FakeFilesystem):
    # GIVEN a case_deliverables file for a given case
    contents = [
        {
            "file_type": "the_first_type_of_file",
            "id": "case_id",
            "paths": ["/root_directory/case_id/file1.txt"],
            "mandatory": False,
        },
        {
            "file_type": "a_second_type_of_file",
            "id": "sample_id",
            "paths": ["/root_directory/case_id/file2.txt", "/root_directory/case_id/file3.txt"],
            "mandatory": True,
        },
        {
            "file_type": "a_third_type_of_file",
            "id": "case_id",
            "paths": ["/root_directory/case_id/file4.txt"],
            "mandatory": True,
        },
    ]
    contents = write_yaml_stream(contents)
    fs.create_file("/root_directory/case_id/case_id_deliverables.yaml", contents=contents)

    # GIVEN that the case has all mandatory files present
    fs.create_file("/root_directory/case_id/file2.txt")
    fs.create_file("/root_directory/case_id/file3.txt")
    fs.create_file("/root_directory/case_id/file4.txt")

    # GIVEN a HousekeeperAPI
    housekeeper_api: TypedMock[HousekeeperAPI] = create_typed_mock(HousekeeperAPI)
    housekeeper_api.as_type.add_bundle = Mock(
        return_value=(create_autospec(Bundle), create_autospec(Version, id=13))
    )

    # GIVEN a StatusDB with an analysis linked to a case
    status_db: TypedMock[Store] = create_typed_mock(Store)
    status_db.as_type.get_analysis_by_entry_id_strict = Mock(
        return_value=create_autospec(Analysis, case_internal_id="case_id", id=1)
    )

    # WHEN storing the pipeline outputs
    store_analysis_output(
        analysis_id=1,
        root_directory=Path("/root_directory"),
        housekeeper_api=housekeeper_api.as_type,
        status_db=status_db.as_type,
    )

    # THEN the housekeeper bundle for the case should have been created
    expected_bundle_data = {
        "name": "case_id",
        "files": [
            {
                "path": "/root_directory/case_id/file2.txt",
                "file_type": "a_second_type_of_file",
                "tags": ["sample_id"],
            },
            {
                "path": "/root_directory/case_id/file3.txt",
                "file_type": "a_second_type_of_file",
                "tags": ["sample_id"],
            },
            {
                "path": "/root_directory/case_id/file4.txt",
                "file_type": "a_third_type_of_file",
                "tags": ["case_id"],
            },
        ],
    }
    housekeeper_api.as_mock.add_bundle.assert_called_once_with(bundle_data=expected_bundle_data)

    # THEN the analysis in StatusDB was updated with a Housekeeper version
    status_db.as_mock.update_analysis_housekeeper_version_id.assert_called_once_with(
        analysis_id=1, version_id=13
    )


def test_store_output_pipeline_output_missing_mandatory_file(fs: FakeFilesystem):
    # GIVEN a case with deliverables file
    contents = [
        {
            "file_type": "the_first_type_of_file",
            "id": "case_id",
            "paths": ["/root_directory/case_id/file1.txt"],
            "mandatory": True,
        }
    ]
    contents = write_yaml_stream(contents)
    fs.create_file("/root_directory/case_id/case_id_deliverables.yaml", contents=contents)

    # GIVEN that a mandatory file does not exist

    # GIVEN a StatusDB with an analysis linked to a case
    status_db: Store = create_autospec(Store)
    status_db.get_analysis_by_entry_id_strict = Mock(
        return_value=create_autospec(Analysis, case_internal_id="case_id", id=1)
    )

    # WHEN storing the pipeline outputs
    # THEN a MandatoryFileMissingError was raised
    with pytest.raises(MandatoryFileMissingError):
        store_analysis_output(
            analysis_id=1,
            root_directory=Path("/root_directory"),
            housekeeper_api=Mock(),
            status_db=status_db,
        )
