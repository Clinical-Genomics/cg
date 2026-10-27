from pathlib import Path
from unittest.mock import create_autospec

from cg.models.cg_config import TranaConfig
from cg.services.analysis_starter.configurator.extensions.trana_extension import TranaExtension
from cg.services.analysis_starter.configurator.file_creators.nextflow.case_deliverables_file_creator import (
    CaseDeliverablesFileCreator,
)
from tests.typed_mock import TypedMock, create_typed_mock


def test_configure():
    # GIVEN a CaseDeliverablesFileCreator
    case_deliverables_file_creator: TypedMock[CaseDeliverablesFileCreator] = create_typed_mock(
        CaseDeliverablesFileCreator
    )

    # GIVEN a Trana config
    trana_config = create_autospec(TranaConfig, pipeline_deliverables=Path("path/to/template.yaml"))

    # GIVEN a Trana extension
    trana_extension = TranaExtension(
        case_deliverables_file_creator=case_deliverables_file_creator.as_type,
        trana_config=trana_config,
    )

    # WHEN configure is called
    trana_extension.configure(case_id="case_id", case_run_directory=Path("path/to/case"))

    # THEN the case deliverables file should have been created
    case_deliverables_file_creator.as_mock.create.assert_called_once_with(
        case_id="case_id",
        file_path=Path("path/to/case/case_id_deliverables.yaml"),
        pipeline_deliverables=Path("path/to/template.yaml"),
    )
