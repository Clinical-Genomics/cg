"""Utility functions to simply add test data in a cg store"""

from datetime import datetime


def ensure_application_version(disk_store, application_tag="dummy_tag", application_type="tgs"):
    """utility function to return existing or create application version for tests"""
    application = disk_store.application(tag=application_tag)
    if not application:
        application = disk_store.add_application(
            tag=application_tag,
            category=application_type,
            percent_kth=80,
            description="dummy_description",
        )
        disk_store.add_commit(application)

    prices = {"standard": 10, "priority": 20, "express": 30, "research": 5}
    version = disk_store.application_version(application, 1)
    if not version:
        version = disk_store.add_version(application, 1, valid_from=datetime.now(), prices=prices)

        disk_store.add_commit(version)
    return version


def ensure_bed_version(disk_store, bed_name="dummy_bed"):
    """utility function to return existing or create bed version for tests"""
    bed = disk_store.bed(name=bed_name)
    if not bed:
        bed = disk_store.add_bed(name=bed_name)
        disk_store.add_commit(bed)

    version = disk_store.latest_bed_version(bed_name)
    if not version:
        version = disk_store.add_bed_version(bed, 1, "dummy_filename", shortname=bed_name)
        disk_store.add_commit(version)
    return version


def ensure_customer(store, customer_id="cust_test"):
    """utility function to return existing or create customer for tests"""
    customer_group_id = customer_id + "_group"
    customer_group = store.customer_group(customer_group_id)
    if not customer_group:
        customer_group = store.add_customer_group(customer_group_id, customer_group_id)

    customer = store.customer(customer_id)

    if not customer:
        customer = store.add_customer(
            internal_id=customer_id,
            name=customer_id + "_name",
            scout_access=False,
            customer_group=customer_group,
            invoice_address="dummy_address",
            invoice_reference="dummy_reference",
        )
        store.add_commit(customer)
    return customer


def add_analysis(store, family=None, completed_at=None):
    """Utility function to add an analysis for tests"""

    if not family:
        family = add_family(store)

    analysis = store.add_analysis(pipeline="", version="")

    if completed_at:
        analysis.completed_at = completed_at

    analysis.family = family
    store.add_commit(analysis)
    return analysis


def add_sample(
    store,
    sample_id="sample_test",
    gender="female",
    is_tumour=False,
    data_analysis="balsamic",
    application_tag="dummy_tag",
    application_type="tgs",
):
    """utility function to add a sample to use in tests"""
    customer = ensure_customer(store)
    application_version_id = ensure_application_version(
        store, application_tag=application_tag, application_type=application_type
    ).id
    sample = store.add_sample(
        name=sample_id,
        sex=gender,
        tumour=is_tumour,
        sequenced_at=datetime.now(),
        data_analysis=data_analysis,
    )

    sample.application_version_id = application_version_id
    sample.customer = customer
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


def add_family(disk_store, family_id="family_test", customer_id="cust_test"):
    """utility function to add a family to use in tests"""
    panel = ensure_panel(disk_store)
    customer = ensure_customer(disk_store, customer_id)
    family = disk_store.add_family(name=family_id, panels=panel.name)
    family.customer = customer
    disk_store.add_commit(family)
    return family


def add_organism(store):
    """utility function to add an organism to use in tests"""
    organism = store.add_organism(internal_id="organism_id", name="organism_name")
    return organism


def add_microbial_sample(store, sample_id="sample_test"):
    """utility function to add a sample to use in tests"""
    customer = ensure_customer(store)
    application_version = ensure_application_version(store)
    organism = add_organism(store)
    sample = store.add_microbial_sample(
        name=sample_id,
        organism=organism,
        internal_id=sample_id,
        reference_genome="test",
        application_version=application_version,
    )
    sample.customer = customer
    return sample


def add_microbial_sample_and_order(store, order_id="sample_test", customer_id="cust_test"):
    """utility function to set a family to use in tests"""
    customer = ensure_customer(store, customer_id)
    with store.session.no_autoflush:
        order = store.add_microbial_order(name=order_id, customer=customer, ordered=datetime.now())
        order.customer = customer
        sample = add_microbial_sample(store)
        order.microbial_samples.append(sample)
    store.add_commit(sample)
    return sample


def add_flowcell(store, flowcell_id="flowcell_test"):
    """utility function to set a flowcell to use in tests"""
    flowcell_obj = store.add_flowcell(
        name=flowcell_id, sequencer="dummy_sequencer", sequencer_type="hiseqx", date=datetime.now()
    )
    store.add_commit(flowcell_obj)
    return flowcell_obj
