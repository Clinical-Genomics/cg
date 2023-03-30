"""This script tests the cli methods to add families to status-db"""
from datetime import datetime, timedelta

from cg.constants import CASE_ACTIONS, DataDelivery, Pipeline
from cg.store import Store
from cg.store.models import Analysis
from cg.constants import Priority


def test_delivered_at_affects_tat(store: Store, helpers):
    """test that the estimated turnaround time is affected by the delivered_at date"""

    # GIVEN a database with a case and a samples receive_at, prepared_at, sequenced_at,
    # delivered_at one week ago
    new_case = add_case(helpers, store, ordered_days_ago=7)
    one_week_ago = datetime.now() - timedelta(days=7)
    one_week_old_sample = helpers.add_sample(
        store,
        ordered_at=one_week_ago,
        received_at=one_week_ago,
        prepared_at=one_week_ago,
        sequenced_at=one_week_ago,
        delivered_at=one_week_ago,
    )
    store.relate_sample(new_case, one_week_old_sample, "unknown")

    # WHEN getting active cases
    cases = store.cases()

    # THEN TAT should be R-D = 0 = 0
    assert cases
    for case in cases:
        assert case.get("tat") == 0


def test_sequenced_at_affects_tat(store: Store, helpers):
    """test that the estimated turnaround time is affected by the sequenced_at date"""

    # GIVEN a database with a case and a samples receive_at, prepared_at, sequenced_at one week
    # ago
    new_case = add_case(helpers, store, ordered_days_ago=7)
    one_week_ago = datetime.now() - timedelta(days=7)
    one_week_old_sample = helpers.add_sample(
        store,
        ordered_at=one_week_ago,
        received_at=one_week_ago,
        prepared_at=one_week_ago,
        sequenced_at=one_week_ago,
    )
    store.relate_sample(new_case, one_week_old_sample, "unknown")

    # WHEN getting active cases
    cases = store.cases()

    # THEN TAT should be R-P + P-S + S-A + A-U + U-D = 0 + 0 + 7 + 1 + 2 = 10
    assert cases
    for case in cases:
        assert case.get("tat") == 10


def test_prepared_at_affects_tat(store: Store, helpers):
    """test that the estimated turnaround time is affected by the prepared_at date"""

    # GIVEN a database with a case and a samples receive_at, prepared_at one week ago
    new_case = add_case(helpers, store, ordered_days_ago=7)
    one_week_ago = datetime.now() - timedelta(days=7)
    one_week_old_sample = helpers.add_sample(
        store,
        ordered_at=one_week_ago,
        received_at=one_week_ago,
        prepared_at=one_week_ago,
    )
    store.relate_sample(new_case, one_week_old_sample, "unknown")

    # WHEN getting active cases
    cases = store.cases()

    # THEN TAT should be R-P + P-S + S-A + A-U + U-D = 0 + 7 + 4 + 1 + 2 = 14
    assert cases
    for case in cases:
        assert case.get("tat") == 14


def test_received_at_affects_tat(store: Store, helpers):
    """test that the estimated turnaround time is affected by the received_at date"""

    # GIVEN a database with a case and a samples received one week ago
    new_case = add_case(helpers, store, ordered_days_ago=7)
    one_week_ago = datetime.now() - timedelta(days=7)
    one_week_old_sample = helpers.add_sample(
        store,
        ordered_at=one_week_ago,
        received_at=one_week_ago,
    )
    store.relate_sample(new_case, one_week_old_sample, "unknown")

    # WHEN getting active cases
    cases = store.cases()

    # THEN TAT should be R-P + P-S + S-A + A-U + U-D = 7 + 5 + 4 + 1 + 2 = 19
    assert cases
    for case in cases:
        assert case.get("tat") == 19


def test_samples_flowcell(store: Store, helpers):
    """Test to that cases displays the flowcell status"""

    # GIVEN a database with a case with a sample that belongs to a flowcell with status ondisk
    # and a sample not yet on a flowcell
    new_case = add_case(helpers, store)
    sample_on_flowcell = helpers.add_sample(store)
    flowcell = helpers.add_flowcell(store, status="ondisk", samples=[sample_on_flowcell])
    store.relate_sample(new_case, sample_on_flowcell, "unknown")
    sample_not_on_flowcell = helpers.add_sample(store)
    store.relate_sample(new_case, sample_not_on_flowcell, "unknown")

    # WHEN getting active cases
    cases = store.cases()

    # THEN cases should contain info on flowcell status and be false
    assert cases
    for case in cases:
        assert flowcell.status in case.get("flowcells_status")
        assert not case.get("flowcells_on_disk_bool")
        assert case.get("flowcells_on_disk") == 1


def test_sample_flowcell(store: Store, helpers):
    """Test to that cases displays the flowcell status"""

    # GIVEN a database with a case with a sample that belongs to a flowcell with status ondisk
    new_case = add_case(helpers, store)
    sample = helpers.add_sample(store)
    store.relate_sample(new_case, sample, "unknown")
    flowcell = helpers.add_flowcell(store, status="ondisk", samples=[sample])
    assert flowcell.status

    # WHEN getting active cases
    cases = store.cases()

    # THEN cases should contain info on flowcell status and be true
    assert cases
    for case in cases:
        assert case.get("flowcells_on_disk") == 1
        assert case.get("flowcells_status") == flowcell.status
        assert case.get("flowcells_on_disk_bool")


def test_case_action(store: Store, helpers):
    """Test that case action is fetched by cases() method"""

    # GIVEN a database with an analysis that was completed but has an active rerun in progress
    analysis = helpers.add_analysis(store, completed_at=datetime.now(), uploaded_at=datetime.now())
    analysis.family.action = "analyze"

    # WHEN getting active cases
    cases = store.cases()

    # THEN cases should contain info on analysis (case) action
    assert cases
    for case in cases:
        assert case.get("case_action") == analysis.family.action


def test_analysis_dates_for_rerun(store: Store, helpers):
    """Test to that cases displays no analysis dates for active reruns"""

    # GIVEN a database with an analysis that was completed but has an active rerun in progress
    analysis = helpers.add_analysis(store, completed_at=datetime.now(), uploaded_at=datetime.now())
    analysis.family.action = "analyze"

    # WHEN getting active cases
    cases = store.cases()

    # THEN cases should not contain info on completed and uploaded occasion
    assert cases
    for case in cases:
        assert case.get("analysis_completed_at") is None
        assert case.get("analysis_uploaded_at") is None


def test_received_at_is_newest_date(store: Store, helpers):
    """Test to that cases displays newest received date"""

    # GIVEN a database with a case and two samples with different received dates
    new_case = add_case(helpers, store)
    yesterday = datetime.now() - timedelta(days=1)
    yesteryear = datetime.now() - timedelta(days=365)
    newest_sample = helpers.add_sample(store, received_at=yesterday)
    oldest_sample = helpers.add_sample(store, received_at=yesteryear)
    store.relate_sample(new_case, newest_sample, "unknown")
    store.relate_sample(new_case, oldest_sample, "unknown")

    # WHEN getting active cases
    cases = store.cases()

    # THEN cases should contain the date the samples were most recently received
    assert cases
    for case in cases:
        assert case.get("samples_received_at").date() == newest_sample.received_at.date()


def test_prepared_at_is_newest_date(store: Store, helpers):
    """Test to that cases displays newest prepared date"""

    # GIVEN a database with a case and two samples with different prepared dates
    new_case = add_case(helpers, store)
    yesterday = datetime.now() - timedelta(days=1)
    yesteryear = datetime.now() - timedelta(days=365)
    newest_sample = helpers.add_sample(store, prepared_at=yesterday)
    oldest_sample = helpers.add_sample(store, prepared_at=yesteryear)
    store.relate_sample(new_case, newest_sample, "unknown")
    store.relate_sample(new_case, oldest_sample, "unknown")

    # WHEN getting active cases
    cases = store.cases()

    # THEN cases should contain the date the samples were most recently prepared
    assert cases
    for case in cases:
        assert case.get("samples_prepared_at").date() == newest_sample.prepared_at.date()


def test_sequenced_at_is_newest_date(store: Store, helpers):
    """Test to that cases displays newest sequenced date"""

    # GIVEN a database with a case and two samples with different sequenced dates
    new_case = add_case(helpers, store)
    yesterday = datetime.now() - timedelta(days=1)
    yesteryear = datetime.now() - timedelta(days=365)
    newest_sample = helpers.add_sample(store, sequenced_at=yesterday)
    oldest_sample = helpers.add_sample(store, sequenced_at=yesteryear)
    store.relate_sample(new_case, newest_sample, "unknown")
    store.relate_sample(new_case, oldest_sample, "unknown")

    # WHEN getting active cases
    cases = store.cases()

    # THEN cases should contain the date the samples were most recently sequenced
    assert cases
    for case in cases:
        assert case.get("samples_sequenced_at").date() == newest_sample.sequenced_at.date()


def test_delivered_at_is_newest_date(store: Store, helpers):
    """Test to that cases displays newest delivered date"""

    # GIVEN a database with a case and two samples with different delivered dates
    new_case = add_case(helpers, store)
    yesterday = datetime.now() - timedelta(days=1)
    yesteryear = datetime.now() - timedelta(days=365)
    newest_sample = helpers.add_sample(store, delivered_at=yesterday)
    oldest_sample = helpers.add_sample(store, delivered_at=yesteryear)
    store.relate_sample(new_case, newest_sample, "unknown")
    store.relate_sample(new_case, oldest_sample, "unknown")

    # WHEN getting active cases
    cases = store.cases()

    # THEN cases should contain the date the samples were most recently delivered
    assert cases
    for case in cases:
        assert case.get("samples_delivered_at").date() == newest_sample.delivered_at.date()


def test_invoiced_at_is_newest_invoice_date(store: Store, helpers):
    """Test to that cases displays newest invoiced date"""

    # GIVEN a database with a case and two samples with different invoiced dates
    new_case = add_case(helpers, store)
    yesterday = datetime.now() - timedelta(days=1)
    yesteryear = datetime.now() - timedelta(days=365)
    newest_sample = helpers.add_sample(store)
    invoice = store.add_invoice(helpers.ensure_customer(store))
    newest_sample.invoice = invoice
    newest_sample.invoice.invoiced_at = yesterday
    oldest_sample = helpers.add_sample(store)
    invoice = store.add_invoice(helpers.ensure_customer(store))
    oldest_sample.invoice = invoice
    oldest_sample.invoice.invoiced_at = yesteryear
    store.relate_sample(new_case, newest_sample, "unknown")
    store.relate_sample(new_case, oldest_sample, "unknown")

    # WHEN getting active cases
    cases = store.cases()

    # THEN cases should contain the date the samples were most recently invoiced
    assert cases
    for case in cases:
        assert case.get("samples_invoiced_at").date() == newest_sample.invoice.invoiced_at.date()


def test_invoiced_at(store: Store, helpers):
    """Test to that cases displays correct invoiced date"""

    # GIVEN a database with a case and a invoiced date
    new_case = add_case(helpers, store)
    sample = helpers.add_sample(store)
    sample.invoice = store.add_invoice(helpers.ensure_customer(store))
    sample.invoice.invoiced_at = datetime.now()
    store.relate_sample(new_case, sample, "unknown")

    # WHEN getting active cases
    cases = store.cases()

    # THEN cases should contain the date the sample was invoiced
    assert cases
    for case in cases:
        assert case.get("samples_invoiced_at").date() == datetime.now().date()


def test_delivered_at(store: Store, helpers):
    """Test to that cases displays correct delivered date"""

    # GIVEN a database with a case and a delivered date
    new_case = add_case(helpers, store)
    sample = helpers.add_sample(store, delivered_at=datetime.now())
    store.relate_sample(new_case, sample, "unknown")

    # WHEN getting active cases
    cases = store.cases()

    # THEN cases should contain the date the sample was delivered
    assert cases
    for case in cases:
        assert case.get("samples_delivered_at").date() == datetime.now().date()


def test_sequenced_at(store: Store, helpers):
    """Test to that cases displays correct sequenced date"""

    # GIVEN a database with a case and a sequenced date
    new_case = add_case(helpers, store)
    sample = helpers.add_sample(store, sequenced_at=datetime.now())
    store.relate_sample(new_case, sample, "unknown")

    # WHEN getting active cases
    cases = store.cases()

    # THEN cases should contain the date the sample was sequenced
    assert cases
    for case in cases:
        assert case.get("samples_sequenced_at").date() == datetime.now().date()


def test_prepared_at(store: Store, helpers):
    """Test to that cases displays correct prepared date"""

    # GIVEN a database with a case and a prepared date
    new_case = add_case(helpers, store)
    sample = helpers.add_sample(store, prepared_at=datetime.now())
    store.relate_sample(new_case, sample, "unknown")

    # WHEN getting active cases
    cases = store.cases()

    # THEN cases should contain the date the sample was prepared
    assert cases
    for case in cases:
        assert case.get("samples_prepared_at").date() == datetime.now().date()


def test_received_at(store: Store, helpers):
    """Test to that cases displays correct received date"""

    # GIVEN a database with a case and a received date
    new_case = add_case(helpers, store)
    sample = helpers.add_sample(store, received_at=datetime.now())
    store.relate_sample(new_case, sample, "unknown")

    # WHEN getting active cases
    cases = store.cases()

    # THEN cases should contain the date the sample was received
    assert cases
    for case in cases:
        assert case.get("samples_received_at").date() == datetime.now().date()


def test_no_invoice_true(store: Store, helpers):
    """Test to that cases displays correct samples to invoice"""

    # GIVEN a database with a case and one no_invoice sample
    new_case = add_case(helpers, store)
    sample = helpers.add_sample(store, no_invoice=True)
    store.relate_sample(new_case, sample, "unknown")
    assert sample.no_invoice

    # WHEN getting active cases
    cases = store.cases()

    # THEN cases should contain zero samples to invoice
    assert cases
    for case in cases:
        assert case.get("samples_to_invoice") == 0


def test_one_no_invoice_false(store: Store, helpers):
    """Test to that cases displays correct samples to invoice"""

    # GIVEN a database with a case and one sample to invoice
    new_case = add_case(helpers, store)
    sample = helpers.add_sample(store, no_invoice=False)
    store.relate_sample(new_case, sample, "unknown")
    assert not sample.no_invoice

    # WHEN getting active cases
    cases = store.cases()

    # THEN cases should contain one sample to invoice
    assert cases
    for case in cases:
        assert case.get("samples_to_invoice") == 1


def test_one_external_sample(store: Store, helpers):
    """Test to that cases displays correct internal/external samples"""

    # GIVEN a database with a case and one external sample
    new_case = add_case(helpers, store)
    sample = helpers.add_sample(store, is_external=True)
    store.relate_sample(new_case, sample, "unknown")
    assert sample.application_version.application.is_external

    # WHEN getting active cases
    cases = store.cases()

    # THEN cases should contain one external and zero internal samples
    assert cases
    for case in cases:
        assert case.get("total_external_samples") == 1
        assert case.get("total_internal_samples") == 0
        assert case.get("case_external_bool")
        assert case.get("samples_to_receive") == 0
        assert case.get("samples_to_prepare") == 0
        assert case.get("samples_to_sequence") == 0


def test_one_internal_sample(store: Store, helpers):
    """Test to that cases displays correct internal/external samples"""

    # GIVEN a database with a case and one external sample
    new_case = add_case(helpers, store)
    sample = helpers.add_sample(store, is_external=False)
    store.relate_sample(new_case, sample, "unknown")
    assert not sample.application_version.application.is_external

    # WHEN getting active cases
    cases = store.cases()

    # THEN cases should contain zero external and one internal samples
    assert cases
    for case in cases:
        assert case.get("total_external_samples") == 0
        assert case.get("total_internal_samples") == 1
        assert case.get("samples_to_receive") == 1
        assert case.get("samples_to_prepare") == 1
        assert case.get("samples_to_sequence") == 1


def test_include_case_by_sample_id(store: Store, helpers):
    """Test to that cases can be included by sample id"""

    # GIVEN a database with a sample with internal_id
    new_case = add_case(helpers, store)
    sample = helpers.add_sample(store)
    store.relate_sample(new_case, sample, "unknown")

    # WHEN getting active cases by sample id
    cases = store.cases(sample_id=sample.internal_id)

    # THEN cases should only contain this case
    assert cases
    for case in cases:
        assert new_case.internal_id in case.get("internal_id")


def test_exclude_case_by_sample_id(store: Store, helpers):
    """Test to that cases can be excluded by sample id"""

    # GIVEN a database with a sample with internal_id
    new_case = add_case(helpers, store)
    sample = helpers.add_sample(store)
    store.relate_sample(new_case, sample, "unknown")

    # WHEN getting active cases by non-existing sample id
    cases = store.cases(sample_id="dummy_id")

    # THEN cases should not contain this case
    assert not cases


def test_include_case_by_exclude_customer(store: Store, helpers):
    """Test to that cases can be excluded by customer"""

    # GIVEN a database with a case and a customer
    customer_id = "cust000"
    new_case = add_case(helpers, store, customer_id=customer_id)

    # WHEN getting active cases by customer
    cases = store.cases(exclude_customer_id="dummy_customer")

    # THEN cases should contain this case
    assert cases
    for case in cases:
        assert new_case.internal_id in case.get("internal_id")


def test_exclude_case_by_exclude_customer(store: Store, helpers):
    """Test to that cases can be excluded by customer"""

    # GIVEN a database with a case and a customer
    customer_id = "cust000"
    add_case(helpers, store, customer_id=customer_id)

    # WHEN getting active cases by customer
    cases = store.cases(exclude_customer_id=customer_id)

    # THEN cases should not contain this case
    assert not cases


def test_include_case_by_case_uppercase_data_analysis(store: Store, helpers):
    """Test to that cases can be included by uppercase data_analysis"""

    # GIVEN a database with a case with data analysis set
    data_analysis = Pipeline.BALSAMIC
    assert str(data_analysis).upper() != str(data_analysis)
    new_case = add_case(helpers, store, data_analysis=data_analysis)
    sample = helpers.add_sample(store)
    store.relate_sample(new_case, sample, "unknown")

    # WHEN getting active cases by data_analysis
    cases = store.cases(data_analysis=new_case.data_analysis.upper())

    # THEN cases should only contain this case
    assert cases
    for case in cases:
        assert new_case.internal_id in case.get("internal_id")


def test_exclude_case_by_data_analysis(store: Store, helpers):
    """Test to that cases can be excluded by data_analysis"""

    # GIVEN a database with a case with data analysis set
    new_case = add_case(helpers, store, data_analysis=Pipeline.BALSAMIC)
    sample = helpers.add_sample(store)
    store.relate_sample(new_case, sample, "unknown")

    # WHEN getting active cases by data_analysis
    cases = store.cases(data_analysis="dummy_analysis")

    # THEN cases should not contain this case
    assert not cases


def test_include_case_by_partial_data_analysis(store: Store, helpers):
    """Test to that cases can be included by data_analysis"""

    # GIVEN a database with a case with data analysis set
    data_analysis = Pipeline.BALSAMIC
    new_case = add_case(helpers, store, data_analysis=data_analysis)
    sample = helpers.add_sample(store)
    store.relate_sample(new_case, sample, "unknown")

    # WHEN getting active cases by partial data_analysis
    cases = store.cases(data_analysis=str(data_analysis)[:-1])

    # THEN cases should only contain this case
    assert cases
    for case in cases:
        assert new_case.internal_id in case.get("internal_id")


def test_show_multiple_data_analysis(store: Store, helpers):
    """Test to that cases can be included by data_analysis"""

    # GIVEN a database with a case with data analysis set
    data_analysis = Pipeline.BALSAMIC
    new_case = add_case(helpers, store, data_analysis=data_analysis)
    sample1 = helpers.add_sample(store)
    store.relate_sample(new_case, sample1, "unknown")
    new_case2 = add_case(helpers, store, case_id="new_case2", data_analysis=data_analysis)
    sample2 = helpers.add_sample(store)
    store.relate_sample(new_case, sample2, "unknown")
    store.relate_sample(new_case2, sample2, "unknown")

    # WHEN getting active cases by data_analysis
    cases = store.cases(data_analysis=str(data_analysis)[:-1])

    # THEN cases should only contain these analyses
    assert cases
    for case in cases:
        assert new_case2.internal_id or new_case.internal_id in case.get("internal_id")


def test_show_data_analysis(store: Store, helpers):
    """Test to that cases can be included by data_analysis"""

    # GIVEN a database with a case with data analysis set
    data_analysis = Pipeline.BALSAMIC
    new_case = add_case(helpers, store, data_analysis=data_analysis)
    sample = helpers.add_sample(store)
    store.relate_sample(new_case, sample, "unknown")

    # WHEN getting active cases by data_analysis
    cases = store.cases(data_analysis=str(data_analysis))

    # THEN cases should only contain this case
    assert cases
    for case in cases:
        assert new_case.internal_id in case.get("internal_id")


def test_include_case_by_data_analysis(store: Store, helpers):
    """Test to that cases can be included by data_analysis"""

    # GIVEN a database with a case with data analysis set
    data_analysis = Pipeline.BALSAMIC
    new_case = add_case(helpers, store, data_analysis=data_analysis)
    sample = helpers.add_sample(store)
    store.relate_sample(new_case, sample, "unknown")

    # WHEN getting active cases by data_analysis
    cases = store.cases(data_analysis=new_case.data_analysis)

    # THEN cases should only contain this case
    assert cases
    for case in cases:
        assert new_case.internal_id in case.get("internal_id")


def test_exclude_case_by_customer(store: Store, helpers):
    """Test to that cases can be excluded by customer"""

    # GIVEN a database with a case and a customer
    add_case(helpers, store, customer_id="cust000")

    # WHEN getting active cases by customer
    cases = store.cases(customer_id="dummy_cust")

    # THEN cases should not contain this case
    assert not cases


def test_include_case_by_customer(store: Store, helpers):
    """Test to that cases can be included by customer"""

    # GIVEN a database with a case
    customer_id = "cust000"
    new_case = add_case(helpers, store, customer_id=customer_id)

    # WHEN getting active cases by customer
    cases = store.cases(customer_id=customer_id)

    # THEN cases should only contain this case
    assert cases
    for case in cases:
        assert new_case.internal_id in case.get("internal_id")


def test_exclude_case_by_name(store: Store, helpers):
    """Test to that cases can be excluded by name"""

    # GIVEN a database with a case
    add_case(helpers, store)

    # WHEN getting active cases by name
    cases = store.cases(name="dummy_name")

    # THEN cases should not contain this case
    assert not cases


def test_include_case_by_partial_name(store: Store, helpers):
    """Test to that cases can be included by name"""

    # GIVEN a database with a case
    new_case = add_case(helpers, store)

    # WHEN getting active cases by partial name
    cases = store.cases(name=new_case.name[1:-1])

    # THEN cases should only contain this case
    assert cases
    for case in cases:
        assert new_case.name in case.get("name")


def test_include_case_by_name(store: Store, helpers):
    """Test to that cases can be included by name"""

    # GIVEN a database with a case
    new_case = add_case(helpers, store)

    # WHEN getting active cases by name
    cases = store.cases(name=new_case.name)

    # THEN cases should only contain this case
    assert cases
    for case in cases:
        assert new_case.name in case.get("name")


def test_excluded_by_priority(store: Store, helpers):
    """Test to that cases can be excluded by priority"""

    # GIVEN a database with a case with a priority
    add_case(helpers, store, priority=Priority.research)

    # WHEN getting active cases by another priority
    cases = store.cases(priority=Priority.standard)

    # THEN cases should not contain this case
    assert not cases


def test_included_by_priority(store: Store, helpers):
    """Test to that cases can be included by priority"""

    # GIVEN a database with a case with a priority
    new_case = add_case(helpers, store, priority=Priority.research)

    # WHEN getting active cases by priority
    cases = store.cases(priority=new_case.priority)

    # THEN cases should only contain this case
    assert cases
    for case in cases:
        assert new_case.internal_id in case.get("internal_id")


def test_excluded_by_action(store: Store, helpers):
    """Test to that cases can be excluded by action"""

    # GIVEN a database with a case with an action
    add_case(helpers, store, action=CASE_ACTIONS[0])

    # WHEN getting active cases by action
    cases = store.cases(case_action=CASE_ACTIONS[1])

    # THEN cases should not contain this case
    assert not cases


def test_included_by_action(store: Store, helpers):
    """Test to that cases can be included by action"""

    # GIVEN a database with a case with an action
    new_case = add_case(helpers, store, action=CASE_ACTIONS[0])

    # WHEN getting active cases by action
    cases = store.cases(case_action=new_case.action)

    # THEN cases should only contain this case
    assert cases
    for case in cases:
        assert new_case.internal_id in case.get("internal_id")


def test_exclude_case_by_internal_id(store: Store, helpers):
    """Test to that cases can be excluded by internal_id"""

    # GIVEN a database with a case
    add_case(helpers, store)

    # WHEN getting active cases by internal_id
    cases = store.cases(internal_id="dummy_id")

    # THEN cases should not contain this case
    assert not cases


def test_include_case_by_partial_internal_id(store: Store, helpers):
    """Test to that cases can be included by internal_id"""

    # GIVEN a database with a case
    new_case = add_case(helpers, store)

    # WHEN getting active cases by partial internal_id
    cases = store.cases(internal_id=new_case.internal_id[1:-1])

    # THEN cases should only contain this case
    assert cases
    for case in cases:
        assert new_case.internal_id in case.get("internal_id")


def test_include_case_by_internal_id(store: Store, helpers):
    """Test to that cases can be included by internal_id"""

    # GIVEN a database with a case
    new_case = add_case(helpers, store)

    # WHEN getting active cases by internal_id
    cases = store.cases(internal_id=new_case.internal_id)

    # THEN cases should only contain this case
    assert cases
    for case in cases:
        assert new_case.internal_id in case.get("internal_id")


def test_only_prepared_cases(store: Store, helpers):
    """Test to that sequenced cases can be included"""

    # GIVEN a database with an prepared case
    new_case = add_case(helpers, store)
    sample = helpers.add_sample(store, prepared_at=datetime.now())
    store.relate_sample(new_case, sample, "unknown")
    neg_new_case = add_case(helpers, store, "neg_new_case")
    neg_sample = helpers.add_sample(store, name="neg_sample")
    store.relate_sample(neg_new_case, neg_sample, "unknown")

    # WHEN getting active cases excluding prepared
    cases = store.cases(only_prepared=True)

    # THEN cases should only contain the prepared case
    assert cases
    for case in cases:
        assert new_case.internal_id in case.get("internal_id")


def test_only_received_cases(store: Store, helpers):
    """Test to that sequenced cases can be included"""

    # GIVEN a database with an received case
    new_case = add_case(helpers, store)
    sample = helpers.add_sample(store, received_at=datetime.now())
    store.relate_sample(new_case, sample, "unknown")
    neg_new_case = add_case(helpers, store, "neg_new_case")
    neg_sample = helpers.add_sample(store, name="neg_sample")
    store.relate_sample(neg_new_case, neg_sample, "unknown")

    # WHEN getting active cases excluding received
    cases = store.cases(only_received=True)

    # THEN cases should only contain the received case
    assert cases
    for case in cases:
        assert new_case.internal_id in case.get("internal_id")


def test_only_sequenced_cases(store: Store, helpers):
    """Test to that sequenced cases can be included"""

    # GIVEN a database with an sequenced case
    new_case = add_case(helpers, store)
    sample = helpers.add_sample(store, sequenced_at=datetime.now())
    store.relate_sample(new_case, sample, "unknown")
    neg_new_case = add_case(helpers, store, "neg_new_case")
    neg_sample = helpers.add_sample(store, name="neg_sample")
    store.relate_sample(neg_new_case, neg_sample, "unknown")

    # WHEN getting active cases excluding sequenced
    cases = store.cases(only_sequenced=True)

    # THEN cases should only contain the sequenced case
    assert cases
    for case in cases:
        assert new_case.internal_id in case.get("internal_id")


def test_only_delivered_cases(store: Store, helpers):
    """Test to that delivered cases can be included"""

    # GIVEN a database with an delivered case
    new_case = add_case(helpers, store)
    sample = helpers.add_sample(store, delivered_at=datetime.now())
    store.relate_sample(new_case, sample, "unknown")
    neg_new_case = add_case(helpers, store, "neg_new_case")
    neg_sample = helpers.add_sample(store, name="neg_sample")
    store.relate_sample(neg_new_case, neg_sample, "unknown")

    # WHEN getting active cases excluding delivered
    cases = store.cases(only_delivered=True)

    # THEN cases should only contain the delivered case
    assert cases
    for case in cases:
        assert new_case.internal_id in case.get("internal_id")


def test_only_uploaded_cases(store: Store, helpers):
    """Test to that uploaded cases can be included"""

    # GIVEN a database with an uploaded analysis
    helpers.add_analysis(store, uploaded_at=datetime.now())
    neg_new_case = add_case(helpers, store, "neg_new_case")
    neg_sample = helpers.add_sample(store, name="neg_sample")
    store.relate_sample(neg_new_case, neg_sample, "unknown")

    # WHEN getting active cases excluding uploaded
    cases = store.cases(only_uploaded=True)

    # THEN cases should only contain the uploaded case
    assert cases
    for case in cases:
        assert neg_new_case.internal_id not in case.get("internal_id")


def test_only_delivery_reported_cases(store: Store, helpers):
    """Test to that delivery-reported cases can be included"""

    # GIVEN a database with an delivery-reported analysis
    helpers.add_analysis(store, delivery_reported_at=datetime.now())
    neg_new_case = add_case(helpers, store, "neg_new_case")
    neg_sample = helpers.add_sample(store, name="neg_sample")
    store.relate_sample(neg_new_case, neg_sample, "unknown")

    # WHEN getting active cases excluding delivery_reported
    cases = store.cases(only_delivery_reported=True)

    # THEN cases should only contain the delivery-reported case
    assert cases
    for case in cases:
        assert neg_new_case.internal_id not in case.get("internal_id")


def test_only_invoiced_cases(store: Store, helpers):
    """Test to that invoiced cases can be included"""

    # GIVEN a database with an invoiced case
    new_case = add_case(helpers, store)
    sample = helpers.add_sample(store)
    sample.invoice = store.add_invoice(helpers.ensure_customer(store))
    sample.invoice.invoiced_at = datetime.now()
    store.relate_sample(new_case, sample, "unknown")
    neg_new_case = add_case(helpers, store, "neg_new_case")
    neg_sample = helpers.add_sample(store, name="neg_sample")
    store.relate_sample(neg_new_case, neg_sample, "unknown")

    # WHEN getting active cases excluding invoiced
    cases = store.cases(only_invoiced=True)

    # THEN cases should only contain the invoiced case
    assert cases
    for case in cases:
        assert new_case.internal_id in case.get("internal_id")


def test_only_analysed_cases(store: Store, helpers):
    """Test to that analysed cases can be included"""

    # GIVEN a database with a completed analysis
    helpers.add_analysis(store, completed_at=datetime.now())
    neg_new_case = add_case(helpers, store, "neg_new_case")
    neg_sample = helpers.add_sample(store, name="neg_sample")
    store.relate_sample(neg_new_case, neg_sample, "unknown")

    # WHEN getting active cases excluding not analysed
    cases = store.cases(only_analysed=True)

    # THEN cases should only contain the completed case
    assert cases
    for case in cases:
        assert neg_new_case.internal_id not in case.get("internal_id")


def test_exclude_prepared_cases(store: Store, helpers):
    """Test to that sequenced cases can be excluded"""

    # GIVEN a database with an prepared case
    new_case = add_case(helpers, store)
    sample = helpers.add_sample(store, prepared_at=datetime.now())
    store.relate_sample(new_case, sample, "unknown")

    # WHEN getting active cases excluding prepared
    cases = store.cases(exclude_prepared=True)

    # THEN cases should not contain the prepared case
    assert not cases


def test_exclude_received_cases(store: Store, helpers):
    """Test to that sequenced cases can be excluded"""

    # GIVEN a database with an received case
    new_case = add_case(helpers, store)
    sample = helpers.add_sample(store, received_at=datetime.now())
    store.relate_sample(new_case, sample, "unknown")

    # WHEN getting active cases excluding received
    cases = store.cases(exclude_received=True)

    # THEN cases should not contain the received case
    assert not cases


def test_exclude_sequenced_cases(store: Store, helpers):
    """Test to that sequenced cases can be excluded"""

    # GIVEN a database with an sequenced case
    new_case = add_case(helpers, store)
    sample = helpers.add_sample(store, sequenced_at=datetime.now())
    store.relate_sample(new_case, sample, "unknown")

    # WHEN getting active cases excluding sequenced
    cases = store.cases(exclude_sequenced=True)

    # THEN cases should not contain the sequenced case
    assert not cases


def test_exclude_delivered_cases(store: Store, helpers):
    """Test to that delivered cases can be excluded"""

    # GIVEN a database with an delivered case
    new_case = add_case(helpers, store)
    sample = helpers.add_sample(store, delivered_at=datetime.now())
    store.relate_sample(new_case, sample, "unknown")

    # WHEN getting active cases excluding delivered
    cases = store.cases(exclude_delivered=True)

    # THEN cases should not contain the delivered case
    assert not cases


def test_exclude_uploaded_cases(store: Store, helpers):
    """Test to that uploaded cases can be excluded"""

    # GIVEN a database with an uploaded analysis
    helpers.add_analysis(store, uploaded_at=datetime.now())

    # WHEN getting active cases excluding uploaded
    cases = store.cases(exclude_uploaded=True)

    # THEN cases should not contain the uploaded case
    assert not cases


def test_exclude_delivery_reported_cases(store: Store, helpers):
    """Test to that delivery-reported cases can be excluded"""

    # GIVEN a database with an delivery-reported analysis
    helpers.add_analysis(store, delivery_reported_at=datetime.now())

    # WHEN getting active cases excluding delivery-reported
    cases = store.cases(exclude_delivery_reported=True)

    # THEN cases should not contain the delivery-reported case
    assert not cases


def test_exclude_invoiced_cases(store: Store, helpers):
    """Test to that invoiced cases can be excluded"""

    # GIVEN a database with an invoiced case
    new_case = add_case(helpers, store)
    sample = helpers.add_sample(store)
    sample.invoice = store.add_invoice(helpers.ensure_customer(store))
    sample.invoice.invoiced_at = datetime.now()
    store.relate_sample(new_case, sample, "unknown")

    # WHEN getting active cases excluding invoiced
    cases = store.cases(exclude_invoiced=True)

    # THEN cases should not contain the invoiced case
    assert not cases


def test_exclude_analysed_cases(store: Store, helpers):
    """Test to that analysed cases can be excluded"""

    # GIVEN a database with a completed analysis
    helpers.add_analysis(store, completed_at=datetime.now())

    # WHEN getting active cases excluding analysed
    cases = store.cases(exclude_analysed=True)

    # THEN cases should not contain the completed case
    assert not cases


def test_all_days(store: Store, helpers):
    """Test to that cases filter in case in database"""

    # GIVEN a database with a really old case
    new_case = add_case(helpers, store, ordered_days_ago=9999)

    # WHEN getting active cases with days = all
    cases = store.cases(days=0)

    # THEN cases should contain the case
    assert cases
    for case in cases:
        assert new_case.internal_id in case.get("internal_id")


def test_new_case_included(store: Store, helpers):
    """Test to that cases filter in case from database"""

    # GIVEN a database with a case
    new_case = add_case(helpers, store, ordered_days_ago=1)

    # WHEN getting active cases not older than two days
    result_cases = store.cases(days=2)

    # THEN cases should contain the case
    assert result_cases
    for case in result_cases:
        assert new_case.internal_id in case.get("internal_id")


def test_old_case_not_included(store: Store, helpers):
    """Test to that cases filter out old case in database"""

    # GIVEN a database with a case
    add_case(helpers, store, ordered_days_ago=2)

    # WHEN getting active cases not older than one day
    cases = store.cases(days=1)

    # THEN cases should not contain the case
    assert not cases


def test_analysis_bool_true(store: Store, helpers):
    """Test to that cases displays correct booleans for samples"""

    # GIVEN a database with a case
    helpers.add_analysis(store, completed_at=datetime.now(), uploaded_at=datetime.now())

    # WHEN getting active cases
    cases = store.cases()

    # THEN cases should contain true for all analysis booleans
    assert cases
    for case in cases:
        assert case.get("analysis_completed_bool") is True
        assert case.get("analysis_uploaded_bool") is True


def test_samples_bool_true(store: Store, helpers):
    """Test to that cases displays correct booleans for samples"""

    # GIVEN sample that is received, prepared, sequenced and delivered
    new_case = add_case(helpers, store)
    sample = helpers.add_sample(
        store,
        received_at=datetime.now(),
        prepared_at=datetime.now(),
        sequenced_at=datetime.now(),
        delivered_at=datetime.now(),
    )
    assert sample.received_at
    assert sample.prepared_at
    assert sample.sequenced_at
    assert sample.delivered_at
    sample.invoice = store.add_invoice(helpers.ensure_customer(store))
    sample.invoice.invoiced_at = datetime.now()
    store.relate_sample(new_case, sample, "unknown")

    # WHEN getting active cases
    cases = store.cases()

    # THEN cases should contain true for all sample booleans
    assert cases
    for case in cases:
        assert case.get("samples_received_bool") is True
        assert case.get("samples_prepared_bool") is True
        assert case.get("samples_sequenced_bool") is True
        assert case.get("samples_delivered_bool") is True
        assert case.get("samples_invoiced_bool") is True


def test_bool_false(store: Store, helpers):
    """Test to that cases displays correct received samples"""

    # GIVEN a database with a case
    new_case = add_case(helpers, store)
    sample = helpers.add_sample(store)
    store.relate_sample(new_case, sample, "unknown")

    # WHEN getting active cases
    cases = store.cases()

    # THEN cases should contain false for all booleans
    assert cases
    for case in cases:
        assert case.get("samples_received_bool") is False
        assert case.get("samples_prepared_bool") is False
        assert case.get("samples_sequenced_bool") is False
        assert case.get("analysis_completed_bool") is False
        assert case.get("analysis_uploaded_bool") is False
        assert case.get("samples_delivered_bool") is False
        assert case.get("samples_invoiced_bool") is False


def test_one_invoiced_sample(store: Store, helpers):
    """Test to that cases displays correct invoiced samples"""

    # GIVEN a database with a case with an invoiced sample
    new_case = add_case(helpers, store)
    sample = helpers.add_sample(store)

    sample.invoice = store.add_invoice(helpers.ensure_customer(store))
    sample.invoice.invoiced_at = datetime.now()

    store.relate_sample(new_case, sample, "unknown")
    assert sample.invoice is not None

    # WHEN getting active cases
    cases = store.cases()

    # THEN cases should contain number of invoiced samples
    assert cases
    for case in cases:
        assert case.get("samples_invoiced") == 1


def test_analysis_uploaded_at(store: Store, helpers):
    """Test to that cases displays when uploaded"""

    # GIVEN a database with an analysis that was uploaded
    analysis = helpers.add_analysis(store, uploaded_at=datetime.now())
    assert analysis.uploaded_at is not None

    # WHEN getting active cases
    cases = store.cases()

    # THEN cases should contain info on upload occasion
    assert cases
    for case in cases:
        assert case.get("analysis_uploaded_at") is not None


def test_analysis_pipeline(store: Store, helpers):
    """Test to that cases displays pipeline"""

    # GIVEN a database with an analysis that has pipeline
    pipeline = Pipeline.BALSAMIC
    analysis = helpers.add_analysis(store, pipeline=pipeline)
    assert analysis.pipeline is not None

    # WHEN getting active cases
    cases = store.cases()

    # THEN cases should contain info on pipeline
    assert cases
    for case in cases:
        assert case.get("analysis_pipeline") == str(pipeline)


def test_samples_delivered(store: Store, helpers):
    """Test to that cases displays when they were delivered"""

    # GIVEN a database with a sample that is delivered
    new_case = add_case(helpers, store)
    sample = helpers.add_sample(store, delivered_at=datetime.now())
    store.relate_sample(new_case, sample, "unknown")
    assert sample.delivered_at is not None

    # WHEN getting active cases
    cases = store.cases()

    # THEN cases should contain info on delivered occasion
    assert cases
    for case in cases:
        assert case.get("samples_delivered") == 1


def test_analysis_completed_at(store: Store, helpers):
    """Test to that cases displays when they were completed"""

    # GIVEN a database with an analysis that is completed
    analysis = helpers.add_analysis(store, completed_at=datetime.now())
    assert analysis.completed_at is not None
    assert store.families().count() == 1
    assert store._get_query(table=Analysis).count() == 1

    # WHEN getting active cases
    cases = store.cases()

    # THEN cases should contain info on completion occasion
    assert cases
    for case in cases:
        assert case.get("analysis_completed_at") is not None


def test_case_ordered_date(store: Store, helpers):
    """Test to that cases displays when they were ordered"""

    # GIVEN a database with a case without samples and no analyses
    new_case = add_case(helpers, store)
    assert new_case.ordered_at is not None

    # WHEN getting active cases
    cases = store.cases()

    # THEN cases should contain info on order occasion
    assert cases
    for case in cases:
        assert case.get("ordered_at") is not None


def test_one_of_two_samples_received(store: Store, helpers):
    """Test to that cases displays correct received samples"""

    # GIVEN a database with a case with a received sample and one not received
    new_case = add_case(helpers, store)
    sample_received = helpers.add_sample(store, "sample_received", received_at=datetime.now())
    sample_not_received = helpers.add_sample(store, "sample_not_received", received_at=None)
    store.relate_sample(new_case, sample_received, "unknown")
    store.relate_sample(new_case, sample_not_received, "unknown")
    assert sample_received.received_at is not None
    assert sample_not_received.received_at is None

    # WHEN getting active cases
    cases = store.cases()

    # THEN cases should contain number of received samples
    assert cases
    for case in cases:
        assert case.get("total_samples") == 2
        assert case.get("samples_received") == 1


def test_one_sequenced_sample(store: Store, helpers):
    """Test to that cases displays correct sequenced samples"""

    # GIVEN a database with a case with a sequenced sample
    new_case = add_case(helpers, store)
    sample = helpers.add_sample(store, sequenced_at=datetime.now())
    store.relate_sample(new_case, sample, "unknown")
    assert sample.sequenced_at is not None

    # WHEN getting active cases
    cases = store.cases()

    # THEN cases should contain number of sequenced samples
    assert cases
    for case in cases:
        assert case.get("samples_sequenced") == 1


def test_one_prepared_sample(store: Store, helpers):
    """Test to that cases displays correct prepared samples"""

    # GIVEN a database with a case
    new_case = add_case(helpers, store)
    sample = helpers.add_sample(store, prepared_at=datetime.now())
    store.relate_sample(new_case, sample, "unknown")
    assert sample.prepared_at is not None

    # WHEN getting active cases
    cases = store.cases()

    # THEN cases should contain number of prepared samples
    assert cases
    for case in cases:
        assert case.get("samples_prepared") == 1


def test_one_received_sample(store: Store, helpers):
    """Test to that cases displays correct received samples"""

    # GIVEN a database with a case
    new_case = add_case(helpers, store)
    sample = helpers.add_sample(store, received_at=datetime.now())
    store.relate_sample(new_case, sample, "unknown")
    assert sample.received_at is not None

    # WHEN getting active cases
    cases = store.cases()

    # THEN cases should contain number of received samples
    assert cases
    for case in cases:
        assert case.get("samples_received") == 1


def test_one_sample(store: Store, helpers):
    """Test to that cases displays correct total samples"""

    # GIVEN a database with a case
    new_case = add_case(helpers, store)
    sample = helpers.add_sample(store)
    store.relate_sample(new_case, sample, "unknown")
    assert sample.received_at is None
    assert sample.prepared_at is None
    assert sample.delivered_at is None
    assert sample.sequenced_at is None

    # WHEN getting active cases
    cases = store.cases()

    # THEN cases should contain the sample
    assert cases
    for case in cases:
        assert case.get("total_samples") == 1
        assert case.get("samples_received") == 0
        assert case.get("samples_prepared") == 0
        assert case.get("samples_sequenced") == 0
        assert case.get("samples_delivered") == 0
        assert case.get("samples_invoiced") == 0


def test_case_without_samples(store: Store, helpers):
    """Test to that cases displays correct number samples"""

    # GIVEN a database with a case without samples and no analyses
    new_case = add_case(helpers, store)
    assert not new_case.links
    assert not new_case.analyses

    # WHEN getting active cases
    cases = store.cases()

    # THEN cases should contain zero samples and no analysis info
    assert cases
    for case in cases:
        assert case.get("total_samples") == 0
        assert case.get("samples_received") is None
        assert case.get("samples_prepared") is None
        assert case.get("samples_sequenced") is None
        assert case.get("analysis_completed_at") is None
        assert case.get("analysis_pipeline") is None
        assert case.get("analysis_uploaded_at") is None
        assert case.get("samples_delivered") is None
        assert case.get("samples_invoiced") is None
        assert case.get("samples_received_bool") is None
        assert case.get("samples_prepared_bool") is None
        assert case.get("samples_sequenced_bool") is None
        assert case.get("analysis_completed_bool") is None
        assert case.get("analysis_uploaded_bool") is None
        assert case.get("samples_delivered_bool") is None
        assert case.get("samples_invoiced_bool") is None


def test_case_included(store: Store, helpers):
    """Test to that cases displays case in database"""

    # GIVEN a database with a case
    new_case = add_case(helpers, store)

    # WHEN getting active cases
    cases = store.cases()

    # THEN cases should contain the case
    assert cases
    for case in cases:
        assert new_case.internal_id in case.get("internal_id")


def test_structure(store: Store, helpers):
    """Test to that cases displays case in database"""

    # GIVEN a database with a case
    add_case(helpers, store)

    # WHEN getting active cases
    cases = store.cases()

    # THEN structure should contain
    #   data_analysis
    #   internal_id
    #   name
    #   total number of samples,
    #   samples_received,
    #   samples_prepared,
    #   samples_sequenced,
    #   analysis_completed_at
    #   analysis_pipeline
    #   samples_delivered
    assert cases
    for case in cases:
        assert "data_analysis" in case.keys()
        assert "internal_id" in case.keys()
        assert "name" in case.keys()
        assert "ordered_at" in case.keys()
        assert "total_samples" in case.keys()
        assert "samples_received" in case.keys()
        assert "samples_prepared" in case.keys()
        assert "samples_sequenced" in case.keys()
        assert "analysis_completed_at" in case.keys()
        assert "analysis_pipeline" in case.keys()
        assert "samples_delivered" in case.keys()
        assert "samples_invoiced" in case.keys()


def add_case(
    helpers,
    disk_store,
    case_id="case_test",
    customer_id="cust_test",
    ordered_days_ago=0,
    action=None,
    priority=None,
    data_analysis=Pipeline.BALSAMIC,
    data_delivery=DataDelivery.SCOUT,
    ticket="123456",
):
    """utility function to add a case to use in tests"""
    panel = helpers.ensure_panel(disk_store)
    customer = helpers.ensure_customer(disk_store, customer_id)
    case = disk_store.add_case(
        data_analysis=data_analysis,
        data_delivery=data_delivery,
        name=case_id,
        panels=panel.name,
        priority=priority,
        ticket=ticket,
    )
    case.customer = customer
    case.ordered_at = datetime.now() - timedelta(days=ordered_days_ago)
    if action:
        case.action = action
    disk_store.add_commit(case)
    return case
