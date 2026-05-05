from unittest.mock import create_autospec

from click.testing import CliRunner, Result
from pytest_mock import MockerFixture

from cg.cli.workflow.raw_data import base
from cg.cli.workflow.raw_data.base import store_raw_data_analysis
from cg.cli.workflow.raw_data.raw_data_service import RawDataAnalysisService
from cg.models.cg_config import CGConfig


def test_store_raw_data_analysis(
    cli_runner: CliRunner,
    mocker: MockerFixture,
):
    """Test for CLI command creating an analysis object for a fastq case"""

    # GIVEN a raw data fastq context
    case_id = "fastq_raw_data_case"
    context = create_autospec(CGConfig)
    created_raw_data_analysis_service = create_autospec(RawDataAnalysisService)

    # GIVEN a raw data analaysis service can be instantiated
    raw_data_analysis_service_class = mocker.patch.object(
        base, "RawDataAnalysisService", autospec=True
    )
    raw_data_analysis_service_class.return_value = created_raw_data_analysis_service

    # WHEN a command is run to create and store an analysis for the case
    result: Result = cli_runner.invoke(store_raw_data_analysis, [case_id], obj=context)

    # THEN the analysis is stored by the RawDataAnalysisService
    assert not result.exception
    created_raw_data_analysis_service.store_analysis.assert_called_once_with(case_id)
