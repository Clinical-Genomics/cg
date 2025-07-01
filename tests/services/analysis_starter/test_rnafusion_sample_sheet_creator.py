from pathlib import Path

from pytest_mock import MockerFixture

from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet import rnafusion
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.rnafusion import (
    RNAFusionSampleSheetCreator,
)


def test_rnafusion_sample_sheet_creator(
    rnafusion_sample_sheet_content_list: list[list[str]],
    rnafusion_sample_sheet_creator: RNAFusionSampleSheetCreator,
    rnafusion_case_id: str,
    mocker: MockerFixture,
):

    case_path = Path("some", "path")
    write_mock = mocker.patch.object(rnafusion, "write_csv")
    rnafusion_sample_sheet_creator.create(case_id=rnafusion_case_id, case_path=case_path)

    write_mock.assert_called_with(
        content=rnafusion_sample_sheet_content_list,
        file_path=rnafusion_sample_sheet_creator.get_file_path(
            case_path=case_path, case_id=rnafusion_case_id
        ),
    )
