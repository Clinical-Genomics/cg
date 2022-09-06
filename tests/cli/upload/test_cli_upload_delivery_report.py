"""Tests the cli for uploading delivery reports"""

from cg.cli.upload.delivery_report import upload_delivery_report_to_scout
from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.meta.report.mip_dna import MipDNAReportAPI


def test_delivery_report_to_scout_no_params(upload_context, cli_runner):
    """Tests the upload to Scout without specifying the case"""

    # GIVEN a MIP-DNA report api
    assert isinstance(upload_context.meta_apis.get("report_api"), MipDNAReportAPI)

    # WHEN invoking the delivery report upload without parameters
    result = cli_runner.invoke(
        upload_delivery_report_to_scout,
        obj=upload_context,
    )

    # THEN the command should fail due to a missing case ID
    assert "There are no valid cases to perform delivery report actions" in result.output
    assert result.exit_code == EXIT_FAIL


def test_delivery_report_to_scout(upload_context, cli_runner, upload_report_hk_api, case_id):
    """Tests the upload to Scout of a MIP DNA delivery report"""

    # GIVEN a Housekeeper context with a delivery report file that is ready for upload
    upload_context.housekeeper_api_ = upload_report_hk_api

    # WHEN uploading the delivery report
    result = cli_runner.invoke(
        upload_delivery_report_to_scout,
        [case_id],
        obj=upload_context,
    )

    # THEN check that the command exits with success and that the mock file has been uploaded to Scout
    assert result.exit_code == EXIT_SUCCESS
