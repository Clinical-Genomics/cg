"""Tests for the prepare_fastq_api"""

from unittest import mock

import pytest

from cg.apps.crunchy import CrunchyAPI, crunchy
from cg.meta.compress import files
from cg.meta.compress.compress import CompressAPI
from cg.meta.workflow.prepare_fastq import PrepareFastqAPI
from cg.models import CompressionData
from cg.store.models import Case
from cg.store.store import Store


def test_is_spring_decompression_needed_when_true(
    populated_compress_spring_api: CompressAPI,
    analysis_store_single_case: Store,
    case_id: str,
    sample_id: str,
):
    """Test when spring decompression is needed."""

    # GIVEN a populated prepare_fastq_api
    prepare_fastq_api = PrepareFastqAPI(
        store=analysis_store_single_case, compress_api=populated_compress_spring_api
    )
    # GIVEN a store with a case that has linked samples
    case_obj: Case = analysis_store_single_case.get_case_by_internal_id(internal_id=case_id)
    assert case_obj
    # GIVEN that the case has linked samples
    link_objects = [link_obj for link_obj in case_obj.links]
    assert link_objects
    # GIVEN a that there exists a version with only spring in housekeeper
    version_object = populated_compress_spring_api.hk_api.get_latest_bundle_version(
        bundle_name=sample_id
    )
    for file in version_object.files:
        assert file.path.endswith(".spring")

    # WHEN checking if spring decompression is needed
    res = prepare_fastq_api.is_spring_decompression_needed(case_id)

    # THEN assert that spring decompression is needed since there are no fastq files
    assert res is True


def test_is_spring_decompression_needed_when_false(
    populated_compress_api_fastq_spring: CompressAPI,
    analysis_store_single_case: Store,
    case_id: str,
):
    """Test when spring decompression is not needed"""

    # GIVEN a populated prepare_fastq_api
    prepare_fastq_api = PrepareFastqAPI(
        store=analysis_store_single_case, compress_api=populated_compress_api_fastq_spring
    )
    # GIVEN a store with a case that has linked samples
    case_obj: Case = analysis_store_single_case.get_case_by_internal_id(internal_id=case_id)
    assert case_obj
    # GIVEN that the case has linked samples
    link_objects = [link_obj for link_obj in case_obj.links]
    assert link_objects

    # WHEN checking if spring decompression is needed
    res = prepare_fastq_api.is_spring_decompression_needed(case_id)

    # THEN assert that spring decompression is not needed since there are fastq files
    assert res is False


def test_at_least_one_sample_be_decompressed(
    populated_compress_spring_api: CompressAPI,
    analysis_store_single_case: Store,
    case_id: str,
    mocker,
):
    # GIVEN spring decompression is possible
    mocker.patch.object(CrunchyAPI, "is_spring_decompression_possible")
    CrunchyAPI.is_spring_decompression_possible.return_value = True

    # GIVEN a populated prepare_fastq_api
    prepare_fastq_api = PrepareFastqAPI(
        store=analysis_store_single_case, compress_api=populated_compress_spring_api
    )

    # WHEN checking if spring decompression is possible
    res = prepare_fastq_api.can_at_least_one_sample_be_decompressed(case_id=case_id)

    # THEN assert that spring decompression is possible
    assert res is True


def test_no_samples_can_be_decompressed(
    populated_compress_spring_api: CompressAPI,
    analysis_store_single_case: Store,
    case_id: str,
    mocker,
):
    # GIVEN spring decompression is not possible
    mocker.patch.object(CrunchyAPI, "is_spring_decompression_possible")
    CrunchyAPI.is_spring_decompression_possible.return_value = False

    # GIVEN a populated prepare_fastq_api
    prepare_fastq_api = PrepareFastqAPI(
        store=analysis_store_single_case, compress_api=populated_compress_spring_api
    )

    # WHEN checking if spring decompression is possible
    res = prepare_fastq_api.can_at_least_one_sample_be_decompressed(case_id=case_id)

    # THEN assert that spring decompression is not possible
    assert res is False


@pytest.mark.parametrize("file_exists_and_is_accessible", [False, True])
def test_fastq_should_be_added_to_housekeeper(
    populated_compress_spring_api: CompressAPI,
    analysis_store_single_case: Store,
    case_id: str,
    sample_id: str,
    file_exists_and_is_accessible: bool,
):
    """Test when FASTQ needs to be added to Housekeeper."""

    # GIVEN a populated prepare_fastq_api and a case that has linked samples
    prepare_fastq_api = PrepareFastqAPI(
        store=analysis_store_single_case, compress_api=populated_compress_spring_api
    )

    # GIVEN that there exists nr_of_files_before files in Housekeeper before adding any
    version_object = populated_compress_spring_api.hk_api.get_latest_bundle_version(
        bundle_name=sample_id
    )
    nr_of_files_before: int = len(list(version_object.files))

    # GIVEN that the decompressed files exist
    with mock.patch.object(
        CompressionData, "file_exists_and_is_accessible", return_value=file_exists_and_is_accessible
    ), mock.patch.object(crunchy.files, "get_crunchy_metadata", returnvalue=[]):
        # WHEN adding decompressed fastq files
        prepare_fastq_api.add_decompressed_fastq_files_to_housekeeper(case_id)

    # THEN assert that fastq files were added
    version_object = populated_compress_spring_api.hk_api.get_latest_bundle_version(
        bundle_name=sample_id
    )

    if file_exists_and_is_accessible:
        assert len(list(version_object.files)) > nr_of_files_before
    else:
        assert len(list(version_object.files)) == nr_of_files_before


def test_add_decompressed_fastqs_loops_through_samples(
    case_id: str, analysis_store: Store, populated_compress_spring_api: CompressAPI
):
    """Tests that given a case id, add_decompressed_fastq_files_to_housekeeper loops through all related samples."""

    # GIVEN a case with three samples and a PrepareFastqAPI
    prepare_fastq_api = PrepareFastqAPI(
        store=analysis_store, compress_api=populated_compress_spring_api
    )
    with mock.patch.object(
        PrepareFastqAPI, "add_decompressed_sample", return_value=True
    ) as request_counter:
        # WHEN adding decompressed fastq files to Housekeeper
        prepare_fastq_api.add_decompressed_fastq_files_to_housekeeper(case_id)

    case = analysis_store.get_case_by_internal_id(case_id)

    # THEN each sample should have had their fastq files added to Housekeeper.
    assert request_counter.call_count == len(case.samples)


def test_add_decompressed_sample_loops_through_spring(
    case_id: str,
    analysis_store: Store,
    populated_compress_spring_api: CompressAPI,
    spring_file,
):
    """Tests that given a sample id, all fastq files are added to Housekeeper
    in add_decompressed_sample_to_housekeeper."""

    # GIVEN a case and one of its samples, which in turn has a spring file in Housekeeper but no fastq files
    prepare_fastq_api = PrepareFastqAPI(
        store=analysis_store, compress_api=populated_compress_spring_api
    )
    case = analysis_store.get_case_by_internal_id(case_id)
    sample = case.samples[0]

    with mock.patch.object(
        files,
        "get_hk_files_dict",
        return_value={},
    ), mock.patch.object(
        files,
        "get_spring_paths",
        return_value=[CompressionData(spring_file.with_suffix(""))],
    ), mock.patch.object(
        CompressAPI, "add_decompressed_fastq", return_value=True
    ) as request_submitter:
        # WHEN adding decompressed fastq files to Housekeeper
        prepare_fastq_api.add_decompressed_sample(case=case, sample=sample)

    # THEN the related fastq files should have been added to Housekeeper
    assert request_submitter.call_count == 1
