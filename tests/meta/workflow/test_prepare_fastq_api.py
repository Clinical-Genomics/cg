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
    # GIVEN a populated prepare_fastq_api
    prepare_fastq_api = PrepareFastqAPI(
        store=analysis_store_single_case, compress_api=populated_compress_spring_api
    )
    # GIVEN a store with a case that have linked samples
    case_obj: Family = analysis_store_single_case.family(case_id)
    assert case_obj
    # GIVEN that the case have linked samples
    link_objects = [link_obj for link_obj in case_obj.links]
    assert link_objects
    # GIVEN a that there exists a version with spring file ony in housekeeper
    version_object = populated_compress_spring_api.get_latest_version("ADM1")
    for file in version_object.files:
        assert file.path.endswith(".spring")

    # WHEN checking is spring decompression if needed
    res = prepare_fastq_api.is_spring_decompression_needed(case_id)

    # THEN assert that spring decompression is needed since there are no fastq files
    assert res is True


def test_is_spring_decompression_needed_when_false(
    populated_compress_api_fastq_spring: CompressAPI,
    analysis_store_single_case: Store,
    case_id: str,
):
    # GIVEN a populated prepare_fastq_api
    prepare_fastq_api = PrepareFastqAPI(
        store=analysis_store_single_case, compress_api=populated_compress_api_fastq_spring
    )
    # GIVEN a store with a case that have linked samples
    case_obj: Family = analysis_store_single_case.family(case_id)
    assert case_obj
    # GIVEN that the case have linked samples
    link_objects = [link_obj for link_obj in case_obj.links]
    assert link_objects
    # GIVEN a that there exists a version with spring file ony in housekeeper
    version_object = populated_compress_api_fastq_spring.get_latest_version("ADM1")
    print(version_object)
    compression_objects = files.get_spring_paths(version_object)
    print(compression_objects, compression_objects[0].pair_exists())

    # WHEN checking is spring decompression if needed
    res = prepare_fastq_api.is_spring_decompression_needed(case_id)

    # THEN assert that spring decompression is needed since there are fastq files
    assert res is False


def test_spring_decompression_starts(
    populated_compress_spring_api: CompressAPI,
    analysis_store_single_case: Store,
    case_id: str,
    mocker,
):

    mocker.patch.object(CompressAPI, "decompress_spring")
    CompressAPI.decompress_spring.return_value = True

    mocker.patch.object(CrunchyAPI, "is_spring_decompression_possible")
    CrunchyAPI.is_spring_decompression_possible.return_value = True

    # GIVEN a populated prepare_fastq_api
    prepare_fastq_api = PrepareFastqAPI(
        store=analysis_store_single_case, compress_api=populated_compress_spring_api
    )

    # WHEN checking is spring decompression if needed
    res = prepare_fastq_api.start_spring_decompression(case_id)

    # THEN assert that spring decompression is needed since there are no fastq files
    assert res is True


def test_spring_decompression_do_not_start(
    populated_compress_spring_api: CompressAPI,
    analysis_store_single_case: Store,
    case_id: str,
    mocker,
):

    mocker.patch.object(CompressAPI, "decompress_spring")
    CompressAPI.decompress_spring.return_value = False

    mocker.patch.object(CrunchyAPI, "is_spring_decompression_possible")
    CrunchyAPI.is_spring_decompression_possible.return_value = False

    # GIVEN a populated prepare_fastq_api
    prepare_fastq_api = PrepareFastqAPI(
        store=analysis_store_single_case, compress_api=populated_compress_spring_api
    )

    # WHEN checking is spring decompression if needed
    res = prepare_fastq_api.start_spring_decompression(case_id)

    # THEN assert that spring decompression is needed since there are no fastq files
    assert res is False


def test_no_fastq_in_housekeeper(
    populated_compress_spring_api: CompressAPI,
    analysis_store_single_case: Store,
    case_id: str,
):

    # GIVEN a populated prepare_fastq_api
    prepare_fastq_api = PrepareFastqAPI(
        store=analysis_store_single_case, compress_api=populated_compress_spring_api
    )
    # GIVEN a store with a case that have linked samples
    case_obj: Family = analysis_store_single_case.family(case_id)
    assert case_obj
    # GIVEN that the case have linked samples
    link_objects = [link_obj for link_obj in case_obj.links]
    assert link_objects
    # GIVEN a that there exists a version with spring file ony in housekeeper
    version_object = populated_compress_spring_api.get_latest_version("ADM1")
    for file in version_object.files:
        assert file.path.endswith(".spring")

    # WHEN checking is spring decompression if needed
    res = prepare_fastq_api.check_fastq_links(case_id)

    # THEN assert that spring decompression is needed since there are no fastq files
    assert res is False


def test_fastq_in_housekeeper(
    populated_compress_api_fastq_spring: CompressAPI,
    analysis_store_single_case: Store,
    case_id: str,
):
    # GIVEN a populated prepare_fastq_api
    prepare_fastq_api = PrepareFastqAPI(
        store=analysis_store_single_case, compress_api=populated_compress_api_fastq_spring
    )
    # GIVEN a store with a case that have linked samples
    case_obj: Family = analysis_store_single_case.family(case_id)
    assert case_obj
    # GIVEN that the case have linked samples
    link_objects = [link_obj for link_obj in case_obj.links]
    assert link_objects

    # WHEN checking is spring decompression if needed
    res = prepare_fastq_api.check_fastq_links(case_id)

    # THEN assert that spring decompression is needed since there are no fastq files
    assert res is True
