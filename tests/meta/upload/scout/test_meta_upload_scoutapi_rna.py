"""Tests for RNA part of the scout upload API"""
import logging
from typing import Optional, Generator
import pytest
from _pytest.logging import LogCaptureFixture

from cgmodels.cg.constants import Pipeline

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import DataDelivery
from cg.meta.upload.scout.uploadscoutapi import UploadScoutAPI
from cg.store import Store, models
from tests.store_helpers import StoreHelpers


def test_upload_rna_junctions_to_scout(
    caplog: Generator[LogCaptureFixture, None, None],
    mip_rna_analysis_hk_api: HousekeeperAPI,
    rna_case_id: str,
    rna_store: Store,
    upload_scout_api: UploadScoutAPI,
):
    """Test that A RNA case's gene fusion report and junction splice files for all samples can be loaded via a cg CLI
    command into an already existing DNA case"""

    # GIVEN an existing RNA case with related sample
    # GIVEN an existing DNA case with related sample
    # GIVEN a sample in the RNA case is connected to a sample in the DNA case via subject_id (i.e. same subject_id)
    upload_scout_api.status_db = rna_store

    # GIVEN the connected RNA sample has a junction bed in Housekeeper
    # GIVEN the connected RNA sample has a bigWig in Housekeeper

    # WHEN running the method to upload RNA files to Scout
    caplog.set_level(logging.INFO)
    upload_scout_api.upload_rna_junctions_to_scout(case_id=rna_case_id, dry_run=True)

    # THEN the 2 files should have been uploaded to the connected sample on the dna case in scout
    assert "Splice junctions bed uploaded successfully to Scout" in caplog.text
    assert "Rna coverage bigwig uploaded successfully to Scout" in caplog.text


def test_upload_splice_junctions_bed_to_scout(
    caplog: Generator[LogCaptureFixture, None, None],
    dna_sample_id: str,
    mip_rna_analysis_hk_api: HousekeeperAPI,
    rna_case_id: str,
    rna_sample_id: str,
    rna_store: Store,
    upload_scout_api: UploadScoutAPI,
):
    """Test that A RNA case's junction splice files for all samples can be loaded via a cg CLI
    command into an already existing DNA case"""

    # GIVEN an existing RNA case with related sample
    # GIVEN an existing DNA case with related sample
    # GIVEN a sample in the RNA case is connected to a sample in the DNA case via subject_id (i.e. same subject_id)
    upload_scout_api.status_db = rna_store

    # GIVEN the connected RNA sample has a junction bed in Housekeeper

    # WHEN running the method to upload RNA files to Scout
    caplog.set_level(logging.INFO)
    upload_scout_api.upload_splice_junctions_bed_to_scout(case_id=rna_case_id, dry_run=True)

    # THEN the splice junctions file should have been uploaded to the connected sample on the dna case in scout
    assert "Splice junctions bed uploaded successfully to Scout" in caplog.text

    # THEN the customers samples name should have been mentioned in the logging (and used in the upload)
    dna_customer_sample_name: str = rna_store.sample(internal_id=dna_sample_id).name
    assert dna_customer_sample_name in caplog.text

    # THEN the customers dna samples name should NOT have been mentioned in the logging
    rna_customer_sample_name: str = rna_store.sample(internal_id=rna_sample_id).name
    assert rna_customer_sample_name not in caplog.text


def test_upload_rna_coverage_bigwig_to_scout(
    caplog: Generator[LogCaptureFixture, None, None],
    dna_sample_id: str,
    mip_rna_analysis_hk_api: HousekeeperAPI,
    rna_case_id: str,
    rna_sample_id: str,
    rna_store: Store,
    upload_scout_api: UploadScoutAPI,
):
    """Test that A RNA case's bigWig file for all samples can be loaded via a cg CLI
    command into an already existing DNA case"""

    # GIVEN an existing RNA case with related sample
    # GIVEN an existing DNA case with related sample
    # GIVEN a sample in the RNA case is connected to a sample in the DNA case via subject_id (i.e. same subject_id)
    upload_scout_api.status_db = rna_store

    # GIVEN the connected RNA sample has a bigWig in Housekeeper

    # WHEN running the method to upload RNA files to Scout
    caplog.set_level(logging.INFO)
    upload_scout_api.upload_rna_coverage_bigwig_to_scout(case_id=rna_case_id, dry_run=True)

    # THEN the bigWig file should have been uploaded to the connected sample on the dna case in scout
    assert "Rna coverage bigwig uploaded successfully to Scout" in caplog.text

    # THEN the customers dna samples name should have been mentioned in the logging (and used in the upload)
    dna_customer_sample_name: str = rna_store.sample(internal_id=dna_sample_id).name
    assert dna_customer_sample_name in caplog.text

    # THEN the customers dna samples name should NOT have been mentioned in the logging
    rna_customer_sample_name: str = rna_store.sample(internal_id=rna_sample_id).name
    assert rna_customer_sample_name not in caplog.text


def test_upload_clinical_rna_fusion_report_to_scout(
    caplog: Generator[LogCaptureFixture, None, None],
    dna_case_id: str,
    dna_sample_id: str,
    mip_rna_analysis_hk_api: HousekeeperAPI,
    rna_case_id: str,
    rna_sample_id: str,
    rna_store: Store,
    upload_scout_api: UploadScoutAPI,
):
    """Test that A RNA case's clinical fusion report and junction splice files for all samples can be loaded via a cg CLI
    command into an already existing DNA case"""

    # GIVEN an existing RNA case with related sample
    # GIVEN an existing DNA case with related sample
    # GIVEN a sample in the RNA case is connected to a sample in the DNA case via subject_id (i.e. same subject_id)
    upload_scout_api.status_db = rna_store

    # GIVEN the connected RNA case has a clinical fusion report in Housekeeper

    # WHEN running the method to upload RNA files to Scout
    caplog.set_level(logging.INFO)
    upload_scout_api.upload_fusion_report_to_scout(case_id=rna_case_id, dry_run=True)

    # THEN the fusion report file should have been uploaded to the connected sample on the dna case in scout
    assert "Clinical fusion report uploaded successfully to Scout" in caplog.text

    # THEN the dna case id should have been mentioned in the logging (and used in the upload)
    assert dna_case_id in caplog.text

    # THEN the customers dna samples name should NOT have been mentioned in the logging
    dna_customer_sample_name: str = rna_store.sample(internal_id=dna_sample_id).name
    assert dna_customer_sample_name not in caplog.text

    # THEN the customers rna samples name should NOT have been mentioned in the logging
    rna_customer_sample_name: str = rna_store.sample(internal_id=rna_sample_id).name
    assert rna_customer_sample_name not in caplog.text


def test_upload_research_rna_fusion_report_to_scout(
    caplog: Generator[LogCaptureFixture, None, None],
    dna_case_id: str,
    dna_sample_id: str,
    mip_rna_analysis_hk_api: HousekeeperAPI,
    rna_case_id: str,
    rna_sample_id: str,
    rna_store: Store,
    upload_scout_api: UploadScoutAPI,
):
    """Test that A RNA case's gene fusion report and junction splice files for all samples can be loaded via a cg CLI
    command into an already existing DNA case"""

    # GIVEN an existing RNA case with related sample
    # GIVEN an existing DNA case with related sample
    # GIVEN a sample in the RNA case is connected to a sample in the DNA case via subject_id (i.e. same subject_id)
    upload_scout_api.status_db = rna_store

    # GIVEN the connected RNA case has a research fusion report in Housekeeper

    # WHEN running the method to upload RNA files to Scout
    caplog.set_level(logging.INFO)
    upload_scout_api.upload_fusion_report_to_scout(case_id=rna_case_id, dry_run=True, research=True)

    # THEN the fusion report file should have been uploaded to the connected sample on the dna case in scout
    assert "Research fusion report uploaded successfully to Scout" in caplog.text

    # THEN the dna case id should have been mentioned in the logging (and used in the upload)
    assert dna_case_id in caplog.text

    # THEN the customers dna samples name should NOT have been mentioned in the logging
    dna_customer_sample_name: str = rna_store.sample(internal_id=dna_sample_id).name
    assert dna_customer_sample_name not in caplog.text

    # THEN the customers rna samples name should NOT have been mentioned in the logging
    rna_customer_sample_name: str = rna_store.sample(internal_id=rna_sample_id).name
    assert rna_customer_sample_name not in caplog.text


def test_upload_rna_research_fusion_report_to_scout_no_subject_id(
    caplog: Generator[LogCaptureFixture, None, None],
    mip_rna_analysis_hk_api: HousekeeperAPI,
    rna_case_id: str,
    rna_sample_id: str,
    rna_store: Store,
    upload_scout_api: UploadScoutAPI,
):
    """Test that A RNA case's gene fusion report and junction splic"""

    # GIVEN a sample in the RNA case is NOT connected to a sample in the DNA case via subject_id (i.e. same subject_id)
    upload_scout_api.status_db = rna_store
    rna_sample: models.Sample = rna_store.sample(internal_id=rna_sample_id)
    rna_sample.subject_id = ""
    rna_store.commit()

    # GIVEN the connected RNA case has a research fusion report in Housekeeper

    # WHEN running the method to upload RNA files to Scout
    caplog.set_level(logging.INFO)
    upload_scout_api.upload_fusion_report_to_scout(case_id=rna_case_id, dry_run=True, research=True)

    # THEN we should not get a message about uploading
    assert "Uploading fusion report to scout for case" not in caplog.text


def test_upload_rna_coverage_bigwig_to_scout_no_subject_id(
    caplog: Generator[LogCaptureFixture, None, None],
    rna_sample_id: str,
    mip_rna_analysis_hk_api: HousekeeperAPI,
    rna_case_id: str,
    rna_store: Store,
    upload_scout_api: UploadScoutAPI,
):
    """Test that A RNA case's gene fusion report and junction splice files for all samples can be loaded via a cg CLI
    command into an already existing DNA case"""

    # GIVEN a sample in the RNA case is NOT connected to a sample in the DNA case via subject_id (i.e. same subject_id)
    upload_scout_api.status_db = rna_store
    rna_sample: models.Sample = rna_store.sample(internal_id=rna_sample_id)
    rna_sample.subject_id = ""
    rna_store.commit()

    # GIVEN the connected RNA sample has a bigWig in Housekeeper

    # WHEN running the method to upload RNA files to Scout
    caplog.set_level(logging.INFO)
    upload_scout_api.upload_rna_coverage_bigwig_to_scout(case_id=rna_case_id, dry_run=True)

    # THEN we should not get a message about uploading
    assert "Uploading rna coverage bigwig file to " not in caplog.text


def test_upload_splice_junctions_bed_to_scout_no_subject_id(
    caplog: Generator[LogCaptureFixture, None, None],
    rna_sample_id: str,
    mip_rna_analysis_hk_api: HousekeeperAPI,
    rna_case_id: str,
    rna_store: Store,
    upload_scout_api: UploadScoutAPI,
):
    """Test that A RNA case's junction splice files for all samples can be loaded via a cg CLI
    command into an already existing DNA case"""

    # GIVEN a sample in the RNA case is NOT connected to a sample in the DNA case via subject_id (i.e. same subject_id)
    upload_scout_api.status_db = rna_store
    rna_sample: models.Sample = rna_store.sample(internal_id=rna_sample_id)
    rna_sample.subject_id = ""
    rna_store.commit()

    # GIVEN the connected RNA sample has a junction bed in Housekeeper

    # WHEN running the method to upload RNA files to Scout
    caplog.set_level(logging.INFO)
    upload_scout_api.upload_splice_junctions_bed_to_scout(case_id=rna_case_id, dry_run=True)

    # THEN we should not get a message about uploading
    assert "Uploading splice junctions bed file for " not in caplog.text
