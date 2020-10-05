"""Tests for meta compress functionality that updates housekeeper"""

from cg.constants import HK_FASTQ_TAGS
from cg.meta.compress import files


def test_add_fastq_housekeeper(
    compress_api, real_housekeeper_api, decompress_hk_spring_bundle, compression_files, helpers
):
    """Test functionality to add fastq files to housekeeper

    This is done after a decompressed spring archives
    """
    # GIVEN real housekeeper api populated with a housekeeper bundle with spring info
    hk_bundle = decompress_hk_spring_bundle
    sample_id = hk_bundle["name"]
    helpers.ensure_hk_bundle(real_housekeeper_api, hk_bundle)
    compress_api.hk_api = real_housekeeper_api
    # GIVEN that there are no fastq files in HK
    version_obj = compress_api.get_latest_version(sample_id)
    file_tags = set()
    for file_obj in version_obj.files:
        for tag in file_obj.tags:
            file_tags.add(tag.name)
    assert not set(HK_FASTQ_TAGS).intersection(file_tags)

    # WHEN adding the files to housekeeper
    compress_api.add_fastq_hk(
        sample_id=sample_id,
        fastq_first=compression_files.fastq_first_file,
        fastq_second=compression_files.fastq_second_file,
    )

    # THEN assert that the fastq files where added to HK
    version_obj = compress_api.get_latest_version(sample_id)
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
    helpers,
):
    """Test functionality to add decompressed fastq files """
    # GIVEN real housekeeper api populated with a housekeeper bundle with spring info
    hk_bundle = decompress_hk_spring_bundle
    sample_id = hk_bundle["name"]
    helpers.ensure_hk_bundle(real_housekeeper_api, hk_bundle)
    compress_api.hk_api = real_housekeeper_api
    # GIVEN that there exists a spring archive, spring metadata and unpacked fastqs
    version_obj = compress_api.get_latest_version(sample_id)
    fastq_first = compression_files.fastq_first_file
    fastq_second = compression_files.fastq_second_file
    spring_file = compression_files.spring_file
    spring_metadata_file = compression_files.updated_spring_metadata_file
    assert files.is_file_in_version(version_obj=version_obj, path=spring_file)
    assert files.is_file_in_version(version_obj=version_obj, path=spring_metadata_file)

    assert not files.is_file_in_version(version_obj=version_obj, path=fastq_first)

    # WHEN adding decompresed files
    compress_api.add_decompressed_fastq(sample_id)

    # THEN assert that the files where added
    version_obj = compress_api.get_latest_version(sample_id)
    assert files.is_file_in_version(version_obj=version_obj, path=spring_file)
    assert files.is_file_in_version(version_obj=version_obj, path=spring_metadata_file)

    assert files.is_file_in_version(version_obj=version_obj, path=fastq_first)
    assert files.is_file_in_version(version_obj=version_obj, path=fastq_second)
