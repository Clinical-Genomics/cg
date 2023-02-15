"""Tests the findbusinessdata part of the Cg store API."""
from datetime import datetime
from typing import List

from sqlalchemy.orm import Query

from cg.constants import FlowCellStatus
from cg.store import Store
from cg.store.models import FamilySample, Family
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


def test_get_flow_cell_query(re_sequenced_sample_store: Store):
    """Test function to return the flow cell query from the database."""

    # GIVEN a store with two flow cells

    # WHEN getting the query for the flow cells
    flow_cell_query: Query = re_sequenced_sample_store._get_flow_cell_query()

    # THEN a query should be returned
    assert isinstance(flow_cell_query, Query)


def test_get_flow_cell_sample_links_query(re_sequenced_sample_store: Store):
    """Test function to return the flow cell query from the database."""

    # GIVEN a store with two flow cells

    # WHEN getting the query for the flow cells
    flow_cell_query: Query = re_sequenced_sample_store._get_flow_cell_sample_links_query()

    # THEN a query should be returned
    assert isinstance(flow_cell_query, Query)


def test_get_flow_cells(re_sequenced_sample_store: Store):
    """Test function to return the flow cells from the database."""

    # GIVEN a store with two flow cells

    # WHEN fetching the flow cells
    flow_cells: List[Flowcell] = re_sequenced_sample_store.get_flow_cells()

    # THEN a flow cells should be returned
    assert flow_cells

    # THEN a flow cell model should be returned
    assert isinstance(flow_cells[0], Flowcell)


def test_get_flow_cell(flow_cell_id: str, re_sequenced_sample_store: Store):
    """Test returning the latest flow cell from the database."""

    # GIVEN a store with two flow cells

    # WHEN fetching the latest flow cell
    flow_cell: Flowcell = re_sequenced_sample_store.get_flow_cell(flow_cell_id=flow_cell_id)

    # THEN the returned flow cell should have the same name as the one in the database
    assert flow_cell.name == flow_cell_id


def test_get_flow_cells_by_case(
    base_store: Store,
    flow_cell_id: str,
    another_flow_cell_id: str,
    case_obj: Family,
    helpers: StoreHelpers,
    sample_obj: Sample,
):
    """Test returning the latest flow cell from the database by case."""

    # GIVEN a store with two flow cell
    helpers.add_flowcell(store=base_store, flow_cell_id=flow_cell_id, samples=[sample_obj])

    helpers.add_flowcell(store=base_store, flow_cell_id=another_flow_cell_id)

    # WHEN fetching the latest flow cell
    flow_cells: List[Flowcell] = base_store.get_flow_cells_by_case(case=case_obj)

    # THEN the flow cell samples for the case should be returned
    for flow_cell in flow_cells:
        for sample in flow_cell.samples:
            assert sample in case_obj.samples

    # THEN the returned flow cell should have the same name as the one in the database
    assert flow_cells[0].name == flow_cell_id


def test_get_flow_cells_by_statuses(another_flow_cell_id: str, re_sequenced_sample_store: Store):
    """Test returning the latest flow cell from the database by statuses."""

    # GIVEN a store with two flow cells

    # WHEN fetching the latest flow cell
    flow_cells: List[Flowcell] = re_sequenced_sample_store.get_flow_cells_by_statuses(
        flow_cell_statuses=[FlowCellStatus.ONDISK, FlowCellStatus.REQUESTED]
    )

    # THEN the flow cell status should be "ondisk"
    for flow_cell in flow_cells:
        assert flow_cell.status == FlowCellStatus.ONDISK

    # THEN the returned flow cell should have the same name as the one in the database
    assert flow_cells[0].name == another_flow_cell_id


def test_get_flow_cells_by_statuses_when_multiple_matches(
    another_flow_cell_id: str, flow_cell_id: str, re_sequenced_sample_store: Store
):
    """Test returning the latest flow cell from the database by statuses when multiple matches."""

    # GIVEN a store with two flow cells

    # GIVEN a flow cell that exist in status db with status "requested"
    flow_cells: List[Flowcell] = re_sequenced_sample_store.get_flow_cells()
    flow_cells[0].status = FlowCellStatus.REQUESTED
    re_sequenced_sample_store.add_commit(flow_cells[0])

    # WHEN fetching the latest flow cell
    flow_cells: List[Flowcell] = re_sequenced_sample_store.get_flow_cells_by_statuses(
        flow_cell_statuses=[FlowCellStatus.ONDISK, FlowCellStatus.REQUESTED]
    )

    # THEN the flow cell status should be "ondisk" or "requested"
    for flow_cell in flow_cells:
        assert flow_cell.status in [FlowCellStatus.ONDISK, FlowCellStatus.REQUESTED]

    # THEN the returned flow cell should have the same status as the ones in the database
    assert flow_cells[0].status == FlowCellStatus.REQUESTED

    assert flow_cells[1].status == FlowCellStatus.ONDISK


def test_get_flow_cells_by_statuses_when_incorrect_status(re_sequenced_sample_store: Store):
    """Test returning the latest flow cell from the database when no flow cell with status."""

    # GIVEN a store with two flow cells

    # WHEN fetching the latest flow cell
    flow_cells: List[Flowcell] = re_sequenced_sample_store.get_flow_cells_by_statuses(
        flow_cell_statuses=["does_not_exist"]
    )

    # THEN no flow cells should be returned
    assert len(list(flow_cells)) == 0


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
