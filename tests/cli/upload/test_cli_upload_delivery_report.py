"""Tests the cli for uploading delivery reports"""

import logging

from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.cli.upload.delivery_report import mip_dna
from cg.meta.report.mip_dna import MipDNAReportAPI


def test_delivery_report_to_scout_no_params(upload_context, cli_runner, caplog):
    """Tests the upload to Scout no specifying the case"""

    caplog.set_level(logging.INFO)

    # GIVEN a MIP-DNA report api
    assert isinstance(upload_context.meta_apis.get("report_api"), MipDNAReportAPI)

    # WHEN invoking the delivery report upload without parameters
    result = cli_runner.invoke(
        mip_dna,
        ["delivery-report-to-scout"],
        obj=upload_context,
    )

    # THEN the command should fail due to a missing case ID
    assert result.exit_code == EXIT_FAIL
    assert "Provide a case, suggestions:" in caplog.text


def test_delivery_report_to_scout(
    upload_context, cli_runner, upload_report_hk_api, case_id, caplog
):
    """Tests the upload to Scout of a MIP DNA delivery report"""

    caplog.set_level(logging.INFO)

    # GIVEN a Housekeeper context with a delivery report file that is ready for upload
    upload_context.housekeeper_api_ = upload_report_hk_api

    # WHEN uploading the delivery report
    result = cli_runner.invoke(
        mip_dna,
        ["delivery-report-to-scout", case_id],
        obj=upload_context,
    )

    # THEN check that the command exits with success and that the mock file has been uploaded to Scout
    assert result.exit_code == EXIT_SUCCESS
    assert "Uploaded delivery report to Scout successfully" in caplog.text
