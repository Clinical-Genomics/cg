import logging

from click.testing import CliRunner

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.store.fastq import (
    store_case,
    store_demultiplexed_flow_cell,
    store_flow_cell,
    store_sample,
    store_ticket,
)
from cg.constants import EXIT_SUCCESS
from cg.meta.compress import CompressAPI
from cg.models.cg_config import CGConfig
from cg.store import Store
from cg.store.models import Sample


def test_store_sample_when_no_samples(
    caplog, cli_runner: CliRunner, compress_context: CGConfig, sample_id: str
):
    """Test to run store samples command with a database without samples."""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context without samples

    # WHEN running the store sample command
    res = cli_runner.invoke(store_sample, [sample_id], obj=compress_context)

    # THEN assert the command exits successfully
    assert res.exit_code == EXIT_SUCCESS

    # THEN assert that we log that sample cannot be found
    assert f"Could not find {sample_id}" in caplog.text


def test_store_sample_when_decompression_not_finished(
    cli_runner: CliRunner, caplog, mocker, populated_compress_context: CGConfig, sample_id: str
):
    """Test to run store samples command when decompression is not finished."""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context with a sample

    # GIVEN that decompression is not finished
    mocker.patch.object(CompressAPI, "add_decompressed_fastq")
    CompressAPI.add_decompressed_fastq.return_value = False

    # WHEN running the store samples command
    res = cli_runner.invoke(store_sample, [sample_id], obj=populated_compress_context)

    # THEN assert that the command exits successfully
    assert res.exit_code == EXIT_SUCCESS

    # THEN assert that we log that we skip the sample
    assert f"Skipping sample {sample_id}" in caplog.text


def test_store_sample_when_decompression_finished(
    caplog, cli_runner: CliRunner, mocker, populated_compress_context: CGConfig, sample_id: str
):
    """Test to run store samples command when decompression is finished."""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context with a sample

    # GIVEN that decompression is finished
    mocker.patch.object(CompressAPI, "add_decompressed_fastq")
    CompressAPI.add_decompressed_fastq.return_value = True

    # WHEN running the store sample command
    res = cli_runner.invoke(store_sample, [sample_id], obj=populated_compress_context)

    # THEN assert that the command exits successfully
    assert res.exit_code == EXIT_SUCCESS

    # THEN assert that we log that we stored FASTQ files
    assert f"Stored fastq files for {sample_id}" in caplog.text


def test_store_case_when_no_case(
    caplog, case_id: str, cli_runner: CliRunner, compress_context: CGConfig
):
    """Test to run store case command when no case in database."""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context with no case

    # WHEN running the store case command
    res = cli_runner.invoke(store_case, [case_id], obj=compress_context)

    # THEN assert that the command exits successfully
    assert res.exit_code == EXIT_SUCCESS

    # THEN assert that we log that we cannot find the case
    assert f"Could not find case {case_id}" in caplog.text


def test_store_case(
    caplog,
    cli_runner: CliRunner,
    case_id: str,
    mocker,
    populated_compress_context: CGConfig,
    sample_id: str,
):
    """Test to run store case command."""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context with a case and a sample

    # GIVEN that decompression is not finished
    mocker.patch.object(CompressAPI, "add_decompressed_fastq")
    CompressAPI.add_decompressed_fastq.return_value = True

    # WHEN running the store case command
    res = cli_runner.invoke(store_case, [case_id], obj=populated_compress_context)

    # THEN assert that the command exits successfully
    assert res.exit_code == EXIT_SUCCESS

    # THEN assert that we log that we stored FASTQ files
    assert f"Stored fastq files for {sample_id}" in caplog.text


def test_store_flow_cell(
    caplog,
    cli_runner: CliRunner,
    flow_cell_id: str,
    mocker,
    populated_compress_context: CGConfig,
    sample_id: str,
):
    """Test to run store flow cell command."""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context with a sample
    sample: Sample = populated_compress_context.status_db.sample(sample_id)

    # GIVEN samples objects on a flow cell
    mocker.patch.object(Store, "get_samples_from_flow_cell")
    Store.get_samples_from_flow_cell.return_value = [sample]

    # GIVEN that decompression is not finished
    mocker.patch.object(CompressAPI, "add_decompressed_fastq")
    CompressAPI.add_decompressed_fastq.return_value = True

    # WHEN running the store flow cell command
    res = cli_runner.invoke(store_flow_cell, [flow_cell_id], obj=populated_compress_context)

    # THEN assert that the command exits successfully
    assert res.exit_code == EXIT_SUCCESS

    # THEN assert that we log that we stored FASTQ files
    assert f"Stored fastq files for {sample_id}" in caplog.text


def test_store_ticket(
    caplog,
    cli_runner: CliRunner,
    mocker,
    populated_compress_context: CGConfig,
    sample_id: str,
    ticket: str,
):
    """Test to run store ticket command."""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context with a sample

    # GIVEN that decompression is not finished
    mocker.patch.object(CompressAPI, "add_decompressed_fastq")
    CompressAPI.add_decompressed_fastq.return_value = True

    # WHEN running the store ticket command
    res = cli_runner.invoke(store_ticket, [ticket], obj=populated_compress_context)

    # THEN assert that the command exits successfully
    assert res.exit_code == EXIT_SUCCESS

    # THEN assert that we log that we stored FASTQ files
    assert f"Stored fastq files for {sample_id}" in caplog.text


def test_store_store_demultiplexed_flow_cell(
    caplog,
    cli_runner: CliRunner,
    flow_cell_id: str,
    helpers,
    mocker,
    real_populated_compress_context: CGConfig,
    sample_id: str,
):
    """Test to run store demultiplexed flow cell command."""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context with a sample
    sample: Sample = real_populated_compress_context.status_db.sample(sample_id)

    # GIVEN samples objects on a flow cell
    mocker.patch.object(Store, "get_samples_from_flow_cell")
    Store.get_samples_from_flow_cell.return_value = [sample]

    # GIVEN an updated metadata file
    mocker.patch("cg.cli.store.fastq.update_metadata_paths", return_value=None)

    # WHEN running the store demultiplexed flow cell command
    res = cli_runner.invoke(
        store_demultiplexed_flow_cell, [flow_cell_id], obj=real_populated_compress_context
    )

    # THEN assert that the command exits successfully
    assert res.exit_code == EXIT_SUCCESS
