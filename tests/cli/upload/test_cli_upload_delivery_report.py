"""Test the cli for uploading delivery reports"""

# test with correct date correct data
# test with bad date
import logging
from datetime import datetime

from cg.cli.upload.base import delivery_report

EXIT_CODE_SUCCESS = 0


def test_no_parameters(base_context, cli_runner, caplog):
    # GIVEN we have a report_api set up

    # WHEN calling delivery_report without parameters
    with caplog.at_level(logging.INFO):
        result = cli_runner.invoke(delivery_report, [], obj=base_context)

    # THEN it should fail on missing case_id
    result.exit_code != EXIT_CODE_SUCCESS
    assert "provide a case, suggestions:" in caplog.text


def test_analysis_started_at(base_context, cli_runner, caplog, helpers):

    # GIVEN a correct case_id and a correct date
    analysis = helpers.add_analysis(base_context["status"], started_at=datetime.now())
    case_id = analysis.family.internal_id
    a_date = analysis.started_at

    # WHEN calling delivery_report with malformed date parameter
    with caplog.at_level(logging.INFO):
        result = cli_runner.invoke(delivery_report, [case_id, '--analysis-started-at', a_date],
                                   obj=base_context)

    # THEN it should contain the date in the logged info
    result.exit_code != EXIT_CODE_SUCCESS
    assert str(a_date) in caplog.text
