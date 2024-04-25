"""Tests for meta compress functionality that updates housekeeper."""

from pathlib import Path
from typing import Generator

from housekeeper.store.models import File, Version

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import HK_FASTQ_TAGS, SequencingFileTag
from cg.meta.compress import CompressAPI, files
from cg.store.models import Sample
from cg.store.store import Store
from tests.cli.conftest import MockCompressAPI
from tests.meta.compress.conftest import MockCompressionData
from tests.store_helpers import StoreHelpers


def test_get_flow_cell_id_when_hiseqx(
    compress_api: CompressAPI,
    hiseq_x_single_index_flow_cell_id: str,
    hiseq_x_single_index_flow_cell_name: str,
):
    """Test extracting the flow cell id from a fastq file path."""

    # GIVEN a CompressAPI and a flow cell id within a fastq file path
    fastq_path: Path = compress_api.demux_root.joinpath(
        Path(
            hiseq_x_single_index_flow_cell_name,
            f"{hiseq_x_single_index_flow_cell_id}-l6t11_Undetermined_GACGTCTT_L006_R1_001.fastq.gz",
        )
    )

    # WHEN retrieving the flow cell id
    returned_flow_cell_name: str = compress_api.get_flow_cell_id(fastq_path=fastq_path)

    # THEN the flow cell id retrieved should be identical to the flow cell id used
    assert returned_flow_cell_name == hiseq_x_single_index_flow_cell_id


def test_get_flow_cell_id_when_novaseq(
    compress_api: CompressAPI,
    novaseq_6000_pre_1_5_kits_flow_cell_id: str,
    novaseq_6000_pre_1_5_kits_flow_cell_full_name: str,
):
    """Test extracting the flow cell id from a fastq file path."""

    # GIVEN a CompressAPI and a flow cell id within a fastq file path
    fastq_path: Path = compress_api.demux_root.joinpath(
        Path(
            novaseq_6000_pre_1_5_kits_flow_cell_full_name,
            f"{novaseq_6000_pre_1_5_kits_flow_cell_id}_ACC10950A36_S36_L001_R1_001.fastq.gz",
        )
    )

    # WHEN retrieving the flow cell id
    returned_flow_cell_name: str = compress_api.get_flow_cell_id(fastq_path=fastq_path)

    # THEN the flow cell id retrieved should be identical to the flow cell id used
    assert returned_flow_cell_name == novaseq_6000_pre_1_5_kits_flow_cell_id


def test_add_fastq_housekeeper_when_no_fastq_in_hk(
    compress_api: MockCompressAPI,
    real_housekeeper_api: Generator[HousekeeperAPI, None, None],
    decompress_hk_spring_bundle: dict,
    compression_files: MockCompressionData,
    store: Store,
    helpers: StoreHelpers,
):
    """Test adding fastq files to Housekeeper when no fastq files in Housekeeper."""

    # GIVEN real Housekeeper API populated with a bundle with SPRING metadata
    hk_bundle: dict = decompress_hk_spring_bundle
    sample_id: str = hk_bundle["name"]
    helpers.ensure_hk_bundle(store=real_housekeeper_api, bundle_data=hk_bundle)
    sample: Sample = helpers.add_sample(store=store, internal_id=sample_id)
    compress_api.hk_api = real_housekeeper_api

    # GIVEN that there are no FASTQ files in HK
    version: Version = compress_api.hk_api.get_latest_bundle_version(bundle_name=sample_id)
    file_tags: set = set()
    for file_obj in version.files:
        for tag in file_obj.tags:
            file_tags.add(tag.name)
    assert not set(HK_FASTQ_TAGS).intersection(file_tags)

    # WHEN adding the files to housekeeper
    compress_api.add_fastq_hk(
        sample_internal_id=sample.internal_id,
        fastq_first=compression_files.fastq_first_file,
        fastq_second=compression_files.fastq_second_file,
        fastq_tags=compress_api.get_fastq_tag_names(compression_files.spring_path),
    )

    # THEN assert that the FASTQ files where added to HK
    file_tags = set()
    for file_obj in version.files:
        for tag in file_obj.tags:
            file_tags.add(tag.name)

    assert set(HK_FASTQ_TAGS).intersection(file_tags)


def test_add_decompressed_fastq(
    compress_api: MockCompressAPI,
    real_housekeeper_api: Generator[HousekeeperAPI, None, None],
    decompress_hk_spring_bundle: dict,
    compression_files: MockCompressionData,
    store: Store,
    helpers: StoreHelpers,
    hk_bundle_sample_path: Path,
):
    """Test functionality to add decompressed FASTQ files."""

    # GIVEN real HK API populated with a HK bundle with SPRING info
    hk_bundle: dict = decompress_hk_spring_bundle
    sample_id: str = hk_bundle["name"]
    sample: Sample = helpers.add_sample(store, internal_id=sample_id)
    helpers.ensure_hk_bundle(real_housekeeper_api, hk_bundle)
    compress_api.hk_api = real_housekeeper_api

    # GIVEN that there exists a SPRING archive, spring metadata and unpacked FASTQs
    version: Version = compress_api.hk_api.get_latest_bundle_version(bundle_name=sample_id)
    fastq_first: Path = compression_files.fastq_first_file
    fastq_second: Path = compression_files.fastq_second_file
    spring_file: Path = compression_files.spring_file
    spring_metadata_file: Path = compression_files.updated_spring_metadata_file
    assert files.is_file_in_version(version_obj=version, path=spring_file)
    assert files.is_file_in_version(version_obj=version, path=spring_metadata_file)
    assert not files.is_file_in_version(version_obj=version, path=fastq_first)
    assert not files.is_file_in_version(version_obj=version, path=fastq_second)

    # WHEN adding decompressed files
    was_decompressed: bool = compress_api.add_decompressed_fastq(sample=sample)

    # THEN check that the files were actually decompressed
    assert was_decompressed

    # THEN assert that the FASTQ files have been added with a relative path
    assert files.is_file_in_version(
        version_obj=version, path=Path(hk_bundle_sample_path, fastq_first.name)
    )
    assert files.is_file_in_version(
        version_obj=version, path=Path(hk_bundle_sample_path, fastq_second.name)
    )


def test_get_fastq_tag_names(
    compress_api: MockCompressAPI, helpers: StoreHelpers, hk_sample_bundle: dict
):
    """Test that the correct tags for a fastq file are returned given a spring file."""

    # GIVEN a spring file
    helpers.ensure_hk_bundle(store=compress_api.hk_api, bundle_data=hk_sample_bundle)
    spring_file: File = compress_api.hk_api.files(tags={SequencingFileTag.SPRING}).first()
    assert spring_file

    # GIVEN that the spring_file is tagged with more than 'spring'
    assert len(spring_file.tags) > 1 and SequencingFileTag.SPRING in [
        tag.name for tag in spring_file.tags
    ]

    # WHEN getting fastq tags from its path
    fastq_tags: list[str] = compress_api.get_fastq_tag_names(Path(spring_file.path))

    # THEN the fastq tags should contain all non-spring tags of the spring file
    for tag_name in [tag.name for tag in spring_file.tags]:
        if tag_name != SequencingFileTag.SPRING:
            assert tag_name in fastq_tags

    # THEN the fastq tags should contain the fastq tag
    assert SequencingFileTag.FASTQ in fastq_tags

    # THEN the fastq tags should not contain the spring tag
    assert SequencingFileTag.SPRING not in fastq_tags
