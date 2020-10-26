"""This script tests the cli methods to add families to status-db"""
from datetime import datetime, timedelta

from cg.constants import FAMILY_ACTIONS, PRIORITY_OPTIONS
from cg.store import Store


def test_delivered_at_affects_tat(base_store: Store):
    """test that the estimated turnaround time is affected by the delivered_at date """

    # GIVEN a database with a family and a samples receive_at, prepared_at, sequenced_at,
    # delivered_at one week ago
    family = add_family(base_store, ordered_days_ago=7)
    yesterweek = datetime.now() - timedelta(days=7)
    weekold_sample = add_sample(
        base_store,
        ordered=True,
        received=True,
        prepared=True,
        sequenced=True,
        delivered=True,
        date=yesterweek,
    )
    base_store.relate_sample(family, weekold_sample, "unknown")

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN TAT should be R-D = 0 = 0
    assert cases
    for case in cases:
        assert case.get("tat") == 0


def test_sequenced_at_affects_tat(base_store: Store):
    """test that the estimated turnaround time is affected by the sequenced_at date """

    # GIVEN a database with a family and a samples receive_at, prepared_at, sequenced_at one week
    # ago
    family = add_family(base_store, ordered_days_ago=7)
    yesterweek = datetime.now() - timedelta(days=7)
    weekold_sample = add_sample(
        base_store,
        ordered=True,
        received=True,
        prepared=True,
        sequenced=True,
        date=yesterweek,
    )
    base_store.relate_sample(family, weekold_sample, "unknown")

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN TAT should be R-P + P-S + S-A + A-U + U-D = 0 + 0 + 7 + 1 + 2 = 10
    assert cases
    for case in cases:
        assert case.get("tat") == 10


def test_prepared_at_affects_tat(base_store: Store):
    """test that the estimated turnaround time is affected by the prepared_at date """

    # GIVEN a database with a family and a samples receive_at, prepared_at one week ago
    family = add_family(base_store, ordered_days_ago=7)
    yesterweek = datetime.now() - timedelta(days=7)
    weekold_sample = add_sample(
        base_store, ordered=True, received=True, prepared=True, date=yesterweek
    )
    base_store.relate_sample(family, weekold_sample, "unknown")

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN TAT should be R-P + P-S + S-A + A-U + U-D = 0 + 7 + 4 + 1 + 2 = 14
    assert cases
    for case in cases:
        assert case.get("tat") == 14


def test_received_at_affects_tat(base_store: Store):
    """test that the estimated turnaround time is affected by the received_at date """

    # GIVEN a database with a family and a samples received one week ago
    family = add_family(base_store, ordered_days_ago=7)
    yesterweek = datetime.now() - timedelta(days=7)
    weekold_sample = add_sample(base_store, ordered=True, received=True, date=yesterweek)
    base_store.relate_sample(family, weekold_sample, "unknown")

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN TAT should be R-P + P-S + S-A + A-U + U-D = 7 + 5 + 4 + 1 + 2 = 19
    assert cases
    for case in cases:
        assert case.get("tat") == 19


def test_samples_flowcell(base_store: Store):
    """Test to that cases displays the flowcell status """

    # GIVEN a database with a family with a sample that belongs to a flowcell with status ondisk
    # and a sample not yet on a flowcell
    family = add_family(base_store)
    sample_on_flowcell = add_sample(base_store)
    flowcell = add_flowcell(base_store, sample=sample_on_flowcell, status="ondisk")
    base_store.relate_sample(family, sample_on_flowcell, "unknown")
    sample_not_on_flowcell = add_sample(base_store)
    base_store.relate_sample(family, sample_not_on_flowcell, "unknown")

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN cases should contain info on flowcell status and be false
    assert cases
    for case in cases:
        assert flowcell.status in case.get("flowcells_status")
        assert not case.get("flowcells_on_disk_bool")
        assert case.get("flowcells_on_disk") == 1


def test_sample_flowcell(base_store: Store):
    """Test to that cases displays the flowcell status """

    # GIVEN a database with a family with a sample that belongs to a flowcell with status ondisk
    family = add_family(base_store)
    sample = add_sample(base_store)
    base_store.relate_sample(family, sample, "unknown")
    flowcell = add_flowcell(base_store, sample=sample, status="ondisk")
    assert flowcell.status

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN cases should contain info on flowcell status and be true
    assert cases
    for case in cases:
        assert case.get("flowcells_on_disk") == 1
        assert case.get("flowcells_status") == flowcell.status
        assert case.get("flowcells_on_disk_bool")


def test_case_action(base_store: Store):
    """Test to that cases displays no analysis dates for active reruns """

    # GIVEN a database with an analysis that was completed but has an active rerun in progress
    analysis = add_analysis(base_store, completed=True, uploaded=True)
    analysis.family.action = "analyze"

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN cases should contain info on analysis (family) action
    assert cases
    for case in cases:
        assert case.get("case_action") == analysis.family.action


def test_analysis_dates_for_rerun(base_store: Store):
    """Test to that cases displays no analysis dates for active reruns """

    # GIVEN a database with an analysis that was completed but has an active rerun in progress
    analysis = add_analysis(base_store, completed=True, uploaded=True)
    analysis.family.action = "analyze"

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN cases should not contain info on completed and uploaded occasion
    assert cases
    for case in cases:
        assert case.get("analysis_completed_at") is None
        assert case.get("analysis_uploaded_at") is None


def test_received_at_is_newest_date(base_store: Store):
    """Test to that cases displays newest received date"""

    # GIVEN a database with a family and two samples with different received dates
    family = add_family(base_store)
    yesterday = datetime.now() - timedelta(days=1)
    yesteryear = datetime.now() - timedelta(days=365)
    newest_sample = add_sample(base_store, received=True, date=yesterday)
    oldest_sample = add_sample(base_store, received=True, date=yesteryear)
    base_store.relate_sample(family, newest_sample, "unknown")
    base_store.relate_sample(family, oldest_sample, "unknown")

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN cases should contain the date the samples were most recently received
    assert cases
    for case in cases:
        assert case.get("samples_received_at").date() == newest_sample.received_at.date()


def test_prepared_at_is_newest_date(base_store: Store):
    """Test to that cases displays newest prepared date"""

    # GIVEN a database with a family and two samples with different prepared dates
    family = add_family(base_store)
    yesterday = datetime.now() - timedelta(days=1)
    yesteryear = datetime.now() - timedelta(days=365)
    newest_sample = add_sample(base_store, prepared=True, date=yesterday)
    oldest_sample = add_sample(base_store, prepared=True, date=yesteryear)
    base_store.relate_sample(family, newest_sample, "unknown")
    base_store.relate_sample(family, oldest_sample, "unknown")

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN cases should contain the date the samples were most recently prepared
    assert cases
    for case in cases:
        assert case.get("samples_prepared_at").date() == newest_sample.prepared_at.date()


def test_sequenced_at_is_newest_date(base_store: Store):
    """Test to that cases displays newest sequenced date"""

    # GIVEN a database with a family and two samples with different sequenced dates
    family = add_family(base_store)
    yesterday = datetime.now() - timedelta(days=1)
    yesteryear = datetime.now() - timedelta(days=365)
    newest_sample = add_sample(base_store, sequenced=True, date=yesterday)
    oldest_sample = add_sample(base_store, sequenced=True, date=yesteryear)
    base_store.relate_sample(family, newest_sample, "unknown")
    base_store.relate_sample(family, oldest_sample, "unknown")

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN cases should contain the date the samples were most recently sequenced
    assert cases
    for case in cases:
        assert case.get("samples_sequenced_at").date() == newest_sample.sequenced_at.date()


def test_delivered_at_is_newest_date(base_store: Store):
    """Test to that cases displays newest delivered date"""

    # GIVEN a database with a family and two samples with different delivered dates
    family = add_family(base_store)
    yesterday = datetime.now() - timedelta(days=1)
    yesteryear = datetime.now() - timedelta(days=365)
    newest_sample = add_sample(base_store, delivered=True, date=yesterday)
    oldest_sample = add_sample(base_store, delivered=True, date=yesteryear)
    base_store.relate_sample(family, newest_sample, "unknown")
    base_store.relate_sample(family, oldest_sample, "unknown")

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN cases should contain the date the samples were most recently delivered
    assert cases
    for case in cases:
        assert case.get("samples_delivered_at").date() == newest_sample.delivered_at.date()


def test_invoiced_at_is_newest_invoice_date(base_store: Store):
    """Test to that cases displays newest invoiced date"""

    # GIVEN a database with a family and two samples with different invoiced dates
    family = add_family(base_store)
    yesterday = datetime.now() - timedelta(days=1)
    yesteryear = datetime.now() - timedelta(days=365)
    newest_sample = add_sample(base_store, invoiced=True, date=yesterday)
    oldest_sample = add_sample(base_store, invoiced=True, date=yesteryear)
    base_store.relate_sample(family, newest_sample, "unknown")
    base_store.relate_sample(family, oldest_sample, "unknown")

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN cases should contain the date the samples were most recently invoiced
    assert cases
    for case in cases:
        assert case.get("samples_invoiced_at").date() == newest_sample.invoice.invoiced_at.date()


def test_invoiced_at(base_store: Store):
    """Test to that cases displays correct invoiced date"""

    # GIVEN a database with a family and a invoiced date
    family = add_family(base_store)
    sample = add_sample(base_store, invoiced=True)
    base_store.relate_sample(family, sample, "unknown")

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN cases should contain the date the sample was invoiced
    assert cases
    for case in cases:
        assert case.get("samples_invoiced_at").date() == datetime.now().date()


def test_delivered_at(base_store: Store):
    """Test to that cases displays correct delivered date"""

    # GIVEN a database with a family and a delivered date
    family = add_family(base_store)
    sample = add_sample(base_store, delivered=True)
    base_store.relate_sample(family, sample, "unknown")

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN cases should contain the date the sample was delivered
    assert cases
    for case in cases:
        assert case.get("samples_delivered_at").date() == datetime.now().date()


def test_sequenced_at(base_store: Store):
    """Test to that cases displays correct sequenced date"""

    # GIVEN a database with a family and a sequenced date
    family = add_family(base_store)
    sample = add_sample(base_store, sequenced=True)
    base_store.relate_sample(family, sample, "unknown")

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN cases should contain the date the sample was sequenced
    assert cases
    for case in cases:
        assert case.get("samples_sequenced_at").date() == datetime.now().date()


def test_prepared_at(base_store: Store):
    """Test to that cases displays correct prepared date"""

    # GIVEN a database with a family and a prepared date
    family = add_family(base_store)
    sample = add_sample(base_store, prepared=True)
    base_store.relate_sample(family, sample, "unknown")

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN cases should contain the date the sample was prepared
    assert cases
    for case in cases:
        assert case.get("samples_prepared_at").date() == datetime.now().date()


def test_received_at(base_store: Store):
    """Test to that cases displays correct received date"""

    # GIVEN a database with a family and a received date
    family = add_family(base_store)
    sample = add_sample(base_store, received=True)
    base_store.relate_sample(family, sample, "unknown")

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN cases should contain the date the sample was received
    assert cases
    for case in cases:
        assert case.get("samples_received_at").date() == datetime.now().date()


def test_no_invoice_true(base_store: Store):
    """Test to that cases displays correct samples to invoice"""

    # GIVEN a database with a family and one no_invoice sample
    family = add_family(base_store)
    sample = add_sample(base_store, no_invoice=True)
    base_store.relate_sample(family, sample, "unknown")
    assert sample.no_invoice

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN cases should contain zero samples to invoice
    assert cases
    for case in cases:
        assert case.get("samples_to_invoice") == 0


def test_one_no_invoice_false(base_store: Store):
    """Test to that cases displays correct samples to invoice"""

    # GIVEN a database with a family and one sample to invoice
    family = add_family(base_store)
    sample = add_sample(base_store, no_invoice=False)
    base_store.relate_sample(family, sample, "unknown")
    assert not sample.no_invoice

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN cases should contain one sample to invoice
    assert cases
    for case in cases:
        assert case.get("samples_to_invoice") == 1


def test_one_external_sample(base_store: Store):
    """Test to that cases displays correct internal/external samples"""

    # GIVEN a database with a family and one external sample
    family = add_family(base_store)
    sample = add_sample(base_store, is_external=True)
    base_store.relate_sample(family, sample, "unknown")
    assert sample.application_version.application.is_external

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN cases should contain one external and zero internal samples
    assert cases
    for case in cases:
        assert case.get("total_external_samples") == 1
        assert case.get("total_internal_samples") == 0
        assert case.get("case_external_bool")
        assert case.get("samples_to_receive") == 0
        assert case.get("samples_to_prepare") == 0
        assert case.get("samples_to_sequence") == 0


def test_one_internal_sample(base_store: Store):
    """Test to that cases displays correct internal/external samples"""

    # GIVEN a database with a family and one external sample
    family = add_family(base_store)
    sample = add_sample(base_store, is_external=False)
    base_store.relate_sample(family, sample, "unknown")
    assert not sample.is_external

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN cases should contain zero external and one internal samples
    assert cases
    for case in cases:
        assert case.get("total_external_samples") == 0
        assert case.get("total_internal_samples") == 1
        assert case.get("samples_to_receive") == 1
        assert case.get("samples_to_prepare") == 1
        assert case.get("samples_to_sequence") == 1


def test_include_case_by_sample_id(base_store: Store):
    """Test to that cases can be included by sample id"""

    # GIVEN a database with a sample with internal_id
    family = add_family(base_store)
    sample = add_sample(base_store)
    base_store.relate_sample(family, sample, "unknown")

    # WHEN getting active cases by sample id
    cases = base_store.cases(sample_id=sample.internal_id)

    # THEN cases should only contain this case
    assert cases
    for case in cases:
        assert family.internal_id in case.get("internal_id")


def test_exclude_case_by_sample_id(base_store: Store):
    """Test to that cases can be excluded by sample id"""

    # GIVEN a database with a sample with internal_id
    family = add_family(base_store)
    sample = add_sample(base_store)
    base_store.relate_sample(family, sample, "unknown")

    # WHEN getting active cases by non-existing sample id
    cases = base_store.cases(sample_id="dummy_id")

    # THEN cases should not contain this case
    assert not cases


def test_include_case_by_exclude_customer(base_store: Store):
    """Test to that cases can be excluded by customer"""

    # GIVEN a database with a family and a customer
    customer_id = "cust000"
    family = add_family(base_store, customer_id=customer_id)

    # WHEN getting active cases by customer
    cases = base_store.cases(exclude_customer_id="dummy_customer")

    # THEN cases should contain this case
    assert cases
    for case in cases:
        assert family.internal_id in case.get("internal_id")


def test_exclude_case_by_exclude_customer(base_store: Store):
    """Test to that cases can be excluded by customer"""

    # GIVEN a database with a family and a customer
    customer_id = "cust000"
    add_family(base_store, customer_id=customer_id)

    # WHEN getting active cases by customer
    cases = base_store.cases(exclude_customer_id=customer_id)

    # THEN cases should not contain this case
    assert not cases


def test_include_case_by_case_lowercase_data_analysis(base_store: Store):
    """Test to that cases can be included by lowercase data_analysis"""

    # GIVEN a database with a family with data analysis set
    family = add_family(base_store, data_analysis="UPPERCASE")
    sample = add_sample(base_store)
    base_store.relate_sample(family, sample, "unknown")

    # WHEN getting active cases by data_analysis
    cases = base_store.cases(data_analysis=family.data_analysis.lower())

    # THEN cases should only contain this case
    assert cases
    for case in cases:
        assert family.internal_id in case.get("internal_id")


def test_include_case_by_case_uppercase_data_analysis(base_store: Store):
    """Test to that cases can be included by uppercase data_analysis"""

    # GIVEN a database with a family with data analysis set
    family = add_family(base_store, data_analysis="lowercase")
    sample = add_sample(base_store)
    base_store.relate_sample(family, sample, "unknown")

    # WHEN getting active cases by data_analysis
    cases = base_store.cases(data_analysis=family.data_analysis.upper())

    # THEN cases should only contain this case
    assert cases
    for case in cases:
        assert family.internal_id in case.get("internal_id")


def test_include_samples_with_different_data_analysis(base_store: Store):
    """Test to that cases can be included by data_analysis"""

    # GIVEN a database with a family with data analysis set
    family = add_family(base_store, data_analysis="data_analysis")
    sample_1 = add_sample(base_store, invoiced=True)
    sample_2 = add_sample(base_store, invoiced=True)
    base_store.relate_sample(family, sample_1, "unknown")
    base_store.relate_sample(family, sample_2, "unknown")

    # WHEN getting active cases by data_analysis
    cases = base_store.cases(data_analysis="data_analysis")

    # THEN cases should only contain this case
    assert cases
    for case in cases:
        assert family.internal_id in case.get("internal_id")
        assert case.get("samples_invoiced") == 2


def test_exclude_case_by_data_analysis(base_store: Store):
    """Test to that cases can be excluded by data_analysis"""

    # GIVEN a database with a family with data analysis set
    family = add_family(base_store, data_analysis="data_analysis")
    sample = add_sample(base_store)
    base_store.relate_sample(family, sample, "unknown")

    # WHEN getting active cases by data_analysis
    cases = base_store.cases(data_analysis="dummy_analysis")

    # THEN cases should not contain this case
    assert not cases


def test_include_case_by_partial_data_analysis(base_store: Store):
    """Test to that cases can be included by data_analysis"""

    # GIVEN a database with a family with data analysis set
    family = add_family(base_store, data_analysis="data_analysis")
    sample = add_sample(base_store)
    base_store.relate_sample(family, sample, "unknown")

    # WHEN getting active cases by partial data_analysis
    cases = base_store.cases(data_analysis="data_an")

    # THEN cases should only contain this case
    assert cases
    for case in cases:
        assert family.internal_id in case.get("internal_id")


def test_show_multiple_data_analysis(base_store: Store):
    """Test to that cases can be included by data_analysis"""

    # GIVEN a database with a family with data analysis set
    family = add_family(base_store, data_analysis="data_analysis")
    sample1 = add_sample(base_store)
    base_store.relate_sample(family, sample1, "unknown")
    family2 = add_family(base_store, family_id="family2", data_analysis="data_analysis2")
    sample2 = add_sample(base_store)
    base_store.relate_sample(family, sample2, "unknown")
    base_store.relate_sample(family2, sample2, "unknown")

    # WHEN getting active cases by data_analysis
    cases = base_store.cases(data_analysis="data_analysis")

    # THEN cases should only contain these analyses
    assert cases
    for case in cases:
        assert family2.internal_id or family.internal_id in case.get("internal_id")


def test_show_data_analysis(base_store: Store):
    """Test to that cases can be included by data_analysis"""

    # GIVEN a database with a family with data analysis set
    family = add_family(base_store, data_analysis="data_analysis")
    sample = add_sample(base_store)
    base_store.relate_sample(family, sample, "unknown")

    # WHEN getting active cases by data_analysis
    cases = base_store.cases(data_analysis="data_analysis")

    # THEN cases should only contain this case
    assert cases
    for case in cases:
        assert family.internal_id in case.get("internal_id")


def test_include_case_by_data_analysis(base_store: Store):
    """Test to that cases can be included by data_analysis"""

    # GIVEN a database with a family with data analysis set
    family = add_family(base_store, data_analysis="data_analysis")
    sample = add_sample(base_store)
    base_store.relate_sample(family, sample, "unknown")

    # WHEN getting active cases by data_analysis
    cases = base_store.cases(data_analysis=family.data_analysis)

    # THEN cases should only contain this case
    assert cases
    for case in cases:
        assert family.internal_id in case.get("internal_id")


def test_exclude_case_by_customer(base_store: Store):
    """Test to that cases can be excluded by customer"""

    # GIVEN a database with a family and a customer
    add_family(base_store, customer_id="cust000")

    # WHEN getting active cases by customer
    cases = base_store.cases(customer_id="dummy_cust")

    # THEN cases should not contain this case
    assert not cases


def test_include_case_by_customer(base_store: Store):
    """Test to that cases can be included by customer"""

    # GIVEN a database with a family
    customer_id = "cust000"
    family = add_family(base_store, customer_id=customer_id)

    # WHEN getting active cases by customer
    cases = base_store.cases(customer_id=customer_id)

    # THEN cases should only contain this case
    assert cases
    for case in cases:
        assert family.internal_id in case.get("internal_id")


def test_exclude_case_by_name(base_store: Store):
    """Test to that cases can be excluded by name"""

    # GIVEN a database with a family
    add_family(base_store)

    # WHEN getting active cases by name
    cases = base_store.cases(name="dummy_name")

    # THEN cases should not contain this case
    assert not cases


def test_include_case_by_partial_name(base_store: Store):
    """Test to that cases can be included by name"""

    # GIVEN a database with a family
    family = add_family(base_store)

    # WHEN getting active cases by partial name
    cases = base_store.cases(name=family.name[1:-1])

    # THEN cases should only contain this case
    assert cases
    for case in cases:
        assert family.name in case.get("name")


def test_include_case_by_name(base_store: Store):
    """Test to that cases can be included by name"""

    # GIVEN a database with a family
    family = add_family(base_store)

    # WHEN getting active cases by name
    cases = base_store.cases(name=family.name)

    # THEN cases should only contain this case
    assert cases
    for case in cases:
        assert family.name in case.get("name")


def test_excluded_by_priority(base_store: Store):
    """Test to that cases can be excluded by priority"""

    # GIVEN a database with a family with a priority
    add_family(base_store, priority=PRIORITY_OPTIONS[0])

    # WHEN getting active cases by priority
    cases = base_store.cases(priority=PRIORITY_OPTIONS[1])

    # THEN cases should not contain this case
    assert not cases


def test_included_by_priority(base_store: Store):
    """Test to that cases can be included by priority"""

    # GIVEN a database with a family with a priority
    family = add_family(base_store, priority=PRIORITY_OPTIONS[0])

    # WHEN getting active cases by priority
    cases = base_store.cases(priority=family.action)

    # THEN cases should only contain this case
    assert cases
    for case in cases:
        assert family.internal_id in case.get("internal_id")


def test_excluded_by_action(base_store: Store):
    """Test to that cases can be excluded by action"""

    # GIVEN a database with a family with an action
    add_family(base_store, action=FAMILY_ACTIONS[0])

    # WHEN getting active cases by action
    cases = base_store.cases(case_action=FAMILY_ACTIONS[1])

    # THEN cases should not contain this case
    assert not cases


def test_included_by_action(base_store: Store):
    """Test to that cases can be included by action"""

    # GIVEN a database with a family with an action
    family = add_family(base_store, action=FAMILY_ACTIONS[0])

    # WHEN getting active cases by action
    cases = base_store.cases(case_action=family.action)

    # THEN cases should only contain this case
    assert cases
    for case in cases:
        assert family.internal_id in case.get("internal_id")


def test_exclude_case_by_internal_id(base_store: Store):
    """Test to that cases can be excluded by internal_id"""

    # GIVEN a database with a family
    add_family(base_store)

    # WHEN getting active cases by internal_id
    cases = base_store.cases(internal_id="dummy_id")

    # THEN cases should not contain this case
    assert not cases


def test_include_case_by_partial_internal_id(base_store: Store):
    """Test to that cases can be included by internal_id"""

    # GIVEN a database with a family
    family = add_family(base_store)

    # WHEN getting active cases by partial internal_id
    cases = base_store.cases(internal_id=family.internal_id[1:-1])

    # THEN cases should only contain this case
    assert cases
    for case in cases:
        assert family.internal_id in case.get("internal_id")


def test_include_case_by_internal_id(base_store: Store):
    """Test to that cases can be included by internal_id"""

    # GIVEN a database with a family
    family = add_family(base_store)

    # WHEN getting active cases by internal_id
    cases = base_store.cases(internal_id=family.internal_id)

    # THEN cases should only contain this case
    assert cases
    for case in cases:
        assert family.internal_id in case.get("internal_id")


def test_only_prepared_cases(base_store: Store):
    """Test to that sequenced cases can be included"""

    # GIVEN a database with an prepared case
    family = add_family(base_store)
    sample = add_sample(base_store, prepared=True)
    base_store.relate_sample(family, sample, "unknown")
    neg_family = add_family(base_store, "neg_family")
    neg_sample = add_sample(base_store, sample_name="neg_sample")
    base_store.relate_sample(neg_family, neg_sample, "unknown")

    # WHEN getting active cases excluding prepared
    cases = base_store.cases(only_prepared=True)

    # THEN cases should only contain the prepared case
    assert cases
    for case in cases:
        assert family.internal_id in case.get("internal_id")


def test_only_received_cases(base_store: Store):
    """Test to that sequenced cases can be included"""

    # GIVEN a database with an received case
    family = add_family(base_store)
    sample = add_sample(base_store, received=True)
    base_store.relate_sample(family, sample, "unknown")
    neg_family = add_family(base_store, "neg_family")
    neg_sample = add_sample(base_store, sample_name="neg_sample")
    base_store.relate_sample(neg_family, neg_sample, "unknown")

    # WHEN getting active cases excluding received
    cases = base_store.cases(only_received=True)

    # THEN cases should only contain the received case
    assert cases
    for case in cases:
        assert family.internal_id in case.get("internal_id")


def test_only_sequenced_cases(base_store: Store):
    """Test to that sequenced cases can be included"""

    # GIVEN a database with an sequenced case
    family = add_family(base_store)
    sample = add_sample(base_store, sequenced=True)
    base_store.relate_sample(family, sample, "unknown")
    neg_family = add_family(base_store, "neg_family")
    neg_sample = add_sample(base_store, sample_name="neg_sample")
    base_store.relate_sample(neg_family, neg_sample, "unknown")

    # WHEN getting active cases excluding sequenced
    cases = base_store.cases(only_sequenced=True)

    # THEN cases should only contain the sequenced case
    assert cases
    for case in cases:
        assert family.internal_id in case.get("internal_id")


def test_only_delivered_cases(base_store: Store):
    """Test to that invoiced cases can be included"""

    # GIVEN a database with an delivered case
    family = add_family(base_store)
    sample = add_sample(base_store, delivered=True)
    base_store.relate_sample(family, sample, "unknown")
    neg_family = add_family(base_store, "neg_family")
    neg_sample = add_sample(base_store, sample_name="neg_sample")
    base_store.relate_sample(neg_family, neg_sample, "unknown")

    # WHEN getting active cases excluding delivered
    cases = base_store.cases(only_delivered=True)

    # THEN cases should only contain the delivered case
    assert cases
    for case in cases:
        assert family.internal_id in case.get("internal_id")


def test_only_uploaded_cases(base_store: Store):
    """Test to that uploaded cases can be included"""

    # GIVEN a database with an uploaded analysis
    add_analysis(base_store, uploaded=True)
    neg_family = add_family(base_store, "neg_family")
    neg_sample = add_sample(base_store, sample_name="neg_sample")
    base_store.relate_sample(neg_family, neg_sample, "unknown")

    # WHEN getting active cases excluding uploaded
    cases = base_store.cases(only_uploaded=True)

    # THEN cases should only contain the uploaded case
    assert cases
    for case in cases:
        assert neg_family.internal_id not in case.get("internal_id")


def test_only_delivery_reported_cases(base_store: Store):
    """Test to that delivery-reported cases can be included"""

    # GIVEN a database with an delivery-reported analysis
    add_analysis(base_store, delivery_reported=True)
    neg_family = add_family(base_store, "neg_family")
    neg_sample = add_sample(base_store, sample_name="neg_sample")
    base_store.relate_sample(neg_family, neg_sample, "unknown")

    # WHEN getting active cases excluding delivery_reported
    cases = base_store.cases(only_delivery_reported=True)

    # THEN cases should only contain the delivery-reported case
    assert cases
    for case in cases:
        assert neg_family.internal_id not in case.get("internal_id")


def test_only_invoiced_cases(base_store: Store):
    """Test to that invoiced cases can be included"""

    # GIVEN a database with an invoiced case
    family = add_family(base_store)
    sample = add_sample(base_store, invoiced=True)
    base_store.relate_sample(family, sample, "unknown")
    neg_family = add_family(base_store, "neg_family")
    neg_sample = add_sample(base_store, sample_name="neg_sample")
    base_store.relate_sample(neg_family, neg_sample, "unknown")

    # WHEN getting active cases excluding invoiced
    cases = base_store.cases(only_invoiced=True)

    # THEN cases should only contain the invoiced case
    assert cases
    for case in cases:
        assert family.internal_id in case.get("internal_id")


def test_only_analysed_cases(base_store: Store):
    """Test to that invoiced cases can be included"""

    # GIVEN a database with a completed analysis
    add_analysis(base_store, completed=True)
    neg_family = add_family(base_store, "neg_family")
    neg_sample = add_sample(base_store, sample_name="neg_sample")
    base_store.relate_sample(neg_family, neg_sample, "unknown")

    # WHEN getting active cases excluding invoiced
    cases = base_store.cases(only_analysed=True)

    # THEN cases should only contain the completed case
    assert cases
    for case in cases:
        assert neg_family.internal_id not in case.get("internal_id")


def test_exclude_prepared_cases(base_store: Store):
    """Test to that sequenced cases can be excluded"""

    # GIVEN a database with an prepared case
    family = add_family(base_store)
    sample = add_sample(base_store, prepared=True)
    base_store.relate_sample(family, sample, "unknown")

    # WHEN getting active cases excluding prepared
    cases = base_store.cases(exclude_prepared=True)

    # THEN cases should not contain the prepared case
    assert not cases


def test_exclude_received_cases(base_store: Store):
    """Test to that sequenced cases can be excluded"""

    # GIVEN a database with an received case
    family = add_family(base_store)
    sample = add_sample(base_store, received=True)
    base_store.relate_sample(family, sample, "unknown")

    # WHEN getting active cases excluding received
    cases = base_store.cases(exclude_received=True)

    # THEN cases should not contain the received case
    assert not cases


def test_exclude_sequenced_cases(base_store: Store):
    """Test to that sequenced cases can be excluded"""

    # GIVEN a database with an sequenced case
    family = add_family(base_store)
    sample = add_sample(base_store, sequenced=True)
    base_store.relate_sample(family, sample, "unknown")

    # WHEN getting active cases excluding sequenced
    cases = base_store.cases(exclude_sequenced=True)

    # THEN cases should not contain the sequenced case
    assert not cases


def test_exclude_delivered_cases(base_store: Store):
    """Test to that invoiced cases can be excluded"""

    # GIVEN a database with an delivered case
    family = add_family(base_store)
    sample = add_sample(base_store, delivered=True)
    base_store.relate_sample(family, sample, "unknown")

    # WHEN getting active cases excluding delivered
    cases = base_store.cases(exclude_delivered=True)

    # THEN cases should not contain the delivered case
    assert not cases


def test_exclude_uploaded_cases(base_store: Store):
    """Test to that uploaded cases can be excluded"""

    # GIVEN a database with an uploaded analysis
    add_analysis(base_store, uploaded=True)

    # WHEN getting active cases excluding uploaded
    cases = base_store.cases(exclude_uploaded=True)

    # THEN cases should not contain the uploaded case
    assert not cases


def test_exclude_delivery_reported_cases(base_store: Store):
    """Test to that delivery-reported cases can be excluded"""

    # GIVEN a database with an delivery-reported analysis
    add_analysis(base_store, delivery_reported=True)

    # WHEN getting active cases excluding delivery-reported
    cases = base_store.cases(exclude_delivery_reported=True)

    # THEN cases should not contain the delivery-reported case
    assert not cases


def test_exclude_invoiced_cases(base_store: Store):
    """Test to that invoiced cases can be excluded"""

    # GIVEN a database with an invoiced case
    family = add_family(base_store)
    sample = add_sample(base_store, invoiced=True)
    base_store.relate_sample(family, sample, "unknown")

    # WHEN getting active cases excluding invoiced
    cases = base_store.cases(exclude_invoiced=True)

    # THEN cases should not contain the invoiced case
    assert not cases


def test_exclude_analysed_cases(base_store: Store):
    """Test to that invoiced cases can be excluded"""

    # GIVEN a database with a completed analysis
    add_analysis(base_store, completed=True)

    # WHEN getting active cases excluding invoiced
    cases = base_store.cases(exclude_analysed=True)

    # THEN cases should not contain the completed case
    assert not cases


def test_all_days(base_store: Store):
    """Test to that cases filter in family in database"""

    # GIVEN a database with a really old family
    family = add_family(base_store, ordered_days_ago=9999)

    # WHEN getting active cases with days = all
    cases = base_store.cases(days=0)

    # THEN cases should contain the family
    assert cases
    for case in cases:
        assert family.internal_id in case.get("internal_id")


def test_new_family_included(base_store: Store):
    """Test to that cases filter in family in database"""

    # GIVEN a database with a family
    family = add_family(base_store, ordered_days_ago=1)

    # WHEN getting active cases not older than two days
    cases = base_store.cases(days=2)

    # THEN cases should contain the family
    assert cases
    for case in cases:
        assert family.internal_id in case.get("internal_id")


def test_old_family_not_included(base_store: Store):
    """Test to that cases filter out old family in database"""

    # GIVEN a database with a family
    add_family(base_store, ordered_days_ago=2)

    # WHEN getting active cases not older than one day
    cases = base_store.cases(days=1)

    # THEN cases should not contain the family
    assert not cases


def test_analysis_bool_true(base_store: Store):
    """Test to that cases displays correct booleans for samples"""

    # GIVEN a database with a family
    add_analysis(base_store, completed=True, uploaded=True)

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN cases should contain true for all analysis booleans
    assert cases
    for case in cases:
        assert case.get("analysis_completed_bool") is True
        assert case.get("analysis_uploaded_bool") is True


def test_samples_bool_true(base_store: Store):
    """Test to that cases displays correct booleans for samples"""

    # GIVEN a database with a family
    family = add_family(base_store)
    sample = add_sample(
        base_store,
        received=True,
        prepared=True,
        sequenced=True,
        delivered=True,
        invoiced=True,
    )
    base_store.relate_sample(family, sample, "unknown")

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN cases should contain true for all sample booleans
    assert cases
    for case in cases:
        assert case.get("samples_received_bool") is True
        assert case.get("samples_prepared_bool") is True
        assert case.get("samples_sequenced_bool") is True
        assert case.get("samples_delivered_bool") is True
        assert case.get("samples_invoiced_bool") is True


def test_bool_false(base_store: Store):
    """Test to that cases displays correct received samples"""

    # GIVEN a database with a family
    family = add_family(base_store)
    sample = add_sample(base_store)
    base_store.relate_sample(family, sample, "unknown")

    # WHEN getting active cases
    cases = base_store.cases()

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


def test_one_invoiced_sample(base_store: Store):
    """Test to that cases displays correct invoiced samples"""

    # GIVEN a database with a family with an invoiced sample
    family = add_family(base_store)
    sample = add_sample(base_store, invoiced=True)
    base_store.relate_sample(family, sample, "unknown")
    assert sample.invoice is not None

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN cases should contain number of invoiced samples
    assert cases
    for case in cases:
        assert case.get("samples_invoiced") == 1


def test_analysis_uploaded_at(base_store: Store):
    """Test to that cases displays when uploaded """

    # GIVEN a database with an analysis that was uploaded
    analysis = add_analysis(base_store, uploaded=True)
    assert analysis.uploaded_at is not None

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN cases should contain info on upload occasion
    assert cases
    for case in cases:
        assert case.get("analysis_uploaded_at") is not None


def test_analysis_pipeline(base_store: Store):
    """Test to that cases displays pipeline """

    # GIVEN a database with an analysis that has pipeline
    pipeline = "pipeline"
    analysis = add_analysis(base_store, pipeline=pipeline)
    assert analysis.pipeline is not None

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN cases should contain info on pipeline
    assert cases
    for case in cases:
        assert case.get("analysis_pipeline") == pipeline


def test_samples_delivered(base_store: Store):
    """Test to that cases displays when they were delivered """

    # GIVEN a database with a sample that is delivered
    family = add_family(base_store)
    sample = add_sample(base_store, delivered=True)
    base_store.relate_sample(family, sample, "unknown")
    assert sample.delivered_at is not None

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN cases should contain info on delivered occasion
    assert cases
    for case in cases:
        assert case.get("samples_delivered") == 1


def test_analysis_completed_at(base_store: Store):
    """Test to that cases displays when they were completed """

    # GIVEN a database with an analysis that is completed
    analysis = add_analysis(base_store, completed=True)
    assert analysis.completed_at is not None
    assert base_store.families().count() == 1
    assert base_store.analyses().count() == 1

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN cases should contain info on completion occasion
    assert cases
    for case in cases:
        assert case.get("analysis_completed_at") is not None


def test_family_ordered_date(base_store: Store):
    """Test to that cases displays when they were ordered """

    # GIVEN a database with a family without samples and no analyses
    family = add_family(base_store)
    assert family.ordered_at is not None

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN cases should contain info on order occasion
    assert cases
    for case in cases:
        assert case.get("ordered_at") is not None


def test_one_of_two_samples_received(base_store: Store):
    """Test to that cases displays correct received samples"""

    # GIVEN a database with a family with a received sample and one not received
    family = add_family(base_store)
    sample_received = add_sample(base_store, "sample_received", received=True)
    sample_not_received = add_sample(base_store, "sample_not_received", received=False)
    base_store.relate_sample(family, sample_received, "unknown")
    base_store.relate_sample(family, sample_not_received, "unknown")
    assert sample_received.received_at is not None
    assert sample_not_received.received_at is None

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN cases should contain number of received samples
    assert cases
    for case in cases:
        assert case.get("total_samples") == 2
        assert case.get("samples_received") == 1


def test_one_sequenced_sample(base_store: Store):
    """Test to that cases displays correct sequenced samples"""

    # GIVEN a database with a family with a sequenced sample
    family = add_family(base_store)
    sample = add_sample(base_store, sequenced=True)
    base_store.relate_sample(family, sample, "unknown")
    assert sample.sequenced_at is not None

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN cases should contain number of sequenced samples
    assert cases
    for case in cases:
        assert case.get("samples_sequenced") == 1


def test_one_prepared_sample(base_store: Store):
    """Test to that cases displays correct prepared samples"""

    # GIVEN a database with a family
    family = add_family(base_store)
    sample = add_sample(base_store, prepared=True)
    base_store.relate_sample(family, sample, "unknown")
    assert sample.prepared_at is not None

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN cases should contain number of prepared samples
    assert cases
    for case in cases:
        assert case.get("samples_prepared") == 1


def test_one_received_sample(base_store: Store):
    """Test to that cases displays correct received samples"""

    # GIVEN a database with a family
    family = add_family(base_store)
    sample = add_sample(base_store, received=True)
    base_store.relate_sample(family, sample, "unknown")
    assert sample.received_at is not None

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN cases should contain number of received samples
    assert cases
    for case in cases:
        assert case.get("samples_received") == 1


def test_one_sample(base_store: Store):
    """Test to that cases displays correct total samples"""

    # GIVEN a database with a family
    family = add_family(base_store)
    sample = add_sample(base_store)
    base_store.relate_sample(family, sample, "unknown")
    assert sample.received_at is None
    assert sample.prepared_at is None
    assert sample.delivered_at is None
    assert sample.sequenced_at is None

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN cases should contain the family
    assert cases
    for case in cases:
        assert case.get("total_samples") == 1
        assert case.get("samples_received") == 0
        assert case.get("samples_prepared") == 0
        assert case.get("samples_sequenced") == 0
        assert case.get("samples_delivered") == 0
        assert case.get("samples_invoiced") == 0


def test_family_without_samples(base_store: Store):
    """Test to that cases displays correct number samples"""

    # GIVEN a database with a family without samples and no analyses
    family = add_family(base_store)
    assert not family.links
    assert not family.analyses

    # WHEN getting active cases
    cases = base_store.cases()

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


def test_family_included(base_store: Store):
    """Test to that cases displays family in database"""

    # GIVEN a database with a family
    family = add_family(base_store)

    # WHEN getting active cases
    cases = base_store.cases()

    # THEN cases should contain the family
    assert cases
    for case in cases:
        assert family.internal_id in case.get("internal_id")


def test_structure(base_store: Store):
    """Test to that cases displays family in database"""

    # GIVEN a database with a family
    add_family(base_store)

    # WHEN getting active cases
    cases = base_store.cases()

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


def ensure_application_version(disk_store, application_tag="dummy_tag", is_external=False):
    """utility function to return existing or create application version for tests"""
    application = disk_store.application(tag=application_tag)
    if not application:
        application = disk_store.add_application(
            tag=application_tag,
            category="wgs",
            description="dummy_description",
            is_external=is_external,
            percent_kth=80,
        )
        disk_store.add_commit(application)

    prices = {"standard": 10, "priority": 20, "express": 30, "research": 5}
    version = disk_store.application_version(application, 1)
    if not version:
        version = disk_store.add_version(application, 1, valid_from=datetime.now(), prices=prices)

        disk_store.add_commit(version)
    return version


def ensure_customer(disk_store, customer_id="cust_test"):
    """utility function to return existing or create customer for tests"""
    customer_group = disk_store.customer_group("dummy_group")
    if not customer_group:
        customer_group = disk_store.add_customer_group("dummy_group", "dummy group")

        customer = disk_store.add_customer(
            internal_id=customer_id,
            name="Test Customer",
            scout_access=False,
            customer_group=customer_group,
            invoice_address="dummy_address",
            invoice_reference="dummy_reference",
        )
        disk_store.add_commit(customer)
    customer = disk_store.customer(customer_id)
    return customer


def add_sample(
    store,
    sample_name="sample_test",
    ordered=True,
    received=False,
    prepared=False,
    sequenced=False,
    delivered=False,
    invoiced=False,
    data_analysis=None,
    is_external=False,
    no_invoice=False,
    date=datetime.now(),
):
    """utility function to add a sample to use in tests"""
    application_version_id = ensure_application_version(store).id
    sample = store.add_sample(name=sample_name, sex="unknown")
    sample.application_version_id = application_version_id
    sample.customer = ensure_customer(store)

    if ordered:
        sample.ordered_at = date
    if received:
        sample.received_at = date
    if prepared:
        sample.prepared_at = date
    if sequenced:
        sample.sequenced_at = date
    if delivered:
        sample.delivered_at = date
    if invoiced:
        invoice = store.add_invoice(ensure_customer(store))
        sample.invoice = invoice
        sample.invoice.invoiced_at = date
    if data_analysis:
        sample.data_analysis = data_analysis

    if is_external:
        application_version_id = ensure_application_version(
            store, "external_tag", is_external=True
        ).id
        sample.application_version_id = application_version_id

    if no_invoice:
        sample.no_invoice = no_invoice

    store.add_commit(sample)
    return sample


def ensure_panel(disk_store, panel_id="panel_test", customer_id="cust_test"):
    """utility function to add a panel to use in tests"""
    customer = ensure_customer(disk_store, customer_id)
    panel = disk_store.panel(panel_id)
    if not panel:
        panel = disk_store.add_panel(
            customer=customer,
            name=panel_id,
            abbrev=panel_id,
            version=1.0,
            date=datetime.now(),
            genes=1,
        )
        disk_store.add_commit(panel)
    return panel


def add_family(
    disk_store,
    family_id="family_test",
    customer_id="cust_test",
    ordered_days_ago=0,
    action=None,
    priority=None,
    data_analysis="mip",
):
    """utility function to add a family to use in tests"""
    panel = ensure_panel(disk_store)
    customer = ensure_customer(disk_store, customer_id)
    family = disk_store.add_family(data_analysis=data_analysis, name=family_id, panels=panel.name)
    family.customer = customer
    family.ordered_at = datetime.now() - timedelta(days=ordered_days_ago)
    if action:
        family.action = action
    if priority:
        family.priority = priority
    disk_store.add_commit(family)
    return family


def add_analysis(store, completed=False, uploaded=False, pipeline=None, delivery_reported=False):
    """Utility function to add an analysis for tests"""
    family = add_family(store)
    analysis = store.add_analysis(pipeline="", version="")
    if completed:
        analysis.completed_at = datetime.now()
    if uploaded:
        analysis.uploaded_at = datetime.now()
    if delivery_reported:
        analysis.delivery_report_created_at = datetime.now()
    if pipeline:
        analysis.pipeline = pipeline

    family.analyses.append(analysis)
    store.add_commit(analysis)
    return analysis


def add_flowcell(store, name="flowcell_test", sample=None, status=None):
    """utility function to get a flowcell to use in tests"""
    flowcell = store.add_flowcell(
        name=name,
        sequencer="dummy_sequencer",
        sequencer_type="hiseqx",
        date=datetime.now(),
    )
    if status:
        flowcell.status = status
    if sample:
        flowcell.samples = [sample]
    store.add_commit(flowcell)
    return flowcell
