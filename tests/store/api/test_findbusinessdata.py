"""Tests the findbusinessdata part of the Cg store API."""
from datetime import datetime
from typing import List

from cg.store import Store
from cg.store.models import Application, ApplicationVersion, Flowcell, Sample, FamilySample, Family
from cg.constants.indexes import ListIndexes
from cg.store.models import Sample, Flowcell, ApplicationVersion, Application
from tests.store_helpers import StoreHelpers


def test_find_analysis_via_date(
    sample_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test returning an analysis using a date."""
    # GIVEN a case with an analysis with a start date in the database
    analysis = helpers.add_analysis(store=sample_store, started_at=timestamp_now)
    assert analysis.started_at

    # WHEN getting analysis via case_id and start date
    db_analysis = sample_store.analysis(analysis.family, analysis.started_at)

    # THEN the analysis should have been retrieved
    assert db_analysis == analysis


def test_get_flow_cell(flow_cell_id: str, re_sequenced_sample_store: Store):
    """Test function to return the latest flow cell from the database."""

    # GIVEN a store with two flow cells

    # WHEN fetching the latest flow cell
    flow_cell: Flowcell = re_sequenced_sample_store.get_flow_cell(flow_cell_id=flow_cell_id)

    # THEN the returned flow cell should have the same name as the one in the database
    assert flow_cell.name == flow_cell_id


def test_get_flow_cell(flow_cell_id: str, re_sequenced_sample_store: Store):
    """Test returning the latest flow cell from the database."""

    # GIVEN a store with two flow cells

    # WHEN fetching the latest flow cell
    flow_cell: Flowcell = re_sequenced_sample_store.get_flow_cell(flow_cell_id=flow_cell_id)

    # THEN the returned flow cell should have the same name as the one in the database
    assert flow_cell.name == flow_cell_id


def test_get_samples_from_flow_cell(
    flow_cell_id: str, sample_id: str, re_sequenced_sample_store: Store
):
    """Test returning samples present on the latest flow cell from the database."""

    # GIVEN a store with two flow cells

    # WHEN fetching the samples from the latest flow cell
    samples: List[Sample] = re_sequenced_sample_store.get_samples_from_flow_cell(
        flow_cell_id=flow_cell_id
    )

    # THEN the returned sample id should have the same id as the one in the database
    assert samples[0].internal_id == sample_id


def test_get_latest_flow_cell_on_case(
    re_sequenced_sample_store: Store, case_id: str, flow_cell_id: str
):
    """Test returning the latest sequenced flow cell on a case."""

    # GIVEN a store with two flow cells in it, one being the latest sequenced of the two
    latest_flow_cell: Flowcell = re_sequenced_sample_store.Flowcell.query.filter(
        Flowcell.name == flow_cell_id
    ).first()

    # WHEN fetching the latest flow cell on a case with a sample that has been sequenced on both flow cells
    latest_flow_cell_on_case: Flowcell = re_sequenced_sample_store.get_latest_flow_cell_on_case(
        family_id=case_id
    )

    # THEN the fetched flow cell should have the same name as the other
    assert latest_flow_cell.name == latest_flow_cell_on_case.name


def test_get_customer_id_from_ticket(analysis_store, customer_id, ticket: str):
    """Tests if the function in fact returns the correct customer."""
    # Given a store with a ticket

    # Then the function should return the customer connected to the ticket
    assert analysis_store.get_customer_id_from_ticket(ticket) == customer_id


def test_get_latest_ticket_from_case(case_id: str, analysis_store_single_case, ticket: str):
    """Tests if the correct ticket is returned for the given case."""
    # GIVEN a populated store with a case

    # WHEN the function is called
    ticket_from_case: str = analysis_store_single_case.get_latest_ticket_from_case(case_id=case_id)

    # THEN the ticket should be correct
    assert ticket == ticket_from_case


def test_get_case_pool(case_id: str, rml_pool_store: Store):
    """Tests if the correct pool is returned."""
    # GIVEN a case connected to a pool
    case_name = rml_pool_store.family(internal_id=case_id).name
    # WHEN the function is called
    pool = rml_pool_store.get_case_pool(case_id=case_id)
    # THEN the correct pool should be returned and the pool name should be the last part of the
    # case name
    assert pool.name == case_name.split("-", 1)[-1]


def test_get_ready_made_library_expected_reads(case_id: str, rml_pool_store: Store):
    """Test if the correct number of expected reads is returned."""

    # GIVEN a case with a sample with an application version
    application_version: ApplicationVersion = (
        rml_pool_store.family(case_id).links[ListIndexes.FIRST.value].sample.application_version
    )

    # WHEN the expected reads is fetched from the case
    expected_reads: int = rml_pool_store.get_ready_made_library_expected_reads(case_id=case_id)

    # THEN the fetched reads should be equal to the expected reads of the application versions application
    assert application_version.application.expected_reads == expected_reads


def test_get_application_by_case(case_id: str, rml_pool_store: Store):
    """Test that the correct application is returned on a case."""
    # GIVEN a case with a sample with an application version
    application_version: ApplicationVersion = (
        rml_pool_store.family(case_id).links[ListIndexes.FIRST.value].sample.application_version
    )

    # WHEN the application is fetched from the case
    application: Application = rml_pool_store.get_application_by_case(case_id=case_id)

    # THEN the fetched application should be equal to the application version application
    assert application_version.application == application


def test_find_single_case_for_sample(
    sample_id_in_single_case: str, store_with_multiple_cases_and_samples: Store
):
    """Test that cases associated with a sample can be found."""

    # GIVEN a database containing a sample associated with a single case
    sample: Sample = store_with_multiple_cases_and_samples.sample(
        internal_id=sample_id_in_single_case
    )

    assert sample

    # WHEN the cases associated with the sample is fetched
    cases: List[FamilySample] = store_with_multiple_cases_and_samples.get_cases_from_sample(
        sample_entry_id=sample.id
    )

    # THEN only one case is found
    assert cases and len(cases) == 1


def test_find_multiple_cases_for_sample(
    sample_id_in_multiple_cases: str, store_with_multiple_cases_and_samples: Store
):
    # GIVEN a database containing a sample associated with multiple cases
    sample: Sample = store_with_multiple_cases_and_samples.sample(
        internal_id=sample_id_in_multiple_cases
    )
    assert sample

    # WHEN the cases associated with the sample is fetched
    cases: List[FamilySample] = store_with_multiple_cases_and_samples.get_cases_from_sample(
        sample_entry_id=sample.id
    )

    # THEN multiple cases are found
    assert cases and len(cases) > 1


def test_find_cases_for_non_existing_case(store_with_multiple_cases_and_samples: Store):
    """Test that nothing happens when trying to find a case that does not exist."""

    # GIVEN a database containing some cases but not a specific case
    case_id: str = "some_case"
    case: Family = store_with_multiple_cases_and_samples.family(case_id)

    assert not case

    # WHEN trying to find cases with samples given the non existing case id
    cases = store_with_multiple_cases_and_samples.filter_cases_with_samples(case_ids=[case_id])

    # THEN no cases are found
    assert not cases
