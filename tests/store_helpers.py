from datetime import datetime


def ensure_application_version(
    disk_store, application_tag="dummy_tag", application_type="tgs"
):
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
        version = disk_store.add_version(
            application, 1, valid_from=datetime.now(), prices=prices
        )

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
        version = disk_store.add_bed_version(
            bed, 1, "dummy_filename", shortname=bed_name
        )
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