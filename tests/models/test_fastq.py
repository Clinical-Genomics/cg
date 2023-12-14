from cg.models.fastq import FastqFileMeta


def test_instantiate_fastq_file_meta(fastq_file_meta_raw: dict):
    # GIVEN a dictionary with fastq info

    # WHEN instantiating object
    fast_file_meta = FastqFileMeta.model_validate(fastq_file_meta_raw)

    # THEN assert that it was successfully created
    assert isinstance(fast_file_meta, FastqFileMeta)


def test_fastq_file_mets_convert_to_int(fastq_file_meta_raw: dict):
    # GIVEN a dictionary with fastq info

    # WHEN instantiating object
    fast_file_meta = FastqFileMeta.model_validate(fastq_file_meta_raw)

    # THEN assert that str is converted to int
    assert isinstance(fast_file_meta.lane, int)

    assert isinstance(fast_file_meta.read_direction, int)
