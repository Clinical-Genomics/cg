"""Tests the findbusinessdata part of the Cg store API."""
from datetime import datetime

from cg.store import Store, models
from cg.constants.indexes import ListIndexes
from tests.store_helpers import StoreHelpers


def test_find_analysis_via_date(sample_store: Store, helpers: StoreHelpers):
    # GIVEN a case with an analysis with a start date in the database
    analysis = helpers.add_analysis(store=sample_store, started_at=datetime.now())
    assert analysis.started_at

    # WHEN getting analysis via case_id and start date
    db_analysis = sample_store.analysis(analysis.family, analysis.started_at)

    # THEN the analysis should have been retrieved
    assert db_analysis == analysis


def test_get_flow_cell(flow_cell_id: str, re_sequenced_sample_store: Store):
    """Test function to return the latest flow cell froom the database."""

    # GIVEN a store with two flow cells

    # WHEN fetching the latest flow cell
    flow_cell: models.Flowcell = re_sequenced_sample_store.get_flow_cell(flow_cell_id=flow_cell_id)

    # THEN the returned flow cell should have the same name as the one in the database
    assert flow_cell.name == flow_cell_id


def test_get_latest_flow_cell_on_case(
    re_sequenced_sample_store: Store, case_id: str, flow_cell_id: str
):
    """Test function to fetch the latest sequenced flow cell on a case"""

    # GIVEN a store with two flow cells in it, one being the latest sequenced of the two
    latest_flow_cell_obj: models.Flowcell = re_sequenced_sample_store.Flowcell.query.filter(
        models.Flowcell.name == flow_cell_id
    ).first()

    # WHEN fetching the latest flow cell on a case with a sample that has been sequenced on both flow cells
    latest_flow_cell_on_case: models.Flowcell = (
        re_sequenced_sample_store.get_latest_flow_cell_on_case(family_id=case_id)
    )

    # THEN the fetched flow cell should have the same name as the other
    assert latest_flow_cell_obj.name == latest_flow_cell_on_case.name


def test_get_customer_id_from_ticket(analysis_store, customer_id, ticket: str):
    """Tests if the function in fact returns the correct customer"""
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
    application_version: models.ApplicationVersion = (
        rml_pool_store.family(case_id).links[ListIndexes.FIRST.value].sample.application_version
    )

    # WHEN the expected reads is fetched from the case
    expected_reads: int = rml_pool_store.get_ready_made_library_expected_reads(case_id=case_id)

    # THEN the fetched reads should be equal to the expected reads of the application versions application
    assert application_version.application.expected_reads == expected_reads


def test_get_application_by_case(case_id: str, rml_pool_store: Store):
    """Test that the correct application is returned on a case."""
    # GIVEN a case with a sample with an application version
    application_version: models.ApplicationVersion = (
        rml_pool_store.family(case_id).links[ListIndexes.FIRST.value].sample.application_version
    )

    # WHEN the application is fetched from the case
    application: models.Application = rml_pool_store.get_application_by_case(case_id=case_id)

    # THEN the fetched application should be equal to the application version application
    assert application_version.application == application
