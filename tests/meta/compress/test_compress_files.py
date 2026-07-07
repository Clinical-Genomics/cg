"""Tests for the compression files module"""

import logging
from pathlib import Path

from cg.meta.compress import files
from cg.models.compression_data import CompressionData
from cg.store.models import IlluminaFlowCell, IlluminaSequencingRun
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def test_get_fastq_files(populated_compress_fastq_api, sample):
    """Test get_fastq_files method when there are FASTQ files"""
    compress_api = populated_compress_fastq_api
    # GIVEN a sample_id and a hk api populated with fastq bundle

    # WHEN fetching the fastq files
    version_obj = compress_api.hk_api.get_latest_bundle_version(bundle_name=sample)
    fastq_dict = files.get_fastq_files(sample_id=sample, version_obj=version_obj)
    run = list(fastq_dict.keys())[0]

    # THEN the fastq files will be in the dictionary
    assert set(fastq_dict[run].keys()) == set(["compression_data", "hk_first", "hk_second"])
    # THEN assert that a CompressionData object was returned
    assert isinstance(fastq_dict[run]["compression_data"], CompressionData)


def test_get_fastq_files_no_files(compress_api, sample_hk_bundle_no_files, sample, helpers, caplog):
    """Test get_fastq_files method when no FASTQ files are found"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a sample_id
    sample_id = sample
    hk_api = compress_api.hk_api
    # GIVEN a bundle without files
    assert sample_hk_bundle_no_files["files"] == []
    helpers.ensure_hk_bundle(hk_api, sample_hk_bundle_no_files)

    # WHEN fetching the fastq files
    version_obj = compress_api.hk_api.get_latest_bundle_version(bundle_name=sample)
    fastq_dict = files.get_fastq_files(sample_id=sample_id, version_obj=version_obj)

    # THEN assert that None is returned since there where not two files
    assert fastq_dict is None
    # THEN assert that the correct information is returned
    assert f"Could not find FASTQ files for {sample}" in caplog.text


def test_get_reads_for_run_found(base_store: Store, helpers: StoreHelpers):
    """Test get_reads_for_run when a matching sequencing metrics row exists."""
    # GIVEN a sample with sequencing metrics for a given flow cell and lane
    flow_cell_id = "23M7GHLT4"
    sample_id = "ACC20498A8"
    lane = 4
    flow_cell: IlluminaFlowCell = helpers.add_illumina_flow_cell(
        store=base_store, flow_cell_id=flow_cell_id
    )
    sequencing_run: IlluminaSequencingRun = helpers.add_illumina_sequencing_run(
        store=base_store, flow_cell=flow_cell
    )
    helpers.add_sample(store=base_store, internal_id=sample_id)
    helpers.add_illumina_sample_sequencing_metrics_object(
        store=base_store, sample_id=sample_id, sequencing_run=sequencing_run, lane=lane
    )

    # GIVEN a compression run whose name matches that flow cell/sample/lane
    compression_obj = CompressionData(Path(f"{flow_cell_id}_{sample_id}_S52_L00{lane}"))

    # WHEN looking up the reads for the run
    reads: int | None = files.get_reads_for_run(compression_obj, base_store)

    # THEN the total reads in the lane is returned
    assert reads == 100


def test_get_reads_for_run_name_does_not_match(base_store: Store):
    """Test get_reads_for_run returns None when the run name can't be parsed."""
    # GIVEN a compression run whose name doesn't follow the expected naming convention
    compression_obj = CompressionData(Path("not_a_valid_name"))

    # WHEN looking up the reads for the run
    # THEN None is returned
    assert files.get_reads_for_run(compression_obj, base_store) is None


def test_get_reads_for_run_no_matching_metrics(base_store: Store):
    """Test get_reads_for_run returns None when no metrics row matches."""
    # GIVEN a compression run that parses fine but has no matching sequencing metrics row
    compression_obj = CompressionData(Path("23M7GHLT4_UNKNOWNSAMPLE_S1_L001"))

    # WHEN looking up the reads for the run
    # THEN None is returned
    assert files.get_reads_for_run(compression_obj, base_store) is None
