"""Tests the findbusinessdata part of the Cg store API."""
import logging
from datetime import datetime
from typing import List, Optional

import pytest
from cg.constants import FlowCellStatus
from cg.constants.constants import CaseActions
from cg.constants.indexes import ListIndexes
from cg.exc import CgError
from cg.store import Store
from cg.store.models import (
    Application,
    ApplicationVersion,
    Customer,
    Family,
    FamilySample,
    Flowcell,
    Invoice,
    Pool,
    Sample,
    SampleLaneSequencingMetrics,
)
from sqlalchemy.orm import Query
from tests.store_helpers import StoreHelpers


def test_get_analysis_by_case_entry_id_and_started_at(
    sample_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test returning an analysis using a date."""
    # GIVEN a case with an analysis with a start date in the database
    analysis = helpers.add_analysis(store=sample_store, started_at=timestamp_now)
    assert analysis.started_at

    # WHEN getting analysis via case_id and start date
    db_analysis = sample_store.get_analysis_by_case_entry_id_and_started_at(
        case_entry_id=analysis.family.id, started_at_date=analysis.started_at
    )

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
    flow_cells: List[Flowcell] = re_sequenced_sample_store._get_query(table=Flowcell)

    # THEN a flow cells should be returned
    assert flow_cells

    # THEN a flow cell model should be returned
    assert isinstance(flow_cells[0], Flowcell)


def test_get_flow_cell(bcl2fastq_flow_cell_id: str, re_sequenced_sample_store: Store):
    """Test returning the latest flow cell from the database."""

    # GIVEN a store with two flow cells

    # WHEN fetching the latest flow cell
    flow_cell: Flowcell = re_sequenced_sample_store.get_flow_cell_by_name(
        flow_cell_name=bcl2fastq_flow_cell_id
    )

    # THEN the returned flow cell should have the same name as the one in the database
    assert flow_cell.name == bcl2fastq_flow_cell_id


def test_get_flow_cells_by_case(
    base_store: Store,
    bcl2fastq_flow_cell_id: str,
    dragen_flow_cell_id: str,
    case: Family,
    helpers: StoreHelpers,
    sample: Sample,
):
    """Test returning the latest flow cell from the database by case."""

    # GIVEN a store with two flow cell
    helpers.add_flowcell(store=base_store, flow_cell_name=bcl2fastq_flow_cell_id, samples=[sample])

    helpers.add_flowcell(store=base_store, flow_cell_name=dragen_flow_cell_id)

    # WHEN fetching the latest flow cell
    flow_cells: List[Flowcell] = base_store.get_flow_cells_by_case(case=case)

    # THEN the flow cell samples for the case should be returned
    for flow_cell in flow_cells:
        for sample in flow_cell.samples:
            assert sample in case.samples

    # THEN the returned flow cell should have the same name as the one in the database
    assert flow_cells[0].name == bcl2fastq_flow_cell_id


def test_get_flow_cells_by_statuses(dragen_flow_cell_id: str, re_sequenced_sample_store: Store):
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
    assert flow_cells[0].name == dragen_flow_cell_id


def test_get_flow_cells_by_statuses_when_multiple_matches(re_sequenced_sample_store: Store):
    """Test returning the latest flow cell from the database by statuses when multiple matches."""

    # GIVEN a store with two flow cells

    # GIVEN a flow cell that exist in status db with status "requested"
    flow_cells: List[Flowcell] = re_sequenced_sample_store._get_query(table=Flowcell)
    flow_cells[0].status = FlowCellStatus.REQUESTED
    re_sequenced_sample_store.session.add(flow_cells[0])
    re_sequenced_sample_store.session.commit()

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


def test_get_flow_cell_by_enquiry_and_status(
    bcl2fastq_flow_cell_id: str, re_sequenced_sample_store: Store
):
    """Test returning the latest flow cell from the database by enquiry and status."""

    # GIVEN a store with two flow cells

    # WHEN fetching the latest flow cell
    flow_cell: List[Flowcell] = re_sequenced_sample_store.get_flow_cell_by_name_pattern_and_status(
        flow_cell_statuses=[FlowCellStatus.ON_DISK], name_pattern=bcl2fastq_flow_cell_id[:4]
    )

    # THEN the returned flow cell should have the same name as the one in the database
    assert flow_cell[0].name == bcl2fastq_flow_cell_id

    # THEN the returned flow cell should have the same status as the query
    assert flow_cell[0].status == FlowCellStatus.ON_DISK


def test_get_samples_from_flow_cell(
    bcl2fastq_flow_cell_id: str, sample_id: str, re_sequenced_sample_store: Store
):
    """Test returning samples present on the latest flow cell from the database."""

    # GIVEN a store with two flow cells

    # WHEN fetching the samples from the latest flow cell
    samples: List[Sample] = re_sequenced_sample_store.get_samples_from_flow_cell(
        flow_cell_id=bcl2fastq_flow_cell_id
    )

    # THEN the returned sample id should have the same id as the one in the database
    assert samples[0].internal_id == sample_id


def test_get_latest_flow_cell_on_case(
    re_sequenced_sample_store: Store, case_id: str, bcl2fastq_flow_cell_id: str
):
    """Test returning the latest sequenced flow cell on a case."""

    # GIVEN a store with two flow cells in it, one being the latest sequenced of the two
    latest_flow_cell: Flowcell = re_sequenced_sample_store.get_flow_cell_by_name(
        flow_cell_name=bcl2fastq_flow_cell_id
    )

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
    bcl2fastq_flow_cell_id: str,
    dragen_flow_cell_id: str,
    case_id: str,
    helpers: StoreHelpers,
    sample: Sample,
):
    """Test check if all flow cells for samples on a case is on disk when not on disk."""
    caplog.set_level(logging.DEBUG)
    # GIVEN a store with two flow cell
    flow_cell = helpers.add_flowcell(
        store=base_store,
        flow_cell_name=bcl2fastq_flow_cell_id,
        samples=[sample],
        status=FlowCellStatus.PROCESSING,
    )

    another_flow_cell = helpers.add_flowcell(
        store=base_store,
        flow_cell_name=dragen_flow_cell_id,
        samples=[sample],
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
    bcl2fastq_flow_cell_id: str,
    dragen_flow_cell_id: str,
    case_id: str,
    helpers: StoreHelpers,
    sample: Sample,
):
    """Test check if all flow cells for samples on a case is on disk when requested."""
    caplog.set_level(logging.DEBUG)
    # GIVEN a store with two flow cell
    flow_cell = helpers.add_flowcell(
        store=base_store,
        flow_cell_name=bcl2fastq_flow_cell_id,
        samples=[sample],
        status=FlowCellStatus.REMOVED,
    )

    another_flow_cell = helpers.add_flowcell(
        store=base_store,
        flow_cell_name=dragen_flow_cell_id,
        samples=[sample],
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
    bcl2fastq_flow_cell_id: str,
    dragen_flow_cell_id: str,
    case_id: str,
    helpers: StoreHelpers,
    sample: Sample,
):
    """Test check if all flow cells for samples on a case is on disk."""
    caplog.set_level(logging.DEBUG)
    # GIVEN a store with two flow cell
    flow_cell = helpers.add_flowcell(
        store=base_store, flow_cell_name=bcl2fastq_flow_cell_id, samples=[sample]
    )

    helpers.add_flowcell(store=base_store, flow_cell_name=dragen_flow_cell_id)

    # WHEN fetching the latest flow cell
    is_on_disk = base_store.is_all_flow_cells_on_disk(case_id=case_id)

    # THEN return true
    assert is_on_disk is True

    # THEN log the status of the flow cell
    assert f"{flow_cell.name}: status is {flow_cell.status}" in caplog.text


def test_get_customer_id_from_ticket(analysis_store, customer_id, ticket_id: str):
    """Tests if the function in fact returns the correct customer."""
    # Given a store with a ticket

    # Then the function should return the customer connected to the ticket
    assert analysis_store.get_customer_id_from_ticket(ticket_id) == customer_id


def test_get_latest_ticket_from_case(case_id: str, analysis_store_single_case, ticket_id: str):
    """Tests if the correct ticket is returned for the given case."""
    # GIVEN a populated store with a case

    # WHEN the function is called
    ticket_from_case: str = analysis_store_single_case.get_latest_ticket_from_case(case_id=case_id)

    # THEN the ticket should be correct
    assert ticket_id == ticket_from_case


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


def test_get_case_samples_by_case_id(
    store_with_analyses_for_cases: Store,
    case_id: str,
):
    """Test that getting case-samples by case id returns a list of FamilySamples."""
    # GIVEN a store with case-samples and a case id

    # WHEN fetching the case-samples matching the case id
    case_samples: List[FamilySample] = store_with_analyses_for_cases.get_case_samples_by_case_id(
        case_internal_id=case_id
    )

    # THEN a list of case-samples should be returned
    assert case_samples
    assert isinstance(case_samples, List)
    assert isinstance(case_samples[0], FamilySample)


def test_get_case_sample_link(
    store_with_analyses_for_cases: Store,
    case_id: str,
    sample_id: str,
):
    """Test that the returned element is a FamilySample with the correct case and sample internal ids."""
    # GIVEN a store with case-samples and valid case and sample internal ids

    # WHEN fetching a case-sample with case and sample internal ids
    case_sample: FamilySample = store_with_analyses_for_cases.get_case_sample_link(
        case_internal_id=case_id,
        sample_internal_id=sample_id,
    )

    # THEN the returned element is a FamilySample object
    assert isinstance(case_sample, FamilySample)
    # THEN the returned family sample has the correct case and sample internal ids
    assert case_sample.family.internal_id == case_id
    assert case_sample.sample.internal_id == sample_id


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


def test_verify_case_exists(
    caplog, case_id_with_multiple_samples: str, store_with_multiple_cases_and_samples: Store
):
    """Test validating a case that exists in the database."""

    caplog.set_level(logging.INFO)

    # GIVEN a database containing the case

    # WHEN validating if the case exists
    store_with_multiple_cases_and_samples.verify_case_exists(
        case_internal_id=case_id_with_multiple_samples
    )

    # THEN the case is found
    assert f"Case {case_id_with_multiple_samples} exists in Status DB" in caplog.text


def test_verify_case_exists_with_non_existing_case(
    caplog, case_id_does_not_exist: str, store_with_multiple_cases_and_samples: Store
):
    """Test validating a case that does not exist in the database."""

    # GIVEN a database containing the case

    with pytest.raises(CgError):
        # WHEN validating if the case exists
        store_with_multiple_cases_and_samples.verify_case_exists(
            case_internal_id=case_id_does_not_exist
        )

        # THEN the case is not found
        assert f"Case {case_id_does_not_exist} could not be found in Status DB!" in caplog.text


def test_verify_case_exists_with_no_case_samples(
    caplog, case_id_without_samples: str, store_with_multiple_cases_and_samples: Store
):
    """Test validating a case without samples that exist in the database."""

    # GIVEN a database containing the case

    with pytest.raises(CgError):
        # WHEN validating if the case exists
        store_with_multiple_cases_and_samples.verify_case_exists(
            case_internal_id=case_id_without_samples
        )

        # THEN the case is found, but has no samples
        assert "Case {case_id} has no samples in in Status DB!" in caplog.text


def test_is_case_down_sampled_true(base_store: Store, case: Family, sample_id: str):
    """Tests the down sampling check when all samples are down sampled."""
    # GIVEN a case where all samples are down sampled
    for sample in case.samples:
        sample.from_sample = sample_id
    base_store.session.commit()

    # WHEN checking if all sample in the case are down sampled
    is_down_sampled: bool = base_store.is_case_down_sampled(case_id=case.internal_id)

    # THEN the return value should be True
    assert is_down_sampled


def test_is_case_down_sampled_false(base_store: Store, case: Family, sample_id: str):
    """Tests the down sampling check when none of the samples are down sampled."""
    # GIVEN a case where all samples are not down sampled
    for sample in case.samples:
        assert not sample.from_sample

    # WHEN checking if all sample in the case are down sampled
    is_down_sampled: bool = base_store.is_case_down_sampled(case_id=case.internal_id)

    # THEN the return value should be False
    assert not is_down_sampled


def test_is_case_external_true(
    base_store: Store, case: Family, helpers: StoreHelpers, sample_id: str
):
    """Tests the external case check when all the samples are external."""
    # GIVEN a case where all samples are not external
    external_application_version: ApplicationVersion = helpers.ensure_application_version(
        store=base_store, is_external=True
    )
    for sample in case.samples:
        sample.application_version = external_application_version
    base_store.session.commit()

    # WHEN checking if all sample in the case are external
    is_external: bool = base_store.is_case_external(case_id=case.internal_id)

    # THEN the return value should be False
    assert is_external


def test_is_case_external_false(base_store: Store, case: Family, sample_id: str):
    """Tests the external case check when none of the samples are external."""
    # GIVEN a case where all samples are not external
    for sample in case.samples:
        assert not sample.application_version.application.is_external

    # WHEN checking if all sample in the case are external
    is_external: bool = base_store.is_case_external(case_id=case.internal_id)

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


def test_get_case_by_name_and_customer_case_found(store_with_multiple_cases_and_samples: Store):
    """Test that a case can be found by customer and case name."""
    # GIVEN a database with multiple cases for a customer
    case: Family = store_with_multiple_cases_and_samples._get_query(table=Family).first()
    customer: Customer = store_with_multiple_cases_and_samples._get_query(table=Customer).first()

    assert case.customer == customer

    # WHEN fetching a case by customer and case name
    filtered_case: Family = store_with_multiple_cases_and_samples.get_case_by_name_and_customer(
        customer=customer,
        case_name=case.name,
    )

    # THEN the correct case should be returned
    assert filtered_case is not None
    assert filtered_case.customer_id == customer.id
    assert filtered_case.name == case.name


def test_get_cases_not_analysed_by_sample_internal_id_empty_query(
    store_with_multiple_cases_and_samples: Store, non_existent_id: str
):
    """Test that an empty query is returned if no cases match the sample internal id."""
    # GIVEN a store
    # WHEN getting cases not analysed by the sample internal id
    cases = store_with_multiple_cases_and_samples.get_not_analysed_cases_by_sample_internal_id(
        sample_internal_id=non_existent_id
    )

    # THEN an empty list should be returned
    assert cases == []


def test_get_cases_not_analysed_by_sample_internal_id_multiple_cases(
    store_with_multiple_cases_and_samples: Store,
    sample_id_in_multiple_cases: str,
):
    """Test that multiple cases are returned when more than one case matches the sample internal id."""
    # GIVEN a store with multiple cases having the same sample internal id
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Family)

    # Set all cases to not analysed and HOLD action
    for case in cases_query.all():
        case.action = CaseActions.HOLD

    # WHEN getting cases not analysed by the shared sample internal id
    cases = store_with_multiple_cases_and_samples.get_not_analysed_cases_by_sample_internal_id(
        sample_id_in_multiple_cases
    )

    # THEN multiple cases should be returned
    assert len(cases) > 1

    # Check that all returned cases have the matching sample and are not analysed
    for case in cases:
        assert not case.analyses
        assert any(sample.internal_id == sample_id_in_multiple_cases for sample in case.samples)


def test_get_total_read_counts(
    store_with_sequencing_metrics: Store, sample_id: str, expected_total_reads: int
):
    # GIVEN a store with sequencing metrics

    # WHEN getting total read counts for a sample
    total_reads_count: int = (
        store_with_sequencing_metrics.get_number_of_reads_for_sample_passing_q30_threshold(
            sample_internal_id=sample_id, q30_threshold=0
        )
    )

    # THEN assert that the total read count is correct
    assert total_reads_count == expected_total_reads


def test_get_metrics_entry_by_flow_cell_name_sample_internal_id_and_lane(
    store_with_sequencing_metrics: Store, sample_id: str, flow_cell_name: str, lane: int = 1
):
    # GIVEN a store with sequencing metrics

    # WHEN getting a metrics entry by flow cell name, sample internal id and lane
    metrics_entry: SampleLaneSequencingMetrics = store_with_sequencing_metrics.get_metrics_entry_by_flow_cell_name_sample_internal_id_and_lane(
        sample_internal_id=sample_id, flow_cell_name=flow_cell_name, lane=lane
    )

    assert metrics_entry is not None
    assert metrics_entry.flow_cell_name == flow_cell_name
    assert metrics_entry.flow_cell_lane_number == lane
    assert metrics_entry.sample_internal_id == sample_id


def test_get_number_of_reads_for_sample_passing_q30_threshold(
    store_with_sequencing_metrics: Store,
    sample_id: str,
):
    # GIVEN a store with sequencing metrics
    metrics: Query = store_with_sequencing_metrics._get_query(table=SampleLaneSequencingMetrics)

    # GIVEN a metric for a specific sample
    sample_metric: Optional[SampleLaneSequencingMetrics] = metrics.filter(
        SampleLaneSequencingMetrics.sample_internal_id == sample_id
    ).first()
    assert sample_metric

    # GIVEN a Q30 threshold that the sample will pass
    q30_threshold = int(sample_metric.sample_base_fraction_passing_q30 / 2 * 100)

    # WHEN getting the number of reads for the sample that pass the Q30 threshold
    number_of_reads: int = (
        store_with_sequencing_metrics.get_number_of_reads_for_sample_passing_q30_threshold(
            sample_internal_id=sample_id, q30_threshold=q30_threshold
        )
    )

    # THEN assert that the number of reads is an integer
    assert isinstance(number_of_reads, int)

    # THEN assert that the number of reads is at least the number of reads in the lane for the sample passing the q30
    assert number_of_reads >= sample_metric.sample_total_reads_in_lane


def test_get_number_of_reads_for_sample_with_some_not_passing_q30_threshold(
    store_with_sequencing_metrics: Store, sample_id: str
):
    # GIVEN a store with sequencing metrics
    metrics: Query = store_with_sequencing_metrics._get_query(table=SampleLaneSequencingMetrics)

    # GIVEN a metric for a specific sample
    sample_metrics: List[SampleLaneSequencingMetrics] = metrics.filter(
        SampleLaneSequencingMetrics.sample_internal_id == sample_id
    ).all()

    assert sample_metrics

    # GIVEN a Q30 threshold that some of the sample's metrics will not pass
    q30_values = [int(metric.sample_base_fraction_passing_q30 * 100) for metric in sample_metrics]
    q30_threshold = sorted(q30_values)[len(q30_values) // 2]  # This is the median

    # WHEN getting the number of reads for the sample that pass the Q30 threshold
    number_of_reads: int = (
        store_with_sequencing_metrics.get_number_of_reads_for_sample_passing_q30_threshold(
            sample_internal_id=sample_id, q30_threshold=q30_threshold
        )
    )

    # THEN assert that the number of reads is less than the total number of reads for the sample
    total_sample_reads = sum([metric.sample_total_reads_in_lane for metric in sample_metrics])
    assert number_of_reads < total_sample_reads


def test_get_sample_lane_sequencing_metrics_by_flow_cell_name(
    store_with_sequencing_metrics: Store, flow_cell_name: str
):
    # GIVEN a store with sequencing metrics

    # WHEN getting sequencing metrics for a flow cell
    metrics: List[
        SampleLaneSequencingMetrics
    ] = store_with_sequencing_metrics.get_sample_lane_sequencing_metrics_by_flow_cell_name(
        flow_cell_name=flow_cell_name
    )

    # THEN assert that the metrics are returned
    assert metrics
    for metric in metrics:
        assert metric.flow_cell_name == flow_cell_name
