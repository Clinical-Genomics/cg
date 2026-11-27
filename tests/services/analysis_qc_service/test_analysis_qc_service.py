from pathlib import Path
from unittest.mock import Mock, create_autospec

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from cg.apps.tb.api import TrailblazerAPI
from cg.constants.tb import AnalysisStatus
from cg.exc import MandatoryFileMissingError
from cg.io.yaml import write_yaml_stream
from cg.services.analysis_qc_service import analysis_qc_service
from cg.store.models import Analysis, Case
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock


def test_perform_qc(fs: FakeFilesystem):
    # GIVEN a case with deliverables file
    contents = [
        {
            "file_type": "the_first_type_of_file",
            "id": "case_one",
            "paths": ["/root_directory/case_one/file1.txt"],
            "mandatory": True,
        }
    ]
    contents: str = write_yaml_stream(contents)
    fs.create_file("/root_directory/case_one/case_one_deliverables.yaml", contents=contents)

    # GIVEN that all mandatory files exist
    fs.create_file("/root_directory/case_one/file1.txt")

    # GIVEN a trailblazer api
    trailblazer_api: TypedMock[TrailblazerAPI] = create_typed_mock(TrailblazerAPI)

    # GIVEN a StatusDB with an analysis linked to a case
    status_db: Store = create_autospec(Store)
    case: Case = create_autospec(Case)
    case.get_deliverables_file = Mock(
        return_value=Path("/root_directory/case_one/case_one_deliverables.yaml")
    )
    status_db.get_analysis_by_entry_id_strict = Mock(
        return_value=create_autospec(Analysis, case=case, case_internal_id="case_one", id=1)
    )

    # WHEN performing QC and it is successful
    analysis_qc_service.perform_qc(
        root_directory=Path("root_directory"),
        status_db=status_db,
        trailblazer_api=trailblazer_api.as_type,
        analysis_id=1,
    )

    # THEN analysis was marked as completed in trailblazer
    trailblazer_api.as_mock.set_analysis_status.assert_called_once_with(
        analysis_id=1, status=AnalysisStatus.COMPLETED
    )


def test_perform_qc_mandatory_file_missing(fs: FakeFilesystem):
    # GIVEN a case with deliverables file
    contents = [
        {
            "file_type": "the_first_type_of_file",
            "id": "case_one",
            "paths": ["/root_directory/case_one/file1.txt"],
            "mandatory": True,
        }
    ]
    contents = write_yaml_stream(contents)
    fs.create_file("/root_directory/case_one/case_one_deliverables.yaml", contents=contents)

    # GIVEN that a mandatory file does not exist

    # GIVEN a Trailblazer API
    trailblazer_api: TypedMock[TrailblazerAPI] = create_typed_mock(TrailblazerAPI)

    # GIVEN a StatusDB with an analysis linked to a case
    status_db: Store = create_autospec(Store)
    case: Case = create_autospec(Case)
    case.get_deliverables_file = Mock(
        return_value=Path("/root_directory/case_one/case_one_deliverables.yaml")
    )
    status_db.get_analysis_by_entry_id_strict = Mock(
        return_value=create_autospec(Analysis, case=case, case_internal_id="case_one", id=1)
    )

    # WHEN performing QC
    # THEN a MandatoryFileMissingError was raised
    with pytest.raises(MandatoryFileMissingError):
        analysis_qc_service.perform_qc(
            root_directory=Path("root_directory"),
            status_db=status_db,
            trailblazer_api=trailblazer_api.as_type,
            analysis_id=1,
        )

    # THEN a status was set as failed in TB
    trailblazer_api.as_mock.set_analysis_status.assert_called_once_with(
        analysis_id=1, status=AnalysisStatus.FAILED
    )

    # THEN a helpful comment is added to the analysis in Trailblazer
    trailblazer_api.as_mock.add_comment.assert_called_once_with(
        analysis_id=1, comment="Mandatory files missing from case directory"
    )
