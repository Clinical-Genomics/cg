""" Test cg.cli.upload.vogue module """

from cg.cli.upload.vogue import reagent_labels
import logging


def test_cli_upload_vogue_reagent_labes(vogue_context, cli_runner, caplog):
    """"""

    # GIVEN a vogue api
    caplog.set_level(logging.DEBUG)

    # WHEN running vogue load reagent_labels with the days argument
    result = cli_runner.invoke(reagent_labels, ["-d", 1], obj=vogue_context)

    # THEN assert that the correct information was communicated
    assert "REAGENT LABELS" in caplog.text
    # THEN assert that the program exits without errors
    assert result.exit_code == 0


def test_cli_upload_vogue_reagent_labes_no_days(vogue_context, cli_runner):
    """"""

    # GIVEN a vogue api

    # WHEN running vogue load reagent_labels without the days argument
    result = cli_runner.invoke(reagent_labels, [], obj=vogue_context)

    # THEN assert that the program exits with a non zero exit code
    assert result.exit_code != 0
