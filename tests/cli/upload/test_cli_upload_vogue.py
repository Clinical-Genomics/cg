""" Test cg.cli.upload.vogue module """

import logging

from cg.cli.upload.vogue import flowcells, reagent_labels, samples
from cg.models.cg_config import CGConfig
from click.testing import CliRunner


def test_cli_upload_vogue_reagent_labes(upload_context: CGConfig, cli_runner: CliRunner, caplog):
    """Testing cli for upload vogue reagent_labels with correct argument"""

    # GIVEN a vogue api
    caplog.set_level(logging.DEBUG)

    # WHEN running vogue load reagent_labels with the days argument
    result = cli_runner.invoke(reagent_labels, ["-d", 1], obj=upload_context)

    # THEN assert that the correct information was communicated
    assert "REAGENT LABELS" in caplog.text
    # THEN assert that the program exits without errors
    assert result.exit_code == 0


def test_cli_upload_vogue_reagent_labes_no_days(upload_context: CGConfig, cli_runner: CliRunner):
    """ """

    # GIVEN a vogue api

    # WHEN running vogue load reagent_labels without the days argument
    result = cli_runner.invoke(reagent_labels, [], obj=upload_context)

    # THEN assert that the program exits with a non zero exit code
    assert result.exit_code != 0


def test_cli_upload_vogue_samples(upload_context: CGConfig, cli_runner: CliRunner, caplog):
    """Testing cli for upload vogue samples with correct argument"""

    # GIVEN a vogue api
    caplog.set_level(logging.DEBUG)

    # WHEN running vogue load samples with the days argument
    result = cli_runner.invoke(samples, ["-d", 1], obj=upload_context)

    # THEN assert that the correct information was communicated
    assert "SAMPLES" in caplog.text
    # THEN assert that the program exits without errors
    assert result.exit_code == 0


def test_cli_upload_vogue_samples_no_days(upload_context: CGConfig, cli_runner: CliRunner):
    """Testing cli for upload vogue samples with wrong argument"""

    # GIVEN a vogue api

    # WHEN running vogue load samples without the days argument
    result = cli_runner.invoke(samples, [], obj=upload_context)

    # THEN assert that the program exits with a non zero exit code
    assert result.exit_code != 0


def test_cli_upload_vogue_flowcells(upload_context: CGConfig, cli_runner: CliRunner, caplog):
    """Testing cli for upload vogue flowcells with correct argument"""

    # GIVEN a vogue api
    caplog.set_level(logging.DEBUG)

    # WHEN running vogue load flowcells with the days argument
    result = cli_runner.invoke(flowcells, ["-d", 1], obj=upload_context)

    # THEN assert that the correct information was communicated
    assert "FLOWCELLS" in caplog.text
    # THEN assert that the program exits without errors
    assert result.exit_code == 0


def test_cli_upload_vogue_flowcells_no_days(upload_context: CGConfig, cli_runner: CliRunner):
    """Testing cli for upload vogue flowcells with wrong argument"""

    # GIVEN a vogue api

    # WHEN running vogue load flowcells without the days argument
    result = cli_runner.invoke(flowcells, [], obj=upload_context)

    # THEN assert that the program exits with a non zero exit code
    assert result.exit_code != 0
