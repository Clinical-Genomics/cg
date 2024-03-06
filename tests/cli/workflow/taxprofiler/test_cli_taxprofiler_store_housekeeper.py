import logging
from pathlib import Path

import pytest
from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner
from pydantic import ValidationError

from cg.cli.workflow.taxprofiler.base import store_housekeeper
from cg.constants import EXIT_SUCCESS
from cg.constants.constants import FileFormat
from cg.io.controller import WriteStream
from cg.meta.workflow.taxprofiler import TaxprofilerAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.utils import Process


def test_case_with_malformed_deliverables_file(
    cli_runner,
    mocker,
    taxprofiler_context: CGConfig,
    taxprofiler_malformed_hermes_deliverables: dict,
    caplog: LogCaptureFixture,
    taxprofiler_case_id: str,
):
    """Test command with case_id and config file and analysis_finish but malformed deliverables output."""
    caplog.set_level(logging.WARNING)
    # GIVEN a malformed output from hermes
    analysis_api: TaxprofilerAnalysisAPI = taxprofiler_context.meta_apis["analysis_api"]

    # GIVEN that HermesAPI returns a malformed deliverables output
    mocker.patch.object(Process, "run_command")
    Process.run_command.return_value = WriteStream.write_stream_from_content(
        content=taxprofiler_malformed_hermes_deliverables, file_format=FileFormat.JSON
    )

    # GIVEN that the output is malformed
    with pytest.raises(ValidationError):
        analysis_api.hermes_api.convert_deliverables(
            deliverables_file=Path("a_file"), workflow="taxprofiler"
        )

        # GIVEN case-id
        case_id: str = taxprofiler_case_id

        # WHEN running
        result = cli_runner.invoke(store_housekeeper, [case_id], obj=taxprofiler_context)

        # THEN command should NOT execute successfully
        assert result.exit_code != EXIT_SUCCESS

        # THEN information that the file is malformed should be communicated
        assert "Deliverables file is malformed" in caplog.text
        assert "field required" in caplog.text
