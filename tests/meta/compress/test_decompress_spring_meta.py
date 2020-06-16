"""Test do decompress a spring archive"""
import logging


def test_decompress_spring(populated_decompress_spring_api, sample, caplog):
    """Test to compress all fastq files for a sample"""
    caplog.set_level(logging.DEBUG)
    compress_api = populated_decompress_spring_api
    # GIVEN a populated compress api
    spring_path = compress_api.get_spring_path(sample)
    assert spring_path.exists()
    spring_metadata_path = compress_api.crunchy_api.get_flag_path(spring_path)
    assert spring_metadata_path.exists()

    # WHEN Decompressing the spring file for the sample
    res = compress_api.decompress_spring(sample)

    # THEN assert compression succeded
    assert res is True
    # THEN assert that the correct information is communicated
    assert f"Decompressing {spring_path} to FASTQ format for sample {sample}" in caplog.text
    # THEN assert that the fastq compression was called once
    assert compress_api.crunchy_api.nr_fastq_compressions() == 1
