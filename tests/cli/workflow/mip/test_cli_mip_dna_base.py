""" Test the CLI for run mip-dna """
#import click
import logging
#import pytest

from cg.cli.workflow.mip_dna.base import decompress_spring
from cg.meta.workflow.mip import MipAnalysisAPI

CASE_ID = "yellowhog"


def test_mip_dna(cli_runner, mip_context, caplog, mocker):
    caplog.set_level(logging.INFO)

    # GIVEN fastqs are all decompressed and linked
    mocker.patch.object(MipAnalysisAPI, "get_other_format_in_same_folder")
    MipAnalysisAPI.get_other_format_in_same_folder.return_value = [
                        "/path/HVCHCCCXY-l4t11_535422_S4_L004_R1_001.fastq.gz",
                        "/path/HVCHCCCXY-l4t11_535422_S4_L004_R2_001.fastq.gz",
                        "/path/HVCHCCCXY-l4t21_535422_S4_L004_R1_001.fastq.gz",
                        "/path/HVCHCCCXY-l4t21_535422_S4_L004_R2_001.fastq.gz"
    ]

    mocker.patch.object(MipAnalysisAPI, "collect_hk_data")
    MipAnalysisAPI.collect_hk_data.return_value = [
                        "/path/HVCHCCCXY-l4t11_535422_S4_L004_R1_001.fastq.gz",
                        "/path/HVCHCCCXY-l4t11_535422_S4_L004_R2_001.fastq.gz",
                        "/path/HVCHCCCXY-l4t21_535422_S4_L004_R1_001.fastq.gz",
                        "/path/HVCHCCCXY-l4t21_535422_S4_L004_R2_001.fastq.gz"
    ]

    # WHEN calling decompress_spring
    result = cli_runner.invoke(
        decompress_spring, ["-c", CASE_ID, "--dry-run"], obj=mip_context, catch_exceptions=False
    )

    # THEN no error should be thrown
    assert result.exit_code == 0
    # THEN should not output "Decompression is running"
    assert "Decompression is running" not in caplog.text
    # THEN should not output "Started decompression"
    assert "Started decompression" not in caplog.text
    # THEN should not output "Creating links"
    assert "Creating links" not in caplog.text
    # THEN mip should start
    assert "All fastq files decompressed and linked" in caplog.text


def test_case_none(cli_runner, mip_context, caplog):
    # GIVEN no case is given in input

    # WHEN calling decompress_spring
    cli_runner.invoke(
        decompress_spring, ["-c", None, "--dry-run"], obj=mip_context, catch_exceptions=False
    )

    # THEN cases are suggested
    assert "provide a case, suggestions:" in caplog.text


def test_decompression_is_running(cli_runner, mip_context, caplog, mocker):
    caplog.set_level(logging.WARNING)

    # GIVEN there are fastq files compressed to spring
    mocker.patch.object(MipAnalysisAPI, "collect_hk_data")
    MipAnalysisAPI.collect_hk_data.return_value = [
                            "/path/HVCHCCCXY-l4t11_535422_S4_L004.spring",
                            "/path/HVCHCCCXY-l4t21_535422_S4_L004.spring"
    ]

    # GIVEN there are both fastq files and spring files in the folder
    mocker.patch.object(MipAnalysisAPI, "collect_files_in_folder")
    MipAnalysisAPI.collect_files_in_folder.return_value = [
        "/path/HVCHCCCXY-l4t11_535422_S4_L004.spring",
        "/path/HVCHCCCXY-l4t21_535422_S4_L004.spring",
        "/path/HVCHCCCXY-l4t11_535422_S4_L004_R1_001.fastq.gz",
        "/path/HVCHCCCXY-l4t11_535422_S4_L004_R2_001.fastq.gz",
        "/path/HVCHCCCXY-l4t21_535422_S4_L004_R1_001.fastq.gz",
        "/path/HVCHCCCXY-l4t21_535422_S4_L004_R2_001.fastq.gz"
    ]

    # GIVEN decompression is running
    mocker.patch.object(MipAnalysisAPI, "check_system_call")
    MipAnalysisAPI.check_system_call.return_value = "ACC6541A34_P8753U126_S3_L003_fastq_to_spring"

    # WHEN calling decompress_spring
    cli_runner.invoke(
        decompress_spring, ["-c", CASE_ID, "--dry-run"], obj=mip_context, catch_exceptions=False
    )

    # THEN warning about that decompression is running
    assert "No analysis started, decompression is running" in caplog.text
    # THEN mip start is canceled
    #with pytest.raises(click.Abort):
    #    assert "No analysis started, decompression is running" in caplog.text


def test_decompression_needed_dryrun(cli_runner, mip_context, caplog, mocker):
    caplog.set_level(logging.WARNING)

    # GIVEN there are fastq files compressed to spring
    mocker.patch.object(MipAnalysisAPI, "collect_hk_data")
    MipAnalysisAPI.collect_hk_data.return_value = [
        "/path/HVCHCCCXY-l4t11_535422_S4_L004.spring",
        "/path/HVCHCCCXY-l4t21_535422_S4_L004.spring"
    ]

    # GIVEN there are spring files, but no fastq files, in the folder
    mocker.patch.object(MipAnalysisAPI, "collect_files_in_folder")
    MipAnalysisAPI.collect_files_in_folder.return_value = [
        "/path/HVCHCCCXY-l4t11_535422_S4_L004.spring",
        "/path/HVCHCCCXY-l4t21_535422_S4_L004.spring",
    ]

    # GIVEN no decompression is running
    mocker.patch.object(MipAnalysisAPI, "check_system_call")
    MipAnalysisAPI.check_system_call.return_value = None

    # WHEN calling decompress_spring
    cli_runner.invoke(
        decompress_spring, ["-c", CASE_ID, "--dry-run"], obj=mip_context, catch_exceptions=False
    )

    # THEN warning about that analysis can't start (but it is a dry-run)
    assert "no decompression will be started, this is a dry run" in caplog.text


def test_start_decompression(cli_runner, mip_context, caplog, mocker):
    caplog.set_level(logging.WARNING)

    # GIVEN there are fastq files compressed to spring
    mocker.patch.object(MipAnalysisAPI, "collect_hk_data")
    MipAnalysisAPI.collect_hk_data.return_value = [
        "/path/HVCHCCCXY-l4t11_535422_S4_L004.spring",
        "/path/HVCHCCCXY-l4t21_535422_S4_L004.spring"
    ]

    # GIVEN there are spring files, but no fastq files, in the folder
    mocker.patch.object(MipAnalysisAPI, "collect_files_in_folder")
    MipAnalysisAPI.collect_files_in_folder.return_value = [
        "/path/HVCHCCCXY-l4t11_535422_S4_L004.spring",
        "/path/HVCHCCCXY-l4t21_535422_S4_L004.spring",
    ]

    # GIVEN no decompression is running
    mocker.patch.object(MipAnalysisAPI, "check_system_call")
    MipAnalysisAPI.check_system_call.return_value = None

    # WHEN calling decompress_spring
    cli_runner.invoke(
        decompress_spring, ["-c", CASE_ID], obj=mip_context, catch_exceptions=False
    )

    # THEN warning about that analysis can't start since decompression is needed
    assert "No analysis started, started decompression for" in caplog.text


def test_decompression_when_some_samples_decompressed(cli_runner, mip_context, caplog, mocker):
    caplog.set_level(logging.WARNING)

    # GIVEN there are fastq files compressed to spring
    mocker.patch.object(MipAnalysisAPI, "collect_hk_data")
    MipAnalysisAPI.collect_hk_data.return_value = [
        "/path/HVCHCCCXY-l4t11_535422_S4_L004.spring",
        "/path/HVCHCCCXY-l4t21_535422_S4_L004.spring"
    ]

    # GIVEN there spring for two samples, and fastqs for one sample
    mocker.patch.object(MipAnalysisAPI, "collect_files_in_folder")
    MipAnalysisAPI.collect_files_in_folder.return_value = [
        "/path/HVCHCCCXY-l4t11_535422_S4_L004.spring",
        "/path/HVCHCCCXY-l4t21_535422_S4_L004.spring",
        "/path/HVCHCCCXY-l4t21_535422_S4_L004_R1_001.fastq.gz",
        "/path/HVCHCCCXY-l4t21_535422_S4_L004_R2_001.fastq.gz"
    ]

    # GIVEN no decompression is running
    mocker.patch.object(MipAnalysisAPI, "check_system_call")
    MipAnalysisAPI.check_system_call.return_value = None

    # WHEN calling decompress_spring
    cli_runner.invoke(
        decompress_spring, ["-c", CASE_ID], obj=mip_context, catch_exceptions=False
    )

    # THEN warning about that analysis can't start since decompression is needed
    assert "No analysis started, started decompression for" in caplog.text


def test_linking_fastqs(cli_runner, mip_context, caplog, mocker):
    caplog.set_level(logging.INFO)

    # GIVEN there are fastq files in the spring folder
    mocker.patch.object(MipAnalysisAPI, "get_other_format_in_same_folder")
    MipAnalysisAPI.get_other_format_in_same_folder.return_value = [
                                    "/path/HVCHCCCXY-l4t11_535422_S4_L004_R1_001.fastq.gz",
                                    "/path/HVCHCCCXY-l4t11_535422_S4_L004_R2_001.fastq.gz",
                                    "/path/HVCHCCCXY-l4t21_535422_S4_L004_R1_001.fastq.gz",
                                    "/path/HVCHCCCXY-l4t21_535422_S4_L004_R2_001.fastq.gz"
    ]

    # GIVEN there are no fastq files linked in housekeeper
    mocker.patch.object(MipAnalysisAPI, "collect_hk_data")
    MipAnalysisAPI.collect_hk_data.return_value = []

    # GIVEN decompression is not running
    mocker.patch.object(MipAnalysisAPI, "check_system_call")
    MipAnalysisAPI.check_system_call.return_value = None

    # WHEN calling decompress_spring
    cli_runner.invoke(
        decompress_spring, ["-c", CASE_ID], obj=mip_context, catch_exceptions=False
    )

    # THEN info about that links are made
    assert "Adding links for" in caplog.text


def test_linking_fastqs_dryrun(cli_runner, mip_context, caplog, mocker):
    caplog.set_level(logging.INFO)

    # GIVEN there are fastq files in the spring folder
    mocker.patch.object(MipAnalysisAPI, "get_other_format_in_same_folder")
    MipAnalysisAPI.get_other_format_in_same_folder.return_value = [
                                    "/path/HVCHCCCXY-l4t11_535422_S4_L004_R1_001.fastq.gz",
                                    "/path/HVCHCCCXY-l4t11_535422_S4_L004_R2_001.fastq.gz",
                                    "/path/HVCHCCCXY-l4t21_535422_S4_L004_R1_001.fastq.gz",
                                    "/path/HVCHCCCXY-l4t21_535422_S4_L004_R2_001.fastq.gz"
    ]

    # GIVEN there are no fastq files linked in housekeeper
    mocker.patch.object(MipAnalysisAPI, "collect_hk_data")
    MipAnalysisAPI.collect_hk_data.return_value = []

    # GIVEN decompression is not running
    mocker.patch.object(MipAnalysisAPI, "check_system_call")
    MipAnalysisAPI.check_system_call.return_value = None

    # WHEN calling decompress_spring
    cli_runner.invoke(
        decompress_spring, ["-c", CASE_ID, "--dry-run"], obj=mip_context, catch_exceptions=False
    )

    # THEN info about that links are made
    assert "Would have linked fastqs, but this is dry-run mode" in caplog.text
