"""Test the cli for uploading delivery reports"""

import logging
from datetime import datetime

from cg.cli.upload.base import delivery_report
from cg.constants import Pipeline

EXIT_CODE_SUCCESS = 0


def test_no_parameters(base_context, cli_runner, caplog):
    # GIVEN we have a report_api set up
    assert base_context.get("report_api")

    # WHEN calling delivery_report without parameters
    with caplog.at_level(logging.INFO):
        result = cli_runner.invoke(delivery_report, [], obj=base_context)

    # THEN it should fail on missing case_id
    assert result.exit_code != EXIT_CODE_SUCCESS
    assert "provide a case, suggestions:" in caplog.text


def test_analysis_started_at(base_context, cli_runner, caplog, helpers):

    # GIVEN a correct case_id and a correct date
    analysis = helpers.add_analysis(
        base_context["status_db"], started_at=datetime.now(), pipeline=Pipeline.MIP_DNA
    )
    case_id = analysis.family.internal_id
    a_date = analysis.started_at
    assert a_date

    # WHEN calling delivery_report with ok date parameter
    with caplog.at_level(logging.INFO):
        result = cli_runner.invoke(
            delivery_report,
            [case_id, "--analysis-started-at", a_date],
            obj=base_context,
        )

    # THEN it should contain the date in the logged info
    assert str(a_date) in caplog.text


def test_analysis_without_started_at(base_context, cli_runner, caplog, helpers):

    # GIVEN a correct case_id and a correct date
    analysis = helpers.add_analysis(
        base_context["status_db"], started_at=datetime.now(), pipeline=Pipeline.MIP_DNA
    )
    case_id = analysis.family.internal_id
    a_date = analysis.started_at
    assert a_date

    # WHEN calling delivery_report without date parameter
    with caplog.at_level(logging.DEBUG):
        result = cli_runner.invoke(
            delivery_report,
            [case_id],
            obj=base_context,
        )

    # THEN it should contain the date in the logged info
    assert "using analysis date: " in caplog.text
