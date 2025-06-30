from pathlib import Path

from pytest_mock import MockerFixture

from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file import rnafusion
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.rnafusion import (
    RNAFusionParamsFileCreator,
)


def test_rnafusion_params_file_creator_success(
    rnafusion_context: CGConfig,
    rnafusion_params_file_creator: RNAFusionParamsFileCreator,
    mocker: MockerFixture,
):
    # GIVEN an RNAFusion Params file creator
    write_mock = mocker.patch.object(rnafusion, "write_yaml_nextflow_style", return_value=None)
    case_path = Path("case", "path")
    sample_sheet_path = Path("some", "path")
    case_id = "case_id"

    # WHEN creating the RNAFusion params file
    rnafusion_params_file_creator.create(
        case_id=case_id, case_path=case_path, sample_sheet_path=sample_sheet_path
    )

    # THEN the file should have been created correctly
    expected_params = {"someparam": "something"} | {"input": sample_sheet_path, "outdir": case_path}
    write_mock.assert_called_once_with(
        file_path=rnafusion_params_file_creator.get_file_path(case_path=case_path, case_id=case_id),
        content=expected_params,
    )
