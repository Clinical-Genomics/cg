from pathlib import Path

from click.testing import CliRunner
from mock import mock

from cg.cli.workflow.raredisease.base import panel, raredisease
from cg.constants import EXIT_SUCCESS, FileExtensions
from cg.io.txt import read_txt
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.models.cg_config import CGConfig
from tests.conftest import create_process_response


def test_raredisease_no_args(cli_runner: CliRunner, raredisease_context: CGConfig):
    """Test to see that running RAREDISEASE without options prints help and doesn't result in an error."""
    # GIVEN no arguments or options besides the command call

    # WHEN running command
    result = cli_runner.invoke(raredisease, [], obj=raredisease_context)

    # THEN command runs successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN help should be printed
    assert "help" in result.output


def test_panel_file_is_written(
    raredisease_case_id: str,
    cli_runner: CliRunner,
    raredisease_context: CGConfig,
    scout_panel_output: str,
):
    # GIVEN an analysis API
    analysis_api: RarediseaseAnalysisAPI = raredisease_context.meta_apis["analysis_api"]

    # GIVEN a case

    # GIVEN that, the Scout command writes the panel to stdout
    with mock.patch(
        "cg.utils.commands.subprocess.run",
        return_value=create_process_response(std_out=scout_panel_output),
    ):
        # WHEN creating a panel file
        cli_runner.invoke(panel, [raredisease_case_id], obj=raredisease_context)

    panel_file = Path(analysis_api.root, raredisease_case_id, f"gene_panels{FileExtensions.BED}")

    # THEN the file should exist
    assert panel_file.exists()

    # THEN the file should contain the output from Scout
    file_content: str = read_txt(file_path=panel_file, read_to_string=True)
    assert file_content == scout_panel_output
