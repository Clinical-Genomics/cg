from unittest.mock import Mock, create_autospec

from click.testing import CliRunner, Result

from cg.cli.sequencing_qc.sequencing_qc import sequencing_qc
from cg.constants.process import EXIT_FAIL, EXIT_SUCCESS
from cg.models.cg_config import CGConfig
from cg.services.sequencing_qc_service.sequencing_qc_service import SequencingQCService


def test_sequencing_qc_succeeds(cli_runner: CliRunner):
    # GIVEN a context with a sequencing qc service and run_sequencing_qc returns True
    sequencing_qc_service: SequencingQCService = create_autospec(SequencingQCService)
    sequencing_qc_service.run_sequencing_qc = Mock(return_value=True)
    context: CGConfig = create_autospec(CGConfig, sequencing_qc_service=sequencing_qc_service)

    # WHEN the sequencing command is called
    result: Result = cli_runner.invoke(sequencing_qc, [], obj=context)

    # THEN the command exited succesfully
    assert result.exit_code == EXIT_SUCCESS


def test_sequencing_qc_fails(cli_runner: CliRunner):
    # GIVEN a context with a sequencing qc service and run_sequencing_qc returns False
    sequencing_qc_service: SequencingQCService = create_autospec(SequencingQCService)
    sequencing_qc_service.run_sequencing_qc = Mock(return_value=False)

    context: CGConfig = create_autospec(CGConfig, sequencing_qc_service=sequencing_qc_service)

    # WHEN the sequencing command is called
    result: Result = cli_runner.invoke(sequencing_qc, [], obj=context)

    # THEN the command exits with a failure code
    assert result.exit_code == EXIT_FAIL
