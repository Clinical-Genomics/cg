""" This file groups all tests related to microsalt start creation """

from cg.cli.workflow.microsalt.base import run

EXIT_SUCCESS = 0


def test_no_arguments(cli_runner, base_context):
    """Test command without any options"""

    # GIVEN

    # WHEN dry running without anything specified
    result = cli_runner.invoke(run, obj=base_context)

    # THEN command should mention missing arguments
    assert result.exit_code != EXIT_SUCCESS


def test_dry_arguments(cli_runner, base_context, microbial_order_id, queries_path):
    """Test command dry """

    # GIVEN

    # WHEN dry running without anything specified
    result = cli_runner.invoke(run, ["--dry", microbial_order_id], obj=base_context)

    # THEN command should mention missing arguments
    assert result.exit_code == EXIT_SUCCESS

    outfilename = queries_path / microbial_order_id
    outfilename = outfilename.with_suffix(".json")
    assert f"/bin/true --parameters {outfilename}" in result.output
