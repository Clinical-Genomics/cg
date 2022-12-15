"""Tests for meta compress functionality that updates housekeeper"""

import logging
from pathlib import Path

from cg.constants import HK_FASTQ_TAGS
from cg.meta.compress import CompressAPI, files


def test_get_flow_cell_id_when_hiseqx(
    compress_api: CompressAPI, flow_cell_id: str, flow_cell_full_name: str
):
    """Test extracting the flow cell id from a fastq file path."""

    # GIVEN a CompressAPI and a flow cell id within a fastq file path
    fastq_path: Path = compress_api.demux_root.joinpath(
        Path(
            flow_cell_full_name, f"{flow_cell_id}-l6t11_Undetermined_GACGTCTT_L006_R1_001.fastq.gz"
        )
    )

    # WHEN retrieving the flow cell id
    returned_flow_cell_name: str = compress_api.get_flow_cell_id(fastq_path=fastq_path)

    # THEN the flow cell id retrieved should be identical to the flow cell id used
    assert returned_flow_cell_name == flow_cell_id


def test_get_flow_cell_id_when_novaseq(
    compress_api: CompressAPI, flow_cell_id: str, flow_cell_full_name: str
):
    """Test extracting the flow cell id from a fastq file path."""

    # GIVEN a CompressAPI and a flow cell id within a fastq file path
    fastq_path: Path = compress_api.demux_root.joinpath(
        Path(flow_cell_full_name, f"{flow_cell_id}_ACC10950A36_S36_L001_R1_001.fastq.gz")
    )

    # WHEN retrieving the flow cell id
    returned_flow_cell_name: str = compress_api.get_flow_cell_id(fastq_path=fastq_path)

    # THEN the flow cell id retrieved should be identical to the flow cell id used
    assert returned_flow_cell_name == flow_cell_id


def test_add_fastq_housekeeper_when_no_fastq_in_hk(
    caplog,
    compress_api,
    real_housekeeper_api,
    decompress_hk_spring_bundle,
    compression_files,
    store,
    helpers,
):
    """Test adding fastq files to Housekeeper when no fastq files in Housekeeper."""
    caplog.set_level(logging.INFO)

    # GIVEN real housekeeper api populated with a housekeeper bundle with spring info
    hk_bundle = decompress_hk_spring_bundle
    sample_id = hk_bundle["name"]
    helpers.ensure_hk_bundle(real_housekeeper_api, hk_bundle)
    sample_obj = helpers.add_sample(store, internal_id=sample_id)
    compress_api.hk_api = real_housekeeper_api
    # GIVEN that there are no fastq files in HK
    version_obj = compress_api.hk_api.get_latest_bundle_version(bundle_name=sample_id)
    file_tags = set()
    for file_obj in version_obj.files:
        for tag in file_obj.tags:
            file_tags.add(tag.name)
    assert not set(HK_FASTQ_TAGS).intersection(file_tags)

    # WHEN adding the files to housekeeper
    compress_api.add_fastq_hk(
        sample_obj=sample_obj,
        fastq_first=compression_files.fastq_first_file,
        fastq_second=compression_files.fastq_second_file,
    )

    # THEN assert that the fastq files where added to HK
    version_obj = compress_api.hk_api.get_latest_bundle_version(bundle_name=sample_id)
    file_tags = set()
    for file_obj in version_obj.files:
        for tag in file_obj.tags:
            file_tags.add(tag.name)

    assert set(HK_FASTQ_TAGS).intersection(file_tags)


def test_add_decompressed_fastq(
    compress_api,
    real_housekeeper_api,
    decompress_hk_spring_bundle,
    compression_files,
    store,
    helpers,
):
    """Test functionality to add decompressed FASTQ files."""
    # GIVEN real Housekeeper api populated with a Housekeeper bundle with SPRING meta data
    hk_bundle = decompress_hk_spring_bundle
    sample_id = hk_bundle["name"]
    sample = helpers.add_sample(store, internal_id=sample_id)
    helpers.ensure_hk_bundle(real_housekeeper_api, hk_bundle)
    compress_api.hk_api = real_housekeeper_api

    # GIVEN that there exists a SPRING archive, spring metadata and unpacked fastqs
    version = compress_api.hk_api.get_latest_bundle_version(bundle_name=sample_id)
    fastq_first = compression_files.fastq_first_file
    fastq_second = compression_files.fastq_second_file
    spring_file = compression_files.spring_file
    spring_metadata_file = compression_files.updated_spring_metadata_file
    assert files.is_file_in_version(version_obj=version, path=spring_file)
    assert files.is_file_in_version(version_obj=version, path=spring_metadata_file)

    assert not files.is_file_in_version(version_obj=version, path=fastq_first)

    # WHEN adding decompressed files
    compress_api.add_decompressed_fastq(sample=sample)

    # THEN assert that the files where added
    version = compress_api.hk_api.get_latest_bundle_version(bundle_name=sample_id)
    assert files.is_file_in_version(version_obj=version, path=spring_file)
    assert files.is_file_in_version(version_obj=version, path=spring_metadata_file)

    assert files.is_file_in_version(version_obj=version, path=fastq_first)
    assert files.is_file_in_version(version_obj=version, path=fastq_second)
