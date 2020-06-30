"""Tests for cleaning bam functions"""

import logging


def test_remove_bams(compress_api, bam_file, bai_file, bam_flag_file, caplog):
    """ Test remove_bam method"""
    caplog.set_level(logging.DEBUG)
    # GIVEN existing bam, bai and flag files
    assert bam_file.exists()
    assert bai_file.exists()
    assert bam_flag_file.exists()
    # GIVEN a crunchy api where bam compression is done
    crunchy_api = compress_api.crunchy_api
    crunchy_api.set_bam_compression_done_all()

    # WHEN calling remove_bams
    compress_api.remove_bam(bam_path=bam_file, bai_path=bai_file)

    # THEN the assert that the bam-files and flag-file should not exist
    assert not bam_file.exists()
    assert not bai_file.exists()
    assert not bam_file.exists()
    assert f"Will remove {bam_file}, {bai_file}, and {bam_flag_file}" in caplog.text
    assert f"BAM file {bam_file} removed" in caplog.text


def test_remove_bams_dry_run(compress_api, bam_file, bai_file, bam_flag_file, caplog):
    """ Test remove_bam method with dry run flag"""
    caplog.set_level(logging.DEBUG)
    # GIVEN existing bam, bai and flag files
    assert bam_file.exists()
    assert bai_file.exists()
    assert bam_flag_file.exists()
    # GIVEN a compress api with dry run enabled
    compress_api.dry_run = True
    # GIVEN a crunchy api where bam compression is done
    crunchy_api = compress_api.crunchy_api
    crunchy_api.set_bam_compression_done_all()

    # WHEN calling remove_bams with dry run flag
    compress_api.remove_bam(bam_path=bam_file, bai_path=bai_file)

    # THEN the assert that the bam-files and flag-file still exists
    assert bam_file.exists()
    assert bai_file.exists()
    assert bam_file.exists()

    assert f"Will remove {bam_file}, {bai_file}, and {bam_flag_file}" in caplog.text
    assert f"BAM file {bam_file} removed" not in caplog.text


def test_update_scout(compress_api, case_id, sample, bam_path, caplog):
    """ Test to update the bam paths in scout"""
    # GIVEN that the compression is done
    caplog.set_level(logging.DEBUG)
    compress_api.crunchy_api.set_bam_compression_done_all()
    assert compress_api.crunchy_api.is_cram_compression_done(bam_path=None) is True
    scout_api = compress_api.scout_api
    assert scout_api.nr_alignment_updates() == 0
    # GIVEN a cram path
    cram_path = compress_api.crunchy_api.get_cram_path_from_bam(bam_path=bam_path)

    # WHEN updating the bam paths in scout
    compress_api.update_scout(case_id=case_id, sample_id=sample, bam_path=bam_path)
    # THEN update_alignment_file should have been called
    assert scout_api.nr_alignment_updates() == 1
    # THEN assert that the correct information is communicated
    assert f"Updating {bam_path} -> {cram_path} in Scout" in caplog.text
    assert f"Updating alignment-file for {sample} in scout..." in caplog.text


def test_update_scout_dry_run(compress_api, case_id, sample, bam_path, caplog):
    """ Test to update the bam paths in scout"""
    # GIVEN that the compression is done and dry run enabled
    caplog.set_level(logging.DEBUG)
    compress_api.crunchy_api.set_bam_compression_done_all()
    compress_api.dry_run = True
    assert compress_api.crunchy_api.is_cram_compression_done(bam_path=None) is True
    scout_api = compress_api.scout_api
    assert scout_api.nr_alignment_updates() == 0
    # GIVEN a cram path
    cram_path = compress_api.crunchy_api.get_cram_path_from_bam(bam_path=bam_path)

    # WHEN updating the bam paths in scout
    compress_api.update_scout(case_id=case_id, sample_id=sample, bam_path=bam_path)
    # THEN update_alignment_file should not have been called
    assert scout_api.nr_alignment_updates() == 0
    # THEN assert that the correct information is communicated
    assert f"Updating {bam_path} -> {cram_path} in Scout" in caplog.text
    assert f"Updating alignment-file for {sample} in scout..." not in caplog.text


def test_update_hk_bam(
    compress_api, real_housekeeper_api, compress_hk_bam_single_bundle, sample, helpers
):
    """ Test to update the bam file in housekeeper

    The function update_hk_bam will remove bam files and replace them with cram files
    In this test we will make sure that the bam and bai files are removed
    """
    # GIVEN a real housekeeper api populated with some bam and bai files
    hk_bundle = compress_hk_bam_single_bundle
    helpers.ensure_hk_bundle(real_housekeeper_api, hk_bundle)
    compress_api.hk_api = real_housekeeper_api
    bundle_name = hk_bundle["name"]
    # GIVEN a version object
    version_obj = real_housekeeper_api.last_version(bundle_name)
    assert version_obj
    # GIVEN that there is one bam file
    bam_files = list(real_housekeeper_api.files(tags=["bam"]))
    assert len(bam_files) == 1
    hk_bam_file = bam_files[0]
    # GIVEN that there is one bam index file
    bai_files = list(real_housekeeper_api.files(tags=["bai"]))
    assert len(bai_files) == 1
    hk_bai_file = bai_files[0]

    # WHEN updating housekeeper with compress api after compression is done
    compress_api.update_bam_hk(
        sample_id=sample, hk_bam_file=hk_bam_file, hk_bai_file=hk_bai_file, hk_version=version_obj
    )

    # THEN assert that the bam and bai files are removed from hk
    assert len(list(real_housekeeper_api.files(tags=["bam"]))) == 0
    assert len(list(real_housekeeper_api.files(tags=["bai"]))) == 0


def test_update_hk_cram(
    compress_api,
    real_housekeeper_api,
    compress_hk_bam_single_bundle,
    sample,
    cram_file,
    crai_file,
    helpers,
):
    """ Test to update the bam file in housekeeper

    The function update_hk_bam will remove bam files and replace them with cram files
    In this test we will make sure that the bam and bai files are removed
    """
    # GIVEN a real housekeeper api populated with some bam and bai files
    hk_bundle = compress_hk_bam_single_bundle
    helpers.ensure_hk_bundle(real_housekeeper_api, hk_bundle)
    compress_api.hk_api = real_housekeeper_api
    bundle_name = hk_bundle["name"]
    hk_bam_file = list(real_housekeeper_api.files(tags=["bam"]))[0]
    hk_bai_file = list(real_housekeeper_api.files(tags=["bai"]))[0]
    # GIVEN a version object
    version_obj = real_housekeeper_api.last_version(bundle_name)
    assert version_obj
    # GIVEN that there are no cram files
    cram_files = list(real_housekeeper_api.files(tags=["cram"]))
    assert len(cram_files) == 0
    # GIVEN that there are no cram index files
    crai_files = list(real_housekeeper_api.files(tags=["cram-index"]))
    assert len(crai_files) == 0

    # WHEN updating housekeeper with compress api after compression is done
    compress_api.update_bam_hk(
        sample_id=sample, hk_bam_file=hk_bam_file, hk_bai_file=hk_bai_file, hk_version=version_obj
    )

    # THEN assert that the cram and crai files are added to hk
    assert len(list(real_housekeeper_api.files(tags=["cram"]))) == 1
    assert len(list(real_housekeeper_api.files(tags=["cram-index"]))) == 1


def test_clean_bam(
    populated_compress_api,
    real_housekeeper_api,
    compress_hk_bam_single_bundle,
    cram_file,
    crai_file,
    bam_flag_file,
    helpers,
    caplog,
):
    """ Test to update the bam file in housekeeper

    The function update_hk_bam will remove bam files and replace them with cram files
    In this test we will make sure that the bam and bai files are removed
    """
    caplog.set_level(logging.DEBUG)
    compress_api = populated_compress_api
    # GIVEN a real housekeeper api populated with some bam and bai files
    hk_bundle = compress_hk_bam_single_bundle
    case_id = hk_bundle["name"]
    helpers.ensure_hk_bundle(real_housekeeper_api, hk_bundle)
    compress_api.hk_api = real_housekeeper_api
    real_housekeeper_api.get_files(case_id, tags=["bam", "bai", "bam-index"])
    # GIVEN that the cram compression is done
    compress_api.crunchy_api.set_bam_compression_done_all()
    assert compress_api.crunchy_api.is_cram_compression_done(bam_path=None) is True

    # WHEN updating housekeeper with compress api after compression is done
    compress_api.clean_bams(case_id=case_id)
    # THEN assert that the bam files are removed from hk
    assert len(list(real_housekeeper_api.files(tags=["bam"]))) == 0
    assert len(list(real_housekeeper_api.files(tags=["bai"]))) == 0
