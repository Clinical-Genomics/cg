"""Test do decompress a spring archive"""

import logging


def test_decompress_spring(populated_decompress_spring_api, compression_files, sample, caplog):
    """Test to compress all fastq files for a sample"""
    caplog.set_level(logging.DEBUG)
    compress_api = populated_decompress_spring_api
    compress_api.crunchy_api.set_dry_run(True)
    # GIVEN a populated compress api
    spring_path = compression_files.spring_file
    # GIVEN that the spring paths exists
    assert spring_path.exists()
    spring_metadata_path = compression_files.spring_metadata_file
    assert spring_metadata_path.exists()
    # GIVEN that the fastq paths does not exist
    compression_files.fastq_first.unlink()
    compression_files.fastq_second.unlink()
    assert not compression_files.fastq_first.exists()
    assert not compression_files.fastq_second.exists()

    # WHEN Decompressing the spring file for the sample
    res = compress_api.decompress_spring(sample)

    # THEN assert compression succeded
    assert res is True
    # THEN assert that the correct information is communicated
    assert f"Decompressing {spring_path} to FASTQ format for sample {sample}" in caplog.text
