"""Tests for RNA part of the scout upload API"""
import logging
from typing import Optional
import pytest

from cgmodels.cg.constants import Pipeline

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import DataDelivery
from cg.meta.upload.scout.uploadscoutapi import UploadScoutAPI
from cg.store import Store, models
from tests.store_helpers import StoreHelpers


def _get_dna_case(store: Store, helpers: StoreHelpers) -> models.Family:
    new_case_obj = helpers.ensure_case(
        store=store,
        name="dna_case",
        customer=helpers.ensure_customer(store=store),
        data_analysis=Pipeline.MIP_DNA,
        data_delivery=DataDelivery.SCOUT,
    )

    return new_case_obj


def _create_rna_case(store: Store, helpers: StoreHelpers, case_id: str) -> models.Family:
    new_case_obj = helpers.ensure_case(
        store=store,
        name="rna_case",
        customer=helpers.ensure_customer(store=store),
        data_analysis=Pipeline.MIP_RNA,
        data_delivery=DataDelivery.SCOUT,
    )
    new_case_obj.internal_id = case_id

    return new_case_obj


def _get_dna_case_with_sample(store: Store, helpers: StoreHelpers) -> models.Family:
    dna_case = _get_dna_case(store=store, helpers=helpers)
    sample = helpers.add_sample(store=store)
    helpers.add_relationship(store=store, sample=sample, case=dna_case)
    store.add_commit(dna_case)
    return dna_case


def _create_rna_case_with_sample(
    store: Store, helpers: StoreHelpers, case_id: str, sample_id: str
) -> models.Family:
    case = _create_rna_case(store=store, helpers=helpers, case_id=case_id)
    sample = helpers.add_sample(store=store)
    sample.internal_id = sample_id
    helpers.add_relationship(store=store, sample=sample, case=case)
    store.add_commit(case)
    return case


def _existing_case(store: Store, case_id) -> bool:
    return store.family(internal_id=case_id) is not None


def _existing_dna_case(store: Store, dna_case_id: str) -> bool:
    return _existing_case(store, dna_case_id)


def _existing_rna_case(store: Store, rna_case_id: str) -> bool:
    return _existing_case(store, rna_case_id)


def _sample_in_the_rna_case_is_connected_to_a_sample_in_the_dna_case_via_subject_id(
    store: Store, rna_case_id: str, dna_case_id: str
):
    rna_subject_ids = set()
    for rna_link in store.family(rna_case_id).links:
        rna_sample: models.Sample = rna_link.sample
        rna_subject_id = rna_sample.subject_id
        rna_subject_ids.add(rna_subject_id)

    dna_subject_ids = set()
    for dna_link in store.family(dna_case_id).links:
        dna_sample: models.Sample = dna_link.sample
        dna_subject_id = dna_sample.subject_id
        dna_subject_ids.add(dna_subject_id)

    return rna_subject_ids.intersection(dna_subject_ids) is not None


def _connected_rna_sample_has_junction_bed_in_housekeeper(
    housekeeper: HousekeeperAPI, rna_case_id: str, connected_rna_sample_id: str
) -> bool:

    tags = set(["junction", "bed", connected_rna_sample_id])
    file = housekeeper.find_file_in_latest_version(case_id="", tags=tags)
    return connected_rna_sample_id in file.path


def _connected_rna_sample_has_bigwig_in_housekeeper(
    housekeeper: HousekeeperAPI, connected_rna_sample_id: str
) -> bool:
    tags = set(["bigwig", "coverage", connected_rna_sample_id])
    file = housekeeper.find_file_in_latest_version(case_id="", tags=tags)
    return connected_rna_sample_id in file.path


def _case_has_samples(store: Store, case_id: str) -> bool:

    if store.family(internal_id=case_id).links:
        return True
    return False


def _connect_sample_in_cases_via_subject_id(store, first_case_id, second_case_id):
    subject_id = "a_subject_id"

    for link in store.family(first_case_id).links:
        sample: models.Sample = link.sample
        sample.subject_id = subject_id
        break

    for link in store.family(second_case_id).links:
        sample: models.Sample = link.sample
        sample.subject_id = subject_id
        break

    store.commit()


def _get_dna_sample_id(store: Store, dna_case_id: str) -> Optional[str]:
    for link in store.family(internal_id=dna_case_id).links:
        return link.sample.internal_id


def _connected_rna_sample_has_fusion_report_in_housekeeper(housekeeper, rna_case_id):
    tags = set(["fusion", "pdf", rna_case_id])
    file = housekeeper.find_file_in_latest_version(case_id=rna_case_id, tags=tags)
    return rna_case_id in file.path


def test_upload_rna_junctions_to_scout(
    upload_scout_api: UploadScoutAPI,
    base_store: Store,
    helpers: StoreHelpers,
    mip_rna_analysis_hk_api: HousekeeperAPI,
    case_id: str,
    sample_id: str,
    caplog,
):
    """Test that A RNA case's gene fusion report and junction splice files for all samples can be loaded via a cg CLI
    command into an already existing DNA case"""

    store: Store = base_store
    rna_case_id: str = case_id
    rna_sample_id: str = sample_id

    # GIVEN an existing RNA case with related sample
    _create_rna_case_with_sample(
        store=store, helpers=helpers, case_id=rna_case_id, sample_id=rna_sample_id
    )

    # GIVEN an existing DNA case with related sample
    dna_case_id: str = _get_dna_case_with_sample(store=store, helpers=helpers).internal_id

    # GIVEN a sample in the RNA case is connected to a sample in the DNA case via subject_id (i.e. same subject_id)
    _connect_sample_in_cases_via_subject_id(
        store=store, first_case_id=rna_case_id, second_case_id=dna_case_id
    )

    # GIVEN the connected RNA case has a fusion report in Housekeeper
    # GIVEN the connected RNA sample has a junction bed in Housekeeper
    # GIVEN the connected RNA sample has a bigWig in Housekeeper

    # WHEN running the method to upload RNA files to Scout
    caplog.set_level(logging.INFO)
    upload_scout_api.upload_rna_junctions_to_scout(case_id=rna_case_id, dry_run=True)

    # THEN the 2 files should have been uploaded to the connected sample on the dna case in scout
    assert "Splice junctions bed uploaded successfully to Scout" in caplog.text
    assert "Rna coverage bigwig uploaded successfully to Scout" in caplog.text


def test_upload_splice_junctions_bed_to_scout(
    upload_scout_api: UploadScoutAPI,
    base_store: Store,
    helpers: StoreHelpers,
    mip_rna_analysis_hk_api: HousekeeperAPI,
    case_id: str,
    sample_id: str,
    caplog,
):
    """Test that A RNA case's gene fusion report and junction splice files for all samples can be loaded via a cg CLI
    command into an already existing DNA case"""

    store: Store = base_store
    rna_case_id: str = case_id
    rna_sample_id: str = sample_id

    # GIVEN an existing RNA case with related sample
    _create_rna_case_with_sample(
        store=store, helpers=helpers, case_id=rna_case_id, sample_id=rna_sample_id
    )

    # GIVEN an existing DNA case with related sample
    dna_case_id: str = _get_dna_case_with_sample(store=store, helpers=helpers).internal_id

    # GIVEN a sample in the RNA case is connected to a sample in the DNA case via subject_id (i.e. same subject_id)
    _connect_sample_in_cases_via_subject_id(
        store=store, first_case_id=rna_case_id, second_case_id=dna_case_id
    )

    # GIVEN the connected RNA case has a fusion report in Housekeeper
    # GIVEN the connected RNA sample has a junction bed in Housekeeper
    # GIVEN the connected RNA sample has a bigWig in Housekeeper

    # WHEN running the method to upload RNA files to Scout
    caplog.set_level(logging.INFO)
    upload_scout_api.upload_splice_junctions_bed_to_scout(case_id=rna_case_id, dry_run=True)

    # THEN the splice junctions file should have been uploaded to the connected sample on the dna case in scout
    assert "Splice junctions bed uploaded successfully to Scout" in caplog.text
    assert "Rna coverage bigwig uploaded successfully to Scout" not in caplog.text


def test_upload_rna_coverage_bigwig_to_scout(
    upload_scout_api: UploadScoutAPI,
    base_store: Store,
    helpers: StoreHelpers,
    mip_rna_analysis_hk_api: HousekeeperAPI,
    case_id: str,
    sample_id: str,
    caplog,
):
    """Test that A RNA case's gene fusion report and junction splice files for all samples can be loaded via a cg CLI
    command into an already existing DNA case"""

    store: Store = base_store
    rna_case_id: str = case_id
    rna_sample_id: str = sample_id

    # GIVEN an existing RNA case with related sample
    _create_rna_case_with_sample(
        store=store, helpers=helpers, case_id=rna_case_id, sample_id=rna_sample_id
    )

    # GIVEN an existing DNA case with related sample
    dna_case_id: str = _get_dna_case_with_sample(store=store, helpers=helpers).internal_id

    # GIVEN a sample in the RNA case is connected to a sample in the DNA case via subject_id (i.e. same subject_id)
    _connect_sample_in_cases_via_subject_id(
        store=store, first_case_id=rna_case_id, second_case_id=dna_case_id
    )

    # GIVEN the connected RNA case has a fusion report in Housekeeper
    # GIVEN the connected RNA sample has a junction bed in Housekeeper
    # GIVEN the connected RNA sample has a bigWig in Housekeeper

    # WHEN running the method to upload RNA files to Scout
    caplog.set_level(logging.INFO)
    upload_scout_api.upload_rna_coverage_bigwig_to_scout(case_id=rna_case_id, dry_run=True)

    # THEN the bigWig file should have been uploaded to the connected sample on the dna case in scout
    assert "Splice junctions bed uploaded successfully to Scout" not in caplog.text
    assert "Rna coverage bigwig uploaded successfully to Scout" in caplog.text


def test_upload_rna_fusion_report_to_scout(
    upload_scout_api: UploadScoutAPI,
    base_store: Store,
    helpers: StoreHelpers,
    mip_rna_analysis_hk_api: HousekeeperAPI,
    case_id: str,
    sample_id: str,
    caplog,
):
    """Test that A RNA case's gene fusion report and junction splice files for all samples can be loaded via a cg CLI
    command into an already existing DNA case"""

    store: Store = base_store
    rna_case_id: str = case_id
    rna_sample_id: str = sample_id

    # GIVEN an existing RNA case with related sample
    _create_rna_case_with_sample(
        store=store, helpers=helpers, case_id=rna_case_id, sample_id=rna_sample_id
    )

    # GIVEN an existing DNA case with related sample
    dna_case_id: str = _get_dna_case_with_sample(store=store, helpers=helpers).internal_id

    # GIVEN a sample in the RNA case is connected to a sample in the DNA case via subject_id (i.e. same subject_id)
    _connect_sample_in_cases_via_subject_id(
        store=store, first_case_id=rna_case_id, second_case_id=dna_case_id
    )

    # GIVEN the connected RNA case has a fusion report in Housekeeper
    # GIVEN the connected RNA sample has a junction bed in Housekeeper
    # GIVEN the connected RNA sample has a bigWig in Housekeeper

    # WHEN running the method to upload RNA files to Scout
    caplog.set_level(logging.INFO)
    upload_scout_api.upload_fusion_report_to_scout(case_id=rna_case_id, dry_run=True)

    # THEN the fusion report file should have been uploaded to the connected sample on the dna case in scout
    assert "Splice junctions bed uploaded successfully to Scout" not in caplog.text
    assert "Rna coverage bigwig uploaded successfully to Scout" not in caplog.text
    assert "Clinical fusion report uploaded successfully to Scout" in caplog.text


def test_upload_rna_research_fusion_report_to_scout(
    upload_scout_api: UploadScoutAPI,
    base_store: Store,
    helpers: StoreHelpers,
    mip_rna_analysis_hk_api: HousekeeperAPI,
    case_id: str,
    sample_id: str,
    caplog,
):
    """Test that A RNA case's gene fusion report and junction splice files for all samples can be loaded via a cg CLI
    command into an already existing DNA case"""

    store: Store = base_store
    rna_case_id: str = case_id
    rna_sample_id: str = sample_id

    # GIVEN an existing RNA case with related sample
    _create_rna_case_with_sample(
        store=store, helpers=helpers, case_id=rna_case_id, sample_id=rna_sample_id
    )

    # GIVEN an existing DNA case with related sample
    dna_case_id: str = _get_dna_case_with_sample(store=store, helpers=helpers).internal_id

    # GIVEN a sample in the RNA case is connected to a sample in the DNA case via subject_id (i.e. same subject_id)
    _connect_sample_in_cases_via_subject_id(
        store=store, first_case_id=rna_case_id, second_case_id=dna_case_id
    )

    # GIVEN the connected RNA case has a fusion report in Housekeeper
    # GIVEN the connected RNA sample has a junction bed in Housekeeper
    # GIVEN the connected RNA sample has a bigWig in Housekeeper

    # WHEN running the method to upload RNA files to Scout
    caplog.set_level(logging.INFO)
    upload_scout_api.upload_fusion_report_to_scout(case_id=rna_case_id, dry_run=True, research=True)

    # THEN the fusion report file should have been uploaded to the connected sample on the dna case in scout
    assert "Splice junctions bed uploaded successfully to Scout" not in caplog.text
    assert "Rna coverage bigwig uploaded successfully to Scout" not in caplog.text
    assert "Research fusion report uploaded successfully to Scout" in caplog.text
