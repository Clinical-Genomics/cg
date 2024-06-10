"""Tests for RNA part of the scout upload API"""

import logging
from typing import Generator, Set

import pytest
from _pytest.logging import LogCaptureFixture
from housekeeper.store.models import File

import cg.store as Store
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import Workflow
from cg.constants.scout import ScoutCustomCaseReportTags
from cg.constants.sequencing import SequencingMethod
from cg.exc import CgDataError
from cg.meta.upload.scout.uploadscoutapi import RNADNACollection, UploadScoutAPI
from cg.store.models import Case, Sample
from tests.mocks.hk_mock import MockHousekeeperAPI
from tests.store_helpers import StoreHelpers


def set_is_tumour_on_case(store: Store, case_id: str, is_tumour: bool):
    for link in store.get_case_by_internal_id(internal_id=case_id).links:
        link.sample.is_tumour = is_tumour


def get_subject_id_from_case(store: Store, case_id: str) -> str:
    for link in store.get_case_by_internal_id(internal_id=case_id).links:
        return link.sample.subject_id


def ensure_two_dna_tumour_matches(
    dna_case_id: str,
    another_sample_id: str,
    helpers: StoreHelpers,
    rna_case_id: str,
    rna_store: Store,
) -> None:
    """Ensures that we have one RNA case that has two matching DNA cases via subject id and tumour state."""
    set_is_tumour_on_case(store=rna_store, case_id=rna_case_id, is_tumour=True)
    subject_id: str = get_subject_id_from_case(store=rna_store, case_id=rna_case_id)
    set_is_tumour_on_case(store=rna_store, case_id=dna_case_id, is_tumour=True)
    dna_extra_case = helpers.ensure_case(
        store=rna_store, customer=rna_store.get_case_by_internal_id(dna_case_id).customer
    )
    another_sample_id = helpers.add_sample(
        store=rna_store,
        application_tag=SequencingMethod.WGS,
        application_type=SequencingMethod.WGS,
        is_tumour=True,
        name=another_sample_id,
        subject_id=subject_id,
    )
    helpers.add_relationship(store=rna_store, sample=another_sample_id, case=dna_extra_case)
    rna_store.session.commit()


def ensure_extra_rna_case_match(
    another_rna_sample_id: str,
    helpers: StoreHelpers,
    rna_case_id: str,
    rna_store: Store,
) -> None:
    """Ensures that we have an extra RNA case that matches by subject_id the existing RNA case and DNA cases."""
    rna_extra_case = helpers.ensure_case(
        store=rna_store,
        data_analysis=Workflow.MIP_RNA,
        customer=rna_store.get_case_by_internal_id(rna_case_id).customer,
    )
    subject_id: str = get_subject_id_from_case(store=rna_store, case_id=rna_case_id)
    another_rna_sample_id = helpers.add_sample(
        store=rna_store,
        application_type=SequencingMethod.WTS,
        is_tumour=False,
        internal_id=another_rna_sample_id,
        subject_id=subject_id,
    )
    helpers.add_relationship(store=rna_store, sample=another_rna_sample_id, case=rna_extra_case)


def test_upload_rna_alignment_file_to_scout(
    caplog: LogCaptureFixture,
    dna_sample_daughter_id: str,
    dna_sample_father_id: str,
    dna_sample_mother_id: str,
    dna_sample_son_id: str,
    mip_rna_analysis_hk_api: HousekeeperAPI,
    rna_case_id: str,
    rna_store: Store,
    upload_scout_api: UploadScoutAPI,
):
    """Test that a RNA case's alignment file can be loaded via a CG CLI command into an already existing DNA case."""
    caplog.set_level(logging.INFO)

    # GIVEN RNA and DNA cases connected via subject ID
    upload_scout_api.status_db = rna_store

    # GIVEN an RNA case with an alignment file stored in HK

    # WHEN running the method to upload RNA files to Scout
    upload_scout_api.upload_rna_alignment_file(case_id=rna_case_id, dry_run=True)

    # THEN the RNA alignment file should have been uploaded to the linked DNA cases in Scout
    assert "Upload RNA alignment CRAM file finished!" in caplog.text
    for dna_case in [
        dna_sample_mother_id,
        dna_sample_father_id,
        dna_sample_daughter_id,
        dna_sample_son_id,
    ]:
        assert dna_case in caplog.text


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
    assert "Upload splice junctions bed file finished!" in caplog.text
    assert "Upload RNA coverage bigwig file finished!" in caplog.text


def test_upload_splice_junctions_bed_to_scout(
    caplog: Generator[LogCaptureFixture, None, None],
    dna_sample_son_id: str,
    mip_rna_analysis_hk_api: HousekeeperAPI,
    rna_case_id: str,
    rna_sample_son_id: str,
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
    assert "Upload splice junctions bed file finished!" in caplog.text

    # THEN the customers dna samples name should have been mentioned in the logging (and used in the upload)
    dna_customer_sample_name: str = rna_store.get_sample_by_internal_id(
        internal_id=dna_sample_son_id
    ).name
    assert dna_customer_sample_name in caplog.text


def test_upload_rna_coverage_bigwig_to_scout(
    caplog: Generator[LogCaptureFixture, None, None],
    dna_sample_son_id: str,
    mip_rna_analysis_hk_api: HousekeeperAPI,
    rna_case_id: str,
    rna_sample_son_id: str,
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
    assert "Upload RNA coverage bigwig file finished!" in caplog.text

    # THEN the customers dna samples name should have been mentioned in the logging (and used in the upload)
    dna_customer_sample_name: str = rna_store.get_sample_by_internal_id(
        internal_id=dna_sample_son_id
    ).name
    assert dna_customer_sample_name in caplog.text


def test_upload_clinical_rna_fusion_report_to_scout(
    caplog: Generator[LogCaptureFixture, None, None],
    dna_case_id: str,
    dna_sample_son_id: str,
    mip_rna_analysis_hk_api: HousekeeperAPI,
    rna_case_id: str,
    rna_sample_son_id: str,
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
    assert "Upload Clinical fusion report finished!" in caplog.text

    # THEN the dna case id should have been mentioned in the logging (and used in the upload)
    assert dna_case_id in caplog.text

    # THEN the customers dna samples name should NOT have been mentioned in the logging
    dna_customer_sample_name: str = rna_store.get_sample_by_internal_id(
        internal_id=dna_sample_son_id
    ).name
    assert dna_customer_sample_name not in caplog.text


def test_upload_research_rna_fusion_report_to_scout(
    caplog: Generator[LogCaptureFixture, None, None],
    dna_case_id: str,
    dna_sample_son_id: str,
    mip_rna_analysis_hk_api: HousekeeperAPI,
    rna_case_id: str,
    rna_sample_son_id: str,
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
    assert "Upload Research fusion report finished!" in caplog.text

    # THEN the dna case id should have been mentioned in the logging (and used in the upload)
    assert dna_case_id in caplog.text

    # THEN the customers dna samples name should NOT have been mentioned in the logging
    dna_customer_sample_name: str = rna_store.get_sample_by_internal_id(
        internal_id=dna_sample_son_id
    ).name
    assert dna_customer_sample_name not in caplog.text


def test_upload_rna_fusion_report_to_scout_no_subject_id(
    caplog: Generator[LogCaptureFixture, None, None],
    dna_case_id: str,
    mip_rna_analysis_hk_api: HousekeeperAPI,
    rna_case_id: str,
    rna_store: Store,
    upload_scout_api: UploadScoutAPI,
):
    """Test that A RNA case's gene fusion report"""

    # GIVEN a sample in the RNA case is NOT connected to a sample in the DNA case via subject_id (i.e. same subject_id)
    for link in rna_store.get_case_by_internal_id(rna_case_id).links:
        link.sample.subject_id = ""
    for link in rna_store.get_case_by_internal_id(dna_case_id).links:
        link.sample.subject_id = ""
    rna_store.session.commit()
    upload_scout_api.status_db = rna_store

    # GIVEN the connected RNA case has a research fusion report in Housekeeper

    # WHEN running the method to upload RNA files to Scout
    caplog.set_level(logging.INFO)
    # THEN an exception should be raised on unconnected data
    with pytest.raises(CgDataError):
        upload_scout_api.upload_fusion_report_to_scout(case_id=rna_case_id, dry_run=True)


def test_upload_rna_coverage_bigwig_to_scout_no_subject_id(
    caplog: Generator[LogCaptureFixture, None, None],
    dna_case_id: str,
    mip_rna_analysis_hk_api: HousekeeperAPI,
    rna_case_id: str,
    rna_store: Store,
    upload_scout_api: UploadScoutAPI,
):
    """Test that A RNA case's gene fusion report and junction splice files for all samples can be loaded via a cg CLI
    command into an already existing DNA case"""

    # GIVEN a sample in the RNA case is NOT connected to a sample in the DNA case via subject_id (i.e. same subject_id)
    for link in rna_store.get_case_by_internal_id(rna_case_id).links:
        link.sample.subject_id = ""
    for link in rna_store.get_case_by_internal_id(dna_case_id).links:
        link.sample.subject_id = ""
    rna_store.session.commit()
    upload_scout_api.status_db = rna_store

    # GIVEN the connected RNA sample has a bigWig in Housekeeper

    # WHEN running the method to upload RNA files to Scout
    caplog.set_level(logging.INFO)
    # THEN an exception should be raised on unconnected data
    with pytest.raises(CgDataError):
        upload_scout_api.upload_rna_coverage_bigwig_to_scout(case_id=rna_case_id, dry_run=True)


def test_upload_splice_junctions_bed_to_scout_no_subject_id(
    caplog: Generator[LogCaptureFixture, None, None],
    dna_case_id: str,
    mip_rna_analysis_hk_api: HousekeeperAPI,
    rna_case_id: str,
    rna_store: Store,
    upload_scout_api: UploadScoutAPI,
):
    """Test that A RNA case's junction splice files for all samples can be loaded via a cg CLI
    command into an already existing DNA case"""

    # GIVEN a sample in the RNA case is NOT connected to a sample in the DNA case via subject_id (i.e. same subject_id)
    for link in rna_store.get_case_by_internal_id(rna_case_id).links:
        link.sample.subject_id = ""
    for link in rna_store.get_case_by_internal_id(dna_case_id).links:
        link.sample.subject_id = ""
    rna_store.session.commit()
    upload_scout_api.status_db = rna_store

    # GIVEN the connected RNA sample has a junction bed in Housekeeper

    # WHEN running the method to upload RNA files to Scout
    caplog.set_level(logging.INFO)
    # THEN an exception should be raised on unconnected data
    with pytest.raises(CgDataError):
        upload_scout_api.upload_splice_junctions_bed_to_scout(case_id=rna_case_id, dry_run=True)


def test_upload_rna_fusion_report_to_scout_tumour_non_matching(
    caplog: Generator[LogCaptureFixture, None, None],
    dna_case_id: str,
    mip_rna_analysis_hk_api: HousekeeperAPI,
    rna_case_id: str,
    rna_store: Store,
    upload_scout_api: UploadScoutAPI,
):
    """Test that an RNA case's gene fusion report is not uploaded if the is_tumour is not matching"""

    # GIVEN a sample in the RNA case is NOT connected to a sample in the DNA case via is_tumour (i.e. different is_tumour)
    set_is_tumour_on_case(store=rna_store, case_id=rna_case_id, is_tumour=True)
    set_is_tumour_on_case(store=rna_store, case_id=dna_case_id, is_tumour=False)
    rna_store.session.commit()
    upload_scout_api.status_db = rna_store

    # GIVEN the connected RNA case has a research fusion report in Housekeeper

    # WHEN running the method to upload RNA files to Scout
    caplog.set_level(logging.INFO)

    # THEN an exception should be raised on unconnected data
    with pytest.raises(CgDataError):
        upload_scout_api.upload_fusion_report_to_scout(case_id=rna_case_id, dry_run=True)


def test_upload_rna_coverage_bigwig_to_scout_tumour_non_matching(
    caplog: Generator[LogCaptureFixture, None, None],
    dna_case_id: str,
    mip_rna_analysis_hk_api: HousekeeperAPI,
    rna_case_id: str,
    rna_store: Store,
    upload_scout_api: UploadScoutAPI,
):
    """Test that A RNA case's gene fusion report and junction splice files for all samples is not uploaded if the is_tumour is not matching"""

    # GIVEN a sample in the RNA case is NOT connected to a sample in the DNA case via is_tumour (i.e. different is_tumour)
    set_is_tumour_on_case(store=rna_store, case_id=rna_case_id, is_tumour=True)
    set_is_tumour_on_case(store=rna_store, case_id=dna_case_id, is_tumour=False)
    rna_store.session.commit()
    upload_scout_api.status_db = rna_store

    # GIVEN the connected RNA sample has a bigWig in Housekeeper

    # WHEN running the method to upload RNA files to Scout
    caplog.set_level(logging.INFO)

    # THEN an exception should be raised on unconnected data
    with pytest.raises(CgDataError):
        upload_scout_api.upload_rna_coverage_bigwig_to_scout(case_id=rna_case_id, dry_run=True)


def test_upload_splice_junctions_bed_to_scout_tumour_non_matching(
    caplog: Generator[LogCaptureFixture, None, None],
    dna_case_id: str,
    mip_rna_analysis_hk_api: HousekeeperAPI,
    rna_case_id: str,
    rna_store: Store,
    upload_scout_api: UploadScoutAPI,
):
    """Test that A RNA case's junction splice files for all samples is not uploaded if the is_tumour is not matching"""

    # GIVEN a sample in the RNA case is NOT connected to a sample in the DNA case via is_tumour (i.e. different is_tumour)
    set_is_tumour_on_case(store=rna_store, case_id=rna_case_id, is_tumour=True)
    set_is_tumour_on_case(store=rna_store, case_id=dna_case_id, is_tumour=False)
    rna_store.session.commit()
    upload_scout_api.status_db = rna_store

    # GIVEN the connected RNA sample has a junction bed in Housekeeper

    # WHEN running the method to upload RNA files to Scout
    caplog.set_level(logging.INFO)

    # THEN an exception should be raised on unconnected data
    with pytest.raises(CgDataError):
        upload_scout_api.upload_splice_junctions_bed_to_scout(case_id=rna_case_id, dry_run=True)


def test_upload_rna_fusion_report_to_scout_tumour_multiple_matches(
    caplog: Generator[LogCaptureFixture, None, None],
    dna_case_id: str,
    another_sample_id: str,
    helpers: StoreHelpers,
    mip_rna_analysis_hk_api: HousekeeperAPI,
    rna_case_id: str,
    rna_store: Store,
    upload_scout_api: UploadScoutAPI,
):
    """Test that an RNA case's gene fusion report is not uploaded if the is_tumour has too many DNA-matches"""

    # GIVEN a sample in the RNA case is connected to a sample in the DNA case via is_tumour (i.e. same is_tumour)
    ensure_two_dna_tumour_matches(dna_case_id, another_sample_id, helpers, rna_case_id, rna_store)
    upload_scout_api.status_db = rna_store

    # GIVEN the connected RNA case has a research fusion report in Housekeeper

    # WHEN running the method to upload RNA files to Scout
    caplog.set_level(logging.INFO)

    # THEN an exception should be raised on unconnected data
    with pytest.raises(CgDataError):
        upload_scout_api.upload_fusion_report_to_scout(case_id=rna_case_id, dry_run=True)


def test_upload_rna_coverage_bigwig_to_scout_tumour_multiple_matches(
    caplog: Generator[LogCaptureFixture, None, None],
    dna_case_id: str,
    another_sample_id: str,
    helpers: StoreHelpers,
    mip_rna_analysis_hk_api: HousekeeperAPI,
    rna_case_id: str,
    rna_store: Store,
    upload_scout_api: UploadScoutAPI,
):
    """Test that A RNA case's gene fusion report and junction splice files for all samples is not uploaded if the RNA-sample has too many DNA-matches"""

    # GIVEN a sample in the RNA case is connected to a sample in the DNA case via is_tumour (i.e. same is_tumour)
    ensure_two_dna_tumour_matches(dna_case_id, another_sample_id, helpers, rna_case_id, rna_store)
    upload_scout_api.status_db = rna_store

    # GIVEN the connected RNA sample has a bigWig in Housekeeper

    # WHEN running the method to upload RNA files to Scout
    caplog.set_level(logging.INFO)

    # THEN an exception should be raised on unconnected data
    with pytest.raises(CgDataError):
        upload_scout_api.upload_rna_coverage_bigwig_to_scout(case_id=rna_case_id, dry_run=True)


def test_upload_splice_junctions_bed_to_scout_tumour_multiple_matches(
    caplog: Generator[LogCaptureFixture, None, None],
    dna_case_id: str,
    another_sample_id: str,
    helpers: StoreHelpers,
    mip_rna_analysis_hk_api: HousekeeperAPI,
    rna_case_id: str,
    rna_store: Store,
    upload_scout_api: UploadScoutAPI,
):
    """Test that A RNA case's junction splice files for all samples is not uploaded if the RNA-sample has too many DNA-matches"""

    # GIVEN a sample in the RNA case is connected to a sample in the DNA case via is_tumour (i.e. same is_tumour)
    ensure_two_dna_tumour_matches(dna_case_id, another_sample_id, helpers, rna_case_id, rna_store)
    upload_scout_api.status_db = rna_store

    # GIVEN the connected RNA sample has a junction bed in Housekeeper

    # WHEN running the method to upload RNA files to Scout
    caplog.set_level(logging.INFO)

    # THEN an exception should be raised on unconnected data
    with pytest.raises(CgDataError):
        upload_scout_api.upload_splice_junctions_bed_to_scout(case_id=rna_case_id, dry_run=True)


def test_get_application_prep_category(
    another_rna_sample_id: str,
    dna_sample_son_id: str,
    helpers: StoreHelpers,
    rna_case_id: str,
    rna_sample_son_id: str,
    rna_store: Store,
    upload_scout_api: UploadScoutAPI,
):
    """Test that RNA samples are removed when filtering sample list by workflow."""

    # GIVEN an RNA sample that is connected by subject ID to one RNA and one DNA sample in other cases

    ensure_extra_rna_case_match(another_rna_sample_id, helpers, rna_case_id, rna_store)
    upload_scout_api.status_db = rna_store

    dna_sample: Sample = rna_store.get_sample_by_internal_id(dna_sample_son_id)
    another_rna_sample_id: Sample = rna_store.get_sample_by_internal_id(another_rna_sample_id)
    all_son_rna_dna_samples: list[Sample] = [dna_sample, another_rna_sample_id]

    # WHEN running the method to filter a list of Sample objects containing RNA and DNA samples connected by subject_id
    only_son_dna_samples = upload_scout_api._get_application_prep_category(all_son_rna_dna_samples)

    # THEN even though an RNA sample is present in the initial query, the output should not contain any RNA samples
    nr_of_subject_id_samples: int = len(all_son_rna_dna_samples)
    nr_of_subject_id_dna_samples: int = len([only_son_dna_samples])
    assert nr_of_subject_id_samples == 2
    assert nr_of_subject_id_dna_samples == 1


def test_create_rna_dna_collections(
    rna_case_id: str,
    rna_store: Store,
    upload_scout_api: UploadScoutAPI,
):
    """Test that the create_rna_dna_collections returns a list of RNADNACollections."""

    # GIVEN an RNA case with RNA samples that are connected by subject ID to DNA samples in a DNA case
    rna_case: Case = rna_store.get_case_by_internal_id(rna_case_id)

    # WHEN running the method to create a list of RNADNACollections
    # with the relationships between RNA/DNA samples and DNA cases
    rna_dna_collections: list[RNADNACollection] = upload_scout_api.create_rna_dna_collections(
        rna_case
    )

    # THEN the output should be a list of RNADNACollections
    assert all(
        isinstance(rna_dna_collection, RNADNACollection)
        for rna_dna_collection in rna_dna_collections
    )


def test_add_rna_sample(
    rna_case_id: str,
    rna_store: Store,
    upload_scout_api: UploadScoutAPI,
):
    """Test that for a given RNA case the RNA samples are added to the RNADNACollections."""

    # GIVEN an RNA case and the associated RNA samples
    rna_case: Case = rna_store.get_case_by_internal_id(internal_id=rna_case_id)
    rna_sample_list: list[Sample] = (
        rna_store._get_query(table=Sample).filter(Sample.internal_id.contains("rna")).all()
    )

    # WHEN running the method to create a list of RNADNACollections
    # with the relationships between RNA/DNA samples and DNA cases
    rna_dna_collections: list[RNADNACollection] = upload_scout_api.create_rna_dna_collections(
        rna_case
    )

    # THEN the resulting RNADNACollections should contain all RNA samples in the case
    assert rna_sample_list
    for sample in rna_sample_list:
        assert sample.internal_id in [
            rna_dna_collection.rna_sample_internal_id for rna_dna_collection in rna_dna_collections
        ]


def test_link_rna_sample_to_dna_sample(
    dna_sample_son_id: str,
    rna_sample_son_id: str,
    rna_store: Store,
    upload_scout_api: UploadScoutAPI,
):
    """Test for a given RNA sample, the associated DNA sample name matches and is present in rna_dna_case_map."""

    # GIVEN an RNA sample
    rna_sample: Sample = rna_store.get_sample_by_internal_id(rna_sample_son_id)

    # WHEN creating an RNADNACollection for an RNA sample
    rna_dna_collection: RNADNACollection = upload_scout_api.create_rna_dna_collection(rna_sample)

    # THEN the RNADNACollection should contain the RNA sample
    assert rna_sample_son_id == rna_dna_collection.rna_sample_internal_id

    # THEN the RNADNACollection should have its dna_sample_id set to the related dna_sample_id
    assert dna_sample_son_id == rna_dna_collection.dna_sample_name


def test_add_dna_cases_to_dna_sample(
    dna_case_id: str,
    dna_sample_son_id: str,
    rna_sample_son_id: str,
    rna_store: Store,
    upload_scout_api: UploadScoutAPI,
):
    """Test for a given RNA sample, the DNA case name matches to the case name of the DNA sample in the RNADNACollection."""

    # GIVEN an RNA sample, a DNA sample, and a DNA case
    rna_sample: Sample = rna_store.get_sample_by_internal_id(internal_id=rna_sample_son_id)
    dna_case: Case = rna_store.get_case_by_internal_id(internal_id=dna_case_id)

    # WHEN adding creating the RNADNACollection
    rna_dna_collection: RNADNACollection = upload_scout_api.create_rna_dna_collection(rna_sample)

    # THEN the DNA cases should contain the DNA_case name associated with the DNA sample
    assert dna_case.internal_id in rna_dna_collection.dna_case_ids


def test_map_dna_cases_to_dna_sample_incorrect_workflow(
    rna_store: Store,
    upload_scout_api: UploadScoutAPI,
    dna_sample_son_id: str,
    dna_case_id: str,
    rna_sample_son_id: str,
):
    """Test that the DNA case name is not mapped to the DNA sample name in the rna-dna-sample-case map."""

    # GIVEN an RNA sample and a DNA sample

    dna_sample: Sample = rna_store.get_sample_by_internal_id(dna_sample_son_id)
    dna_case: Case = rna_store.get_case_by_internal_id(dna_case_id)
    rna_sample: Sample = rna_store.get_sample_by_internal_id(rna_sample_son_id)

    # GIVEN that the DNA case has a different workflow than the expected workflow
    dna_case.data_analysis = Workflow.FASTQ

    # WHEN mapping the DNA case name to the DNA sample name in the related DNA cases
    related_dna_cases: list[str] = upload_scout_api._dna_cases_related_to_dna_sample(
        dna_sample=dna_sample,
        collaborators=rna_sample.customer.collaborators,
    )

    # THEN the related DNA cases should not contain the DNA case name associated with the DNA sample name
    assert dna_case.internal_id not in related_dna_cases


def test_map_dna_cases_to_dna_sample_incorrect_customer(
    rna_store: Store,
    upload_scout_api: UploadScoutAPI,
    dna_sample_son_id: str,
    dna_case_id: str,
    rna_sample_son_id: str,
):
    """Test that the DNA case name is not mapped to the DNA sample name in the RNADNACollection."""

    # GIVEN an RNA sample, a DNA sample, and a rna-dna case map

    dna_sample: Sample = rna_store.get_sample_by_internal_id(internal_id=dna_sample_son_id)
    dna_case: Case = rna_store.get_case_by_internal_id(internal_id=dna_case_id)
    rna_sample: Sample = rna_store.get_sample_by_internal_id(internal_id=rna_sample_son_id)

    # GIVEN that the DNA case has a different customer than the expected customer
    dna_case.customer_id = 1000

    # WHEN mapping the DNA case name to the DNA sample name in the rna-dna-sample-case map
    dna_cases: list[str] = upload_scout_api._dna_cases_related_to_dna_sample(
        dna_sample=dna_sample,
        collaborators=rna_sample.customer.collaborators,
    )

    # THEN the rna-dna-sample-case map should not contain the DNA case name associated with the DNA sample name
    assert dna_case.internal_id not in dna_cases


def test_get_multiqc_html_report(
    dna_case_id: str,
    rna_store: Store,
    upload_mip_analysis_scout_api: UploadScoutAPI,
    mip_dna_analysis_hk_api: MockHousekeeperAPI,
):
    """Test that the multiqc html report is returned."""

    # GIVEN a DNA case with a multiqc-htlml report
    case: Case = rna_store.get_case_by_internal_id(internal_id=dna_case_id)
    multiqc_file: File = mip_dna_analysis_hk_api.files(
        bundle=dna_case_id, tags=[ScoutCustomCaseReportTags.MULTIQC]
    )[0]

    # WHEN getting the multiqc html report
    report_type, multiqc_report = upload_mip_analysis_scout_api.get_multiqc_html_report(
        case_id=dna_case_id, workflow=case.data_analysis
    )

    # THEN the multiqc html report should be returned and the correct report type
    assert multiqc_report.full_path == multiqc_file.full_path
    assert report_type == ScoutCustomCaseReportTags.MULTIQC


def test_upload_report_to_scout(
    caplog,
    dna_case_id: str,
    upload_mip_analysis_scout_api: UploadScoutAPI,
    mip_dna_analysis_hk_api: MockHousekeeperAPI,
):
    """Test that the uploaded of a report to Scout is possible."""

    caplog.set_level(logging.INFO)

    # GIVEN a DNA case with a multiqc-htlml report
    multiqc_file: File = mip_dna_analysis_hk_api.files(
        bundle=dna_case_id, tags=[ScoutCustomCaseReportTags.MULTIQC]
    )[0]
    assert multiqc_file

    # WHEN uploading a report to Scout
    upload_mip_analysis_scout_api.upload_report_to_scout(
        dry_run=False,
        case_id=dna_case_id,
        report_type=ScoutCustomCaseReportTags.MULTIQC,
        report_file=multiqc_file,
    )

    # THEN the report should be uploaded to Scout
    assert (
        f"Uploading {ScoutCustomCaseReportTags.MULTIQC} report to case {dna_case_id}" in caplog.text
    )


def test_upload_rna_report_to_successful_dna_case_in_scout(
    caplog,
    rna_case_id: str,
    rna_store: Store,
    upload_mip_analysis_scout_api: UploadScoutAPI,
    mip_rna_analysis_hk_api: MockHousekeeperAPI,
):
    """Test that the report is uploaded to Scout."""

    caplog.set_level(logging.INFO)

    # GIVEN an RNA case, and an store with an rna connected to it
    upload_mip_analysis_scout_api.status_db: Store = rna_store

    # GIVEN an RNA case with a multiqc-htlml report
    multiqc_file: File = mip_rna_analysis_hk_api.files(
        bundle=rna_case_id, tags=[ScoutCustomCaseReportTags.MULTIQC]
    )[0]

    # WHEN uploading a report to a completed DNA case in Scout
    upload_mip_analysis_scout_api.upload_rna_report_to_dna_case_in_scout(
        dry_run=False,
        rna_case_id=rna_case_id,
        report_type=ScoutCustomCaseReportTags.MULTIQC,
        report_file=multiqc_file,
    )

    # WHEN finding the related DNA case
    dna_case_ids: Set[str] = upload_mip_analysis_scout_api.get_unique_dna_cases_related_to_rna_case(
        case_id=rna_case_id
    )

    # THEN the api should know that it should find related DNA cases
    assert f"Finding DNA cases related to RNA case {rna_case_id}" in caplog.text

    # THEN the report should be uploaded to Scout
    for case_id in dna_case_ids:
        assert (
            f"Uploading {ScoutCustomCaseReportTags.MULTIQC} report to Scout for case {case_id}"
            in caplog.text
        )


def test_upload_rna_report_to_not_yet_uploaded_dna_case_in_scout(
    caplog,
    rna_case_id: str,
    rna_store: Store,
    upload_mip_analysis_scout_api: UploadScoutAPI,
    mip_rna_analysis_hk_api: MockHousekeeperAPI,
):
    """Test that an error is raised when trying to upload an RNA report to a not yet uploaded DNA case."""

    caplog.set_level(logging.INFO)

    # GIVEN an RNA case, and an store with an RNA connected to it
    upload_mip_analysis_scout_api.status_db: Store = rna_store

    # GIVEN an RNA case with a multiqc-htlml report
    multiqc_file: File = mip_rna_analysis_hk_api.files(
        bundle=rna_case_id, tags=[ScoutCustomCaseReportTags.MULTIQC]
    )[0]

    # WHEN finding the related DNA case with no successful upload
    dna_case_ids: Set[str] = upload_mip_analysis_scout_api.get_unique_dna_cases_related_to_rna_case(
        case_id=rna_case_id
    )
    dna_case: Case = rna_store.get_case_by_internal_id(internal_id=list(dna_case_ids)[0])
    dna_case.analyses[0].uploaded_at = None

    # WHEN trying to upload the report
    # THEN a CgDataError should be raised
    with pytest.raises(CgDataError):
        upload_mip_analysis_scout_api.upload_rna_report_to_dna_case_in_scout(
            dry_run=False,
            rna_case_id=rna_case_id,
            report_type=ScoutCustomCaseReportTags.MULTIQC,
            report_file=multiqc_file,
        )
