from pathlib import Path
from unittest.mock import create_autospec

from pytest_mock import MockerFixture

from cg.apps.demultiplex.sample_sheet.sample_sheet_models import SampleSheet
from cg.constants import Workflow
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet import rnafusion
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.rnafusion import (
    RNAFusionSampleSheetCreator,
)
from cg.store.models import Case, Sample
from cg.store.store import Store


def test_rnafusion_sample_sheet_creator(
    rnafusion_sample_sheet_content_list: list[list[str]],
    rnafusion_sample_sheet_creator: RNAFusionSampleSheetCreator,
    rnafusion_case_id: str,
    mocker: MockerFixture,
):

    case_path = Path("some", "path")
    write_mock = mocker.patch.object(rnafusion, "write_csv")

    mock_case = create_autospec(Case)
    mock_case.data_analysis = Workflow.RNAFUSION
    mock_sample = create_autospec(Sample)
    mock_sample.internal_id = "rna_sample"
    mock_case.samples = [mock_sample]
    mocker.patch.object(Store, "get_case_by_internal_id", return_value=mock_case)
    rnafusion_sample_sheet_creator.create(case_id=rnafusion_case_id, case_path=case_path)

    write_mock.assert_called_with(
        content=rnafusion_sample_sheet_content_list,
        file_path=rnafusion_sample_sheet_creator.get_file_path(
            case_path=case_path, case_id=rnafusion_case_id
        ),
    )
