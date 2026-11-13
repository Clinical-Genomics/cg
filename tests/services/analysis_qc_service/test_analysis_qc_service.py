from pathlib import Path
from unittest.mock import Mock, create_autospec

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from cg.apps.tb.api import TrailblazerAPI
from cg.exc import MandatoryFileMissingError
from cg.io.yaml import write_yaml_stream
from cg.services.analysis_qc_service import analysis_qc_service
from cg.store.models import Analysis
from cg.store.store import Store


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
    contents = write_yaml_stream(contents)
    fs.create_file("/root_directory/case_one/case_one_deliverables.yaml", contents=contents)

    # GIVEN that a mandatory file does not exist

    # GIVEN a StatusDB with an analysis linked to a case
    status_db: Store = create_autospec(Store)
    status_db.get_analysis_by_entry_id_strict = Mock(
        return_value=create_autospec(Analysis, case_internal_id="case_one", id=1)
    )

    # WHEN storing the pipeline outputs
    # THEN a MandatoryFileMissingError was raised
    with pytest.raises(MandatoryFileMissingError):
        analysis_qc_service.perform_qc(
            root_directory=Path("root_directory"),
            status_db=status_db,
            trailblazer_api=create_autospec(TrailblazerAPI),
            analysis_id=1,
        )
