"""Tests enabled commands for the generate command"""

from cg.constants import EXIT_SUCCESS

from cg.cli.generate.base import generate


def test_generate_no_options(base_context, cli_runner):
    """Tests generate command with no options"""

    # GIVEN a base context

    # WHEN dry running
    result = cli_runner.invoke(generate, obj=base_context)

    # THEN the output should list all the supported pipelines
    assert result.exit_code == EXIT_SUCCESS
    assert "delivery-report" in result.output
    assert "available-delivery-reports" in result.output
