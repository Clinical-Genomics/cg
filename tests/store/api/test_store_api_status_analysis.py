"""This script tests the cli methods to add families to status-db"""
from datetime import datetime, timedelta

from cg.constants import Pipeline
from cg.store import Store


def test_that_many_families_can_have_one_sample_each(base_store: Store):
    """Test that tests that families are returned even if there are many result rows in the query"""

    # GIVEN a database with two families one with 50 sequenced samples
    # the other family with one
    n_test_families = 50
    test_families = add_families_with_samples(base_store, n_test_families, sequenced=True)

    # WHEN getting families to analyse
    families = base_store.cases_to_analyze(pipeline=Pipeline.MIP_DNA)

    # THEN families should contain the test family
    assert len(families) == len(test_families)


def test_that_families_can_have_many_samples(base_store: Store):
    """Test that tests that families are returned even if there are many result rows in the query"""

    # GIVEN a database with two families one with 50 sequenced samples
    # the other family with one
    default_limit = 50
    test_family_50 = add_family_with_samples(
        base_store, "test_family_50åäp+ölo0l", default_limit, sequenced=True
    )
    test_sample = add_sample(base_store, sequenced=True)
    test_family = add_family(base_store, "family_one_sample")
    base_store.relate_sample(test_family, test_sample, "unknown")

    # WHEN getting families to analyse
    families = base_store.cases_to_analyze(pipeline=Pipeline.MIP_DNA)

    # THEN families should contain the test family
    assert families
    assert test_family_50 in families
    assert test_family in families


def test_external_sample_to_re_analyse(base_store: Store):
    """Test that a family marked for re-analyse with one sample external not sequenced inhouse and
    with completed analysis do show up among the families to analyse"""

    # GIVEN a database with a family with one not sequenced external sample and completed analysis
    test_sample = add_sample(base_store, sequenced=False, external=True)
    test_analysis = add_analysis(base_store, completed=True, reanalyse=True)
    base_store.relate_sample(test_analysis.family, test_sample, "unknown")

    # WHEN getting families to analyse
    families = base_store.cases_to_analyze(pipeline=Pipeline.MIP_DNA)

    # THEN families should contain the test family
    assert families
    assert test_analysis.family in families


def test_family_to_re_analyse(base_store: Store):
    """Test that a family marked for re-analyse with one sample that has been sequenced and
    with completed analysis do show up among the families to analyse"""

    # GIVEN a database with a family with one of one sequenced samples and completed analysis
    test_sample = add_sample(base_store, sequenced=True)
    test_analysis = add_analysis(base_store, completed=True, reanalyse=True)
    base_store.relate_sample(test_analysis.family, test_sample, "unknown")

    # WHEN getting families to analyse
    families = base_store.cases_to_analyze(pipeline=Pipeline.MIP_DNA)

    # THEN families should contain the test family
    assert families
    assert test_analysis.family in families


def test_all_samples_and_analysis_completed(base_store: Store):
    """Test that a family with one sample that has been sequenced and with completed
    analysis don't show up among the families to analyse"""

    # GIVEN a database with a family with one of one sequenced samples and completed analysis
    test_sample = add_sample(base_store, sequenced=True)
    test_analysis = add_analysis(base_store, completed=True)
    base_store.relate_sample(test_analysis.family, test_sample, "unknown")

    # WHEN getting families to analyse
    families = base_store.cases_to_analyze(pipeline=Pipeline.MIP_DNA)

    # THEN families should not contain the test family

    assert not families


def test_specified_analysis_in_result(base_store: Store):
    """Test that a family with one sample that has specified data_analysis does show up"""

    # GIVEN a database with a family with one sequenced samples for MIP analysis
    pipeline = Pipeline.BALSAMIC
    test_sample = add_sample(base_store, sequenced=True)
    test_family = add_family(base_store, data_analysis=pipeline)
    base_store.relate_sample(test_family, test_sample, "unknown")

    # WHEN getting families to analyse
    families = base_store.cases_to_analyze(pipeline=pipeline)

    # THEN families should contain the test family
    assert families
    assert test_family in families


def test_exclude_other_pipeline_analysis_from_result(base_store: Store):
    """Test that a family with specified analysis and with one sample does not show up among
    others"""

    # GIVEN a database with a family with one sequenced samples for specified analysis
    test_sample = add_sample(base_store, sequenced=True)
    test_family = add_family(base_store, data_analysis=Pipeline.BALSAMIC)
    base_store.relate_sample(test_family, test_sample, "unknown")

    # WHEN getting families to analyse
    families = base_store.cases_to_analyze(pipeline=Pipeline.MIP_DNA)

    # THEN families should not contain the test family
    assert not families


def test_one_of_two_sequenced_samples(base_store: Store):
    """Test that a family with one of one samples that has been sequenced shows up among the
    families to analyse"""

    # GIVEN a database with a family with one of one sequenced samples and no analysis
    test_family = add_family(base_store)
    test_sample1 = add_sample(base_store, sequenced=True)
    test_sample2 = add_sample(base_store, sequenced=False)
    base_store.relate_sample(test_family, test_sample1, "unknown")
    base_store.relate_sample(test_family, test_sample2, "unknown")

    # WHEN getting families to analyse
    families = base_store.cases_to_analyze(pipeline=Pipeline.MIP_DNA)

    # THEN families should not contain the test family
    assert not families


def test_one_of_one_sequenced_samples(base_store: Store):
    """Test that a family with one of one samples that has been sequenced shows up among the
    families to analyse"""

    # GIVEN a database with a family with one of one sequenced samples and no analysis
    test_family = add_family(base_store)
    test_sample = add_sample(base_store, sequenced=True)
    base_store.relate_sample(test_family, test_sample, "unknown")
    assert test_sample.sequenced_at is not None

    # WHEN getting families to analyse
    families = base_store.cases_to_analyze(pipeline=Pipeline.MIP_DNA)

    # THEN families should contain the test family
    assert families
    assert test_family in families


def ensure_application_version(disk_store, application_tag="dummy_tag"):
    """utility function to return existing or create application version for tests"""
    application = disk_store.application(tag=application_tag)
    if not application:
        application = disk_store.add_application(
            tag=application_tag,
            category="wgs",
            description="dummy_description",
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
    received=False,
    prepared=False,
    sequenced=False,
    delivered=False,
    invoiced=False,
    external=None,
):
    """utility function to add a sample to use in tests"""
    customer = ensure_customer(store)
    application_version_id = ensure_application_version(store).id
    sample = store.add_sample(name=sample_name, sex="unknown")
    sample.application_version_id = application_version_id
    sample.customer = customer
    if received:
        sample.received_at = datetime.now()
    if prepared:
        sample.prepared_at = datetime.now()
    if sequenced:
        sample.sequenced_at = datetime.now()
    if delivered:
        sample.delivered_at = datetime.now()
    if invoiced:
        invoice = store.add_invoice(customer)
        sample.invoice = invoice
    if external:
        sample.is_external = external

    store.add_commit(sample)
    return sample


def add_samples(base_store, n_samples, sequenced):
    """utility function to add many samples to use in tests"""
    samples = []
    for _ in range(n_samples):
        samples.append(add_sample(base_store, sequenced=sequenced))
    return samples


def relate_samples(base_store, family, samples):
    """utility function to relate many samples to one family"""

    for sample in samples:
        base_store.relate_sample(family, sample, "unknown")


def add_family_with_samples(base_store, family_name, n_samples, sequenced):
    """utility function to add one family with many samples to use in tests"""

    test_samples = add_samples(base_store, n_samples, sequenced=sequenced)
    test_family = add_family(base_store, family_name)
    relate_samples(base_store, test_family, test_samples)
    return test_family


def add_families_with_samples(base_store, n_families, sequenced):
    """utility function to add many families with two samples to use in tests"""

    families = []
    for i in range(n_families):
        family = add_family_with_samples(base_store, f"f{i}", 2, sequenced=sequenced)
        families.append(family)
    return families


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
    data_analysis=Pipeline.MIP_DNA,
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


def add_analysis(
    store, completed=False, uploaded=False, pipeline=Pipeline.BALSAMIC, reanalyse=False
):
    """Utility function to add an analysis for tests"""
    analysis = store.add_analysis(pipeline=pipeline, version="")
    if completed:
        analysis.completed_at = datetime.now()
    if uploaded:
        analysis.uploaded_at = datetime.now()

    family = add_family(store)

    family.analyses.append(analysis)
    store.add_commit(analysis)

    if reanalyse:
        family.action = "analyze"

    store.add_commit(family)

    return analysis
