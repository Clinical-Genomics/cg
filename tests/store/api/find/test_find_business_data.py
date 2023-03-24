"""Tests the findbusinessdata part of the Cg store API."""
import logging
from datetime import datetime
from typing import List

from sqlalchemy.orm import Query

from cg.constants import FlowCellStatus
from cg.store import Store
from cg.constants.indexes import ListIndexes
from cg.store.models import (
    Application,
    ApplicationVersion,
    Flowcell,
    FamilySample,
    Family,
    Sample,
    Invoice,
    Pool,
    Customer,
)
from tests.store_helpers import StoreHelpers
from cg.constants.invoice import CustomerNames


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


def test_get_flow_cell_sample_links_query(re_sequenced_sample_store: Store):
    """Test function to return the flow cell sample links query from the database."""

    # GIVEN a store with two flow cells

    # WHEN getting the query for the flow cells
    flow_cell_query: Query = re_sequenced_sample_store._get_join_flow_cell_sample_links_query()

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


def test_get_flow_cell_by_enquiry(flow_cell_id: str, re_sequenced_sample_store: Store):
    """Test returning the latest flow cell from the database by enquiry."""

    # GIVEN a store with two flow cells

    # WHEN fetching the latest flow cell
    flow_cell: List[Flowcell] = re_sequenced_sample_store.get_flow_cell_by_enquiry(
        flow_cell_id_enquiry=flow_cell_id[:4]
    )

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
        flow_cell_statuses=[FlowCellStatus.ON_DISK, FlowCellStatus.REQUESTED]
    )

    # THEN the flow cell status should be "ondisk"
    for flow_cell in flow_cells:
        assert flow_cell.status == FlowCellStatus.ON_DISK

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
        flow_cell_statuses=[FlowCellStatus.ON_DISK, FlowCellStatus.REQUESTED]
    )

    # THEN the flow cell status should be "ondisk" or "requested"
    for flow_cell in flow_cells:
        assert flow_cell.status in [FlowCellStatus.ON_DISK, FlowCellStatus.REQUESTED]

    # THEN the returned flow cell should have the same status as the ones in the database
    assert flow_cells[0].status == FlowCellStatus.REQUESTED

    assert flow_cells[1].status == FlowCellStatus.ON_DISK


def test_get_flow_cells_by_statuses_when_incorrect_status(re_sequenced_sample_store: Store):
    """Test returning the latest flow cell from the database when no flow cell with incorrect status."""

    # GIVEN a store with two flow cells

    # WHEN fetching the latest flow cell
    flow_cells: List[Flowcell] = re_sequenced_sample_store.get_flow_cells_by_statuses(
        flow_cell_statuses=["does_not_exist"]
    )

    # THEN no flow cells should be returned
    assert not list(flow_cells)


def test_get_flow_cell_by_enquiry_and_status(flow_cell_id: str, re_sequenced_sample_store: Store):
    """Test returning the latest flow cell from the database by enquiry and status."""

    # GIVEN a store with two flow cells

    # WHEN fetching the latest flow cell
    flow_cell: List[Flowcell] = re_sequenced_sample_store.get_flow_cell_by_enquiry_and_status(
        flow_cell_statuses=[FlowCellStatus.ON_DISK], flow_cell_id_enquiry=flow_cell_id[:4]
    )

    # THEN the returned flow cell should have the same name as the one in the database
    assert flow_cell[0].name == flow_cell_id

    # THEN the returned flow cell should have the same status as the query
    assert flow_cell[0].status == FlowCellStatus.ON_DISK


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


def test_is_all_flow_cells_on_disk_when_no_flow_cell(
    base_store: Store,
    caplog,
    case_id: str,
):
    """Test check if all flow cells for samples on a case is on disk when no flow cells."""
    caplog.set_level(logging.DEBUG)

    # WHEN fetching the latest flow cell
    is_on_disk = base_store.is_all_flow_cells_on_disk(case_id=case_id)

    # THEN return false
    assert is_on_disk is False

    # THEN log no flow cells found
    assert "No flow cells found" in caplog.text


def test_is_all_flow_cells_on_disk_when_not_on_disk(
    base_store: Store,
    caplog,
    flow_cell_id: str,
    another_flow_cell_id: str,
    case_id: str,
    helpers: StoreHelpers,
    sample_obj: Sample,
):
    """Test check if all flow cells for samples on a case is on disk when not on disk."""
    caplog.set_level(logging.DEBUG)
    # GIVEN a store with two flow cell
    flow_cell = helpers.add_flowcell(
        store=base_store,
        flow_cell_id=flow_cell_id,
        samples=[sample_obj],
        status=FlowCellStatus.PROCESSING,
    )

    another_flow_cell = helpers.add_flowcell(
        store=base_store,
        flow_cell_id=another_flow_cell_id,
        samples=[sample_obj],
        status=FlowCellStatus.RETRIEVED,
    )

    # WHEN fetching the latest flow cell
    is_on_disk = base_store.is_all_flow_cells_on_disk(case_id=case_id)

    # THEN return false
    assert is_on_disk is False

    # THEN log the status of the flow cell
    assert f"{flow_cell.name}: {flow_cell.status}" in caplog.text
    assert f"{another_flow_cell.name}: {another_flow_cell.status}" in caplog.text


def test_is_all_flow_cells_on_disk_when_requested(
    base_store: Store,
    caplog,
    flow_cell_id: str,
    another_flow_cell_id: str,
    case_id: str,
    helpers: StoreHelpers,
    sample_obj: Sample,
):
    """Test check if all flow cells for samples on a case is on disk when requested."""
    caplog.set_level(logging.DEBUG)
    # GIVEN a store with two flow cell
    flow_cell = helpers.add_flowcell(
        store=base_store,
        flow_cell_id=flow_cell_id,
        samples=[sample_obj],
        status=FlowCellStatus.REMOVED,
    )

    another_flow_cell = helpers.add_flowcell(
        store=base_store,
        flow_cell_id=another_flow_cell_id,
        samples=[sample_obj],
        status=FlowCellStatus.REQUESTED,
    )

    # WHEN fetching the latest flow cell
    is_on_disk = base_store.is_all_flow_cells_on_disk(case_id=case_id)

    # THEN return false
    assert is_on_disk is False

    # THEN log the requesting the flow cell
    assert f"{flow_cell.name}: flow cell not on disk, requesting" in caplog.text

    # THEN log the status of the flow cell
    assert f"{another_flow_cell.name}: {another_flow_cell.status}" in caplog.text


def test_is_all_flow_cells_on_disk(
    base_store: Store,
    caplog,
    flow_cell_id: str,
    another_flow_cell_id: str,
    case_id: str,
    helpers: StoreHelpers,
    sample_obj: Sample,
):
    """Test check if all flow cells for samples on a case is on disk."""
    caplog.set_level(logging.DEBUG)
    # GIVEN a store with two flow cell
    flow_cell = helpers.add_flowcell(
        store=base_store, flow_cell_id=flow_cell_id, samples=[sample_obj]
    )

    helpers.add_flowcell(store=base_store, flow_cell_id=another_flow_cell_id)

    # WHEN fetching the latest flow cell
    is_on_disk = base_store.is_all_flow_cells_on_disk(case_id=case_id)

    # THEN return true
    assert is_on_disk is True

    # THEN log the status of the flow cell
    assert f"{flow_cell.name}: status is {flow_cell.status}" in caplog.text


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


def test_get_ready_made_library_expected_reads(case_id: str, rml_pool_store: Store):
    """Test if the correct number of expected reads is returned."""

    # GIVEN a case with a sample with an application version
    application_version: ApplicationVersion = (
        rml_pool_store.get_case_by_internal_id(internal_id=case_id)
        .links[ListIndexes.FIRST.value]
        .sample.application_version
    )

    # WHEN the expected reads is fetched from the case
    expected_reads: int = rml_pool_store.get_ready_made_library_expected_reads(case_id=case_id)

    # THEN the fetched reads should be equal to the expected reads of the application versions application
    assert application_version.application.expected_reads == expected_reads


def test_get_application_by_case(case_id: str, rml_pool_store: Store):
    """Test that the correct application is returned on a case."""
    # GIVEN a case with a sample with an application version
    application_version: ApplicationVersion = (
        rml_pool_store.get_case_by_internal_id(internal_id=case_id)
        .links[ListIndexes.FIRST.value]
        .sample.application_version
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
    sample: Sample = store_with_multiple_cases_and_samples.get_sample_by_internal_id(
        internal_id=sample_id_in_single_case
    )

    assert sample

    # WHEN the cases associated with the sample is fetched
    cases: List[FamilySample] = store_with_multiple_cases_and_samples.get_cases_from_sample(
        sample_entry_id=sample.id
    ).all()

    # THEN only one case is found
    assert cases and len(cases) == 1


def test_find_multiple_cases_for_sample(
    sample_id_in_multiple_cases: str, store_with_multiple_cases_and_samples: Store
):
    # GIVEN a database containing a sample associated with multiple cases
    sample: Sample = store_with_multiple_cases_and_samples.get_sample_by_internal_id(
        internal_id=sample_id_in_multiple_cases
    )
    assert sample

    # WHEN the cases associated with the sample is fetched
    cases: List[FamilySample] = store_with_multiple_cases_and_samples.get_cases_from_sample(
        sample_entry_id=sample.id
    ).all()

    # THEN multiple cases are found
    assert cases and len(cases) > 1


def test_find_cases_for_non_existing_case(store_with_multiple_cases_and_samples: Store):
    """Test that nothing happens when trying to find a case that does not exist."""

    # GIVEN a database containing some cases but not a specific case
    case_id: str = "some_case"
    case: Family = store_with_multiple_cases_and_samples.get_case_by_internal_id(
        internal_id=case_id
    )

    assert not case

    # WHEN trying to find cases with samples given the non existing case id
    cases = store_with_multiple_cases_and_samples.filter_cases_with_samples(case_ids=[case_id])

    # THEN no cases are found
    assert not cases


def test_is_case_down_sampled_true(base_store: Store, case_obj: Family, sample_id: str):
    """Tests the down sampling check when all samples are down sampled."""
    # GIVEN a case where all samples are down sampled
    for sample in case_obj.samples:
        sample.from_sample = sample_id
    base_store.commit()

    # WHEN checking if all sample in the case are down sampled
    is_down_sampled: bool = base_store.is_case_down_sampled(case_id=case_obj.internal_id)

    # THEN the return value should be True
    assert is_down_sampled


def test_is_case_down_sampled_false(base_store: Store, case_obj: Family, sample_id: str):
    """Tests the down sampling check when none of the samples are down sampled."""
    # GIVEN a case where all samples are not down sampled
    for sample in case_obj.samples:
        assert not sample.from_sample

    # WHEN checking if all sample in the case are down sampled
    is_down_sampled: bool = base_store.is_case_down_sampled(case_id=case_obj.internal_id)

    # THEN the return value should be False
    assert not is_down_sampled


def test_is_case_external_true(
    base_store: Store, case_obj: Family, helpers: StoreHelpers, sample_id: str
):
    """Tests the external case check when all the samples are external."""
    # GIVEN a case where all samples are not external
    external_application_version: ApplicationVersion = helpers.ensure_application_version(
        store=base_store, is_external=True
    )
    for sample in case_obj.samples:
        sample.application_version = external_application_version
    base_store.commit()

    # WHEN checking if all sample in the case are external
    is_external: bool = base_store.is_case_external(case_id=case_obj.internal_id)

    # THEN the return value should be False
    assert is_external


def test_is_case_external_false(base_store: Store, case_obj: Family, sample_id: str):
    """Tests the external case check when none of the samples are external."""
    # GIVEN a case where all samples are not external
    for sample in case_obj.samples:
        assert not sample.application_version.application.is_external

    # WHEN checking if all sample in the case are external
    is_external: bool = base_store.is_case_external(case_id=case_obj.internal_id)

    # THEN the return value should be False
    assert not is_external


def test_get_invoice_by_status(store_with_an_invoice_with_and_without_attributes: Store):
    """Test that invoices can be fetched by status."""
    # GIVEN a database with two invoices of which one has attributes

    # WHEN fetching the invoice by status
    invoices: List[
        Invoice
    ] = store_with_an_invoice_with_and_without_attributes.get_invoices_by_status(is_invoiced=True)

    # THEN one invoice should be returned
    assert invoices

    # THEN there should be one invoice
    assert len(invoices) == 1

    # THEN the invoice should have that is invoiced
    assert invoices[0].invoiced_at


def test_get_invoice_by_id(store_with_an_invoice_with_and_without_attributes: Store):
    """Test that invoices can be fetched by invoice id."""
    # GIVEN a database with two invoices of which one has attributes

    # WHEN fetching the invoice by invoice id
    invoice: Invoice = store_with_an_invoice_with_and_without_attributes.get_invoice_by_entry_id(
        entry_id=1
    )

    # THEN one invoice should be returned
    assert invoice

    # THEN the invoice should have id 1
    assert invoice.id == 1


def test_get_pools(store_with_multiple_pools_for_customer: Store):
    """Test that pools can be fetched from the store."""
    # GIVEN a database with two pools

    # WHEN getting all pools
    pools: List[Pool] = store_with_multiple_pools_for_customer.get_pools()

    # THEN two pools should be returned
    assert len(pools) == 2


def test_get_pools_by_customer_id(store_with_multiple_pools_for_customer: Store):
    """Test that pools can be fetched from the store by customer id."""
    # GIVEN a database with two pools

    # WHEN getting pools by customer id
    pools: List[Pool] = store_with_multiple_pools_for_customer.get_pools_by_customer_id(
        customers=store_with_multiple_pools_for_customer.get_customers()
    )

    # THEN two pools should be returned
    assert len(pools) == 2


def test_get_pools_by_name_enquiry(store_with_multiple_pools_for_customer: Store, pool_name_1: str):
    """Test that pools can be fetched from the store by customer id."""
    # GIVEN a database with two pools

    # WHEN fetching pools by customer id
    pools: List[Pool] = store_with_multiple_pools_for_customer.get_pools_by_name_enquiry(
        name_enquiry=pool_name_1
    )

    # THEN one pool should be returned
    assert len(pools) == 1


def test_get_pools_by_order_enquiry(
    store_with_multiple_pools_for_customer: Store, pool_order_1: str
):
    """Test that pools can be fetched from the store by customer id."""
    # GIVEN a database with two pools

    # WHEN getting pools by customer id
    pools: List[Pool] = store_with_multiple_pools_for_customer.get_pools_by_order_enquiry(
        order_enquiry=pool_order_1
    )

    # THEN one pool should be returned
    assert len(pools) == 1


def test_get_pools_to_render_with(
    store_with_multiple_pools_for_customer: Store,
    pool_name_1: str,
    pool_order_1: str,
):
    """Test that pools can be fetched from the store by customer id."""
    # GIVEN a database with two pools

    # WHEN fetching pools with no customer or enquiry
    pools: List[Pool] = store_with_multiple_pools_for_customer.get_pools_to_render()

    # THEN two pools should be returned
    assert len(pools) == 2


def test_get_pools_to_render_with_customer(
    store_with_multiple_pools_for_customer: Store,
):
    """Test that pools can be fetched from the store by customer id."""
    # GIVEN a database with two pools

    # WHEN getting pools by customer id
    pools: List[Pool] = store_with_multiple_pools_for_customer.get_pools_to_render(
        customers=store_with_multiple_pools_for_customer.get_customers()
    )

    # THEN two pools should be returned
    assert len(pools) == 2


def test_get_pools_to_render_with_customer_and_name_enquiry(
    store_with_multiple_pools_for_customer: Store,
    pool_name_1: str,
):
    """Test that pools can be fetched from the store by customer id."""
    # GIVEN a database with two pools
    # WHEN fetching pools by customer id and name enquiry
    pools: List[Pool] = store_with_multiple_pools_for_customer.get_pools_to_render(
        customers=store_with_multiple_pools_for_customer.get_customers(), enquiry=pool_name_1
    )

    # THEN one pools should be returned
    assert len(pools) == 1


def test_get_pools_to_render_with_customer_and_order_enquiry(
    store_with_multiple_pools_for_customer: Store,
    pool_order_1: str,
):
    """Test that pools can be fetched from the store by customer id."""
    # GIVEN a database with two pools

    # WHEN fetching pools by customer id and order enquiry

    pools: List[Pool] = store_with_multiple_pools_for_customer.get_pools_to_render(
        customers=store_with_multiple_pools_for_customer.get_customers(), enquiry=pool_order_1
    )

    # THEN one pools should be returned
    assert len(pools) == 1


def test_get_case_action(store_with_active_sample_analyze: Store):
    """Test to get the action of a case"""
    # GIVEN a database with an active sample

    # WHEN fetching the case action
    action: str = store_with_active_sample_analyze.get_case_action(
        sample=store_with_active_sample_analyze.get_samples()[0].links[0]
    )

    # THEN the action should be analyze
    assert action == "analyze"
