"""Tests for RNA part of the scout upload API"""
import logging
from typing import Generator, List
import pytest
from _pytest.logging import LogCaptureFixture

from alchy import Query
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import Pipeline
from cg.constants.sequencing import SequencingMethod
from cg.exc import CgDataError
from cg.meta.upload.scout.uploadscoutapi import UploadScoutAPI
from cg.store import Store, models
from tests.store_helpers import StoreHelpers


def set_is_tumour_on_case(store: Store, case_id: str, is_tumour: bool):
    for link in store.family(case_id).links:
        link.sample.is_tumour = is_tumour


def get_subject_id_from_case(store: Store, case_id: str) -> str:
    for link in store.family(case_id).links:
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
        store=rna_store, customer=rna_store.family(dna_case_id).customer
    )
    another_sample_id = helpers.add_sample(
        store=rna_store,
        name=another_sample_id,
        subject_id=subject_id,
        is_tumour=True,
        application_tag=SequencingMethod.WGS,
        application_type=SequencingMethod.WGS,
    )
    helpers.add_relationship(store=rna_store, sample=another_sample_id, case=dna_extra_case)
    rna_store.commit()


def ensure_extra_rna_case_match(
    another_rna_sample_id: str,
    helpers: StoreHelpers,
    rna_case_id: str,
    rna_store: Store,
) -> None:
    """Ensures that we have an extra RNA case that matches by subject_id the existing RNA case and DNA cases."""
    rna_extra_case = helpers.ensure_case(
        store=rna_store,
        data_analysis=Pipeline.MIP_RNA,
        customer=rna_store.family(rna_case_id).customer,
    )
    subject_id: str = get_subject_id_from_case(store=rna_store, case_id=rna_case_id)
    another_rna_sample_id = helpers.add_sample(
        store=rna_store,
        internal_id=another_rna_sample_id,
        subject_id=subject_id,
        is_tumour=False,
        application_type=SequencingMethod.WTS,
    )
    helpers.add_relationship(store=rna_store, sample=another_rna_sample_id, case=rna_extra_case)


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
    dna_customer_sample_name: str = rna_store.sample(internal_id=dna_sample_son_id).name
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
    dna_customer_sample_name: str = rna_store.sample(internal_id=dna_sample_son_id).name
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
    dna_customer_sample_name: str = rna_store.sample(internal_id=dna_sample_son_id).name
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
    dna_customer_sample_name: str = rna_store.sample(internal_id=dna_sample_son_id).name
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
    for link in rna_store.family(rna_case_id).links:
        link.sample.subject_id = ""
    for link in rna_store.family(dna_case_id).links:
        link.sample.subject_id = ""
    rna_store.commit()
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
    for link in rna_store.family(rna_case_id).links:
        link.sample.subject_id = ""
    for link in rna_store.family(dna_case_id).links:
        link.sample.subject_id = ""
    rna_store.commit()
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
    for link in rna_store.family(rna_case_id).links:
        link.sample.subject_id = ""
    for link in rna_store.family(dna_case_id).links:
        link.sample.subject_id = ""
    rna_store.commit()
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
    rna_store.commit()
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
    rna_store.commit()
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
    rna_store.commit()
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
    """Test that RNA samples are removed when filtering sample list by pipeline"""

    # GIVEN an RNA sample that is connected by subject ID to one RNA and one DNA sample in other cases

    ensure_extra_rna_case_match(another_rna_sample_id, helpers, rna_case_id, rna_store)
    upload_scout_api.status_db = rna_store

    dna_sample: models.Sample = rna_store.sample(dna_sample_son_id)
    another_rna_sample_id: models.Sample = rna_store.sample(another_rna_sample_id)
    all_son_rna_dna_samples: List[models.Sample] = [dna_sample, another_rna_sample_id]

    # WHEN running the method to filter a list of models.Sample objects containing RNA and DNA samples connected by subject_id
    only_son_dna_samples = upload_scout_api._get_application_prep_category(all_son_rna_dna_samples)

    # THEN even though an RNA sample is present in the initial query, the output should not contain any RNA samples
    nr_of_subject_id_samples: int = len(all_son_rna_dna_samples)
    nr_of_subject_id_dna_samples: int = len([only_son_dna_samples])
    assert nr_of_subject_id_samples == 2
    assert nr_of_subject_id_dna_samples == 1


def test_create_rna_dna_sample_case_map(
    rna_case_id: str,
    rna_store: Store,
    upload_scout_api: UploadScoutAPI,
):
    """Test that the create_rna_dna_sample_case_map returns a nested dictionary."""

    # GIVEN an RNA case with RNA samples that are connected by subject ID to DNA samples in a DNA case
    rna_case: models.Family = rna_store.families(enquiry=rna_case_id).first()

    # WHEN running the method to create a nested dictionary with the relationships between RNA/DNA samples and DNA cases
    rna_dna_case_map: dict = upload_scout_api.create_rna_dna_sample_case_map(rna_case=rna_case)

    # THEN the output should be a nested dictionary for each key: {key:{value:[]}}
    assert all(isinstance(items, dict) for items in rna_dna_case_map.values())


def test_add_rna_sample(
    rna_case_id: str,
    rna_store: Store,
    upload_scout_api: UploadScoutAPI,
):
    """Test that for a given RNA case the RNA samples are added to the rna_dna_case_map."""

    # GIVEN an RNA case and the associated RNA samples
    rna_case: models.Family = rna_store.families(enquiry=rna_case_id).first()
    rna_sample_list: list = rna_store.samples(enquiry="rna").all()

    # WHEN running the method to create a nested dictionary with the relationships between RNA/DNA samples and DNA cases
    rna_dna_case_map: dict = upload_scout_api.create_rna_dna_sample_case_map(rna_case=rna_case)

    # THEN the resulting dictionary should contain all RNA samples in the case
    for key in rna_sample_list:
        assert key.internal_id in list(rna_dna_case_map.keys())


def test_link_rna_sample_to_dna_sample(
    dna_sample_son_id: str,
    rna_sample_son_id: str,
    rna_store: Store,
    upload_scout_api: UploadScoutAPI,
):
    """Test for a given RNA sample, the associated DNA sample name matches and is present in rna_dna_case_map."""

    # GIVEN an RNA sample
    rna_sample: models.Sample = rna_store.sample(rna_sample_son_id)

    # WHEN adding the RNA sample to the rna_dna_case_map
    rna_dna_case_map: dict = {}
    upload_scout_api._add_rna_sample(
        rna_sample=rna_sample, rna_dna_sample_case_map=rna_dna_case_map
    )

    # THEN the rna_dna_case_map should contain the RNA sample
    assert rna_sample_son_id in rna_dna_case_map

    # THEN the rna_dna_case_map values should contain the associated DNA sample
    dna_samples: dict = rna_dna_case_map[rna_sample.internal_id]
    assert dna_sample_son_id in dna_samples


def test_add_dna_cases_to_dna_sample(
    dna_case_id: str,
    dna_sample_son_id: str,
    rna_sample_son_id: str,
    rna_store: Store,
    upload_scout_api: UploadScoutAPI,
):
    """Test for a given RNA sample, the DNA case name matches to the case name of the DNA sample in rna_dna_case_map."""

    # GIVEN an RNA sample, a DNA sample, and a DNA case
    rna_sample: models.Sample = rna_store.sample(rna_sample_son_id)
    dna_sample: models.Sample = rna_store.sample(dna_sample_son_id)
    dna_case: models.Family = rna_store.families(enquiry=dna_case_id).first()

    # WHEN adding the RNA sample rna_dna_case_map
    rna_dna_case_map: dict = {}
    upload_scout_api._add_rna_sample(
        rna_sample=rna_sample, rna_dna_sample_case_map=rna_dna_case_map
    )

    # THEN the rna_dna_case_map should contain the DNA_case name associated with the DNA sample
    case_names: list = rna_dna_case_map[rna_sample.internal_id][dna_sample.name]
    assert dna_case.internal_id in case_names
