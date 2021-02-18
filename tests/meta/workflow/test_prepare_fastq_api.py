"""Tests for the prepare_fastq_api"""

from cg.meta.compress.compress import CompressAPI
from cg.apps.crunchy import CrunchyAPI
from cg.store import Store
from cg.store.models import Family
from cg.meta.workflow.prepare_fastq import PrepareFastqAPI
from cg.meta.compress import files


def test_is_spring_decompression_needed_when_true(
    populated_compress_spring_api: CompressAPI, analysis_store_single_case: Store, case_id: str
):
    """Test when spring decompression is needed"""

    # GIVEN a populated prepare_fastq_api
    prepare_fastq_api = PrepareFastqAPI(
        store=analysis_store_single_case, compress_api=populated_compress_spring_api
    )
    # GIVEN a store with a case that has linked samples
    case_obj: Family = analysis_store_single_case.family(case_id)
    assert case_obj
    # GIVEN that the case has linked samples
    link_objects = [link_obj for link_obj in case_obj.links]
    assert link_objects
    # GIVEN a that there exists a version with only spring in housekeeper
    version_object = populated_compress_spring_api.get_latest_version("ADM1")
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
    case_obj: Family = analysis_store_single_case.family(case_id)
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


def test_at_least_one_decompression_job_starts(
    populated_compress_spring_api: CompressAPI,
    analysis_store_single_case: Store,
    case_id: str,
    mocker,
):
    # GIVEN spring decompression starts
    mocker.patch.object(CompressAPI, "decompress_spring")
    CompressAPI.decompress_spring.return_value = True

    # GIVEN a populated prepare_fastq_api
    prepare_fastq_api = PrepareFastqAPI(
        store=analysis_store_single_case, compress_api=populated_compress_spring_api
    )

    # WHEN attempting to start spring decompression
    res = prepare_fastq_api.can_at_least_one_decompression_job_start(case_id=case_id, dry_run=False)

    # THEN assert that spring decompression did start
    assert res is True


def test_no_decompression_job_starts(
    populated_compress_spring_api: CompressAPI,
    analysis_store_single_case: Store,
    case_id: str,
    mocker,
):
    # GIVEN spring decompression fail to start
    mocker.patch.object(CompressAPI, "decompress_spring")
    CompressAPI.decompress_spring.return_value = False

    # GIVEN a populated prepare_fastq_api
    prepare_fastq_api = PrepareFastqAPI(
        store=analysis_store_single_case, compress_api=populated_compress_spring_api
    )

    # WHEN attempting to start spring decompression
    res = prepare_fastq_api.can_at_least_one_decompression_job_start(case_id=case_id, dry_run=False)

    # THEN assert that spring decompression failed to start
    assert res is False


def test_no_fastq_in_housekeeper(
    populated_compress_spring_api: CompressAPI,
    analysis_store_single_case: Store,
    case_id: str,
):
    """Test when fastq needs to be added to housekeeper"""

    # GIVEN a populated prepare_fastq_api
    prepare_fastq_api = PrepareFastqAPI(
        store=analysis_store_single_case, compress_api=populated_compress_spring_api
    )
    # GIVEN a store with a case that has linked samples
    case_obj: Family = analysis_store_single_case.family(case_id)
    assert case_obj
    # GIVEN that the case has linked samples
    link_objects = [link_obj for link_obj in case_obj.links]
    assert link_objects
    # GIVEN a that there exists a version with only spring in housekeeper
    version_object = populated_compress_spring_api.get_latest_version("ADM1")
    for file in version_object.files:
        assert file.path.endswith(".spring")

    # WHEN checking if fastq files need to be added to housekeeper
    res = prepare_fastq_api.check_fastq_links(case_id)

    # THEN assert that all fastq files are not there
    assert res is None
