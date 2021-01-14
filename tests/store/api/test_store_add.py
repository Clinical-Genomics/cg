from datetime import datetime as dt

from cg.constants import Pipeline
from cg.store import Store


def test_add_customer(store: Store):
    # GIVEN an empty database
    assert store.Customer.query.first() is None
    internal_id, name, scout_access = "cust000", "Test customer", True
    customer_group = store.add_customer_group("dummy_group", "dummy group")

    # WHEN adding a new customer
    new_customer = store.add_customer(
        internal_id=internal_id,
        name=name,
        scout_access=scout_access,
        customer_group=customer_group,
        invoice_address="dummy street 1",
        invoice_reference="dummy nr",
    )
    store.add_commit(new_customer)

    # THEN it should be stored in the database
    assert store.Customer.query.first() == new_customer


def test_add_customer_group(store: Store):
    # GIVEN an empty database
    assert store.CustomerGroup.query.first() is None
    internal_id, name = "cust_group", "Test customer group"

    # WHEN adding a new customer group
    new_customer_group = store.add_customer_group(internal_id=internal_id, name=name)
    store.add_commit(new_customer_group)

    # THEN it should be stored in the database
    assert store.CustomerGroup.query.first() == new_customer_group


def test_add_user(store: Store):
    # GIVEN a database with a customer in it that we can connect the user to
    customer_group = store.add_customer_group("dummy_group", "dummy group")
    customer = store.add_customer(
        internal_id="custtest",
        name="Test Customer",
        scout_access=False,
        customer_group=customer_group,
        invoice_address="dummy street 1",
        invoice_reference="dummy nr",
    )
    store.add_commit(customer)

    # WHEN adding a new user
    name, email = "Paul T. Anderson", "paul.anderson@magnolia.com"
    new_user = store.add_user(customer=customer, email=email, name=name)

    store.add_commit(new_user)

    # THEN it should be stored in the database
    assert store.User.query.first() == new_user


def test_add_microbial_sample(base_store: Store, helpers):
    # GIVEN an empty database
    assert base_store.Sample.query.first() is None
    customer_obj = helpers.ensure_customer(base_store)
    assert customer_obj
    name = "microbial_sample"
    organism_name = "e. coli"
    internal_id = "lims-id"
    reference_genome = "ref_gen"
    priority = "research"
    ticket_number = 123456
    application_version = base_store.ApplicationVersion.query.first()
    base_store.add_organism(organism_name, organism_name, reference_genome)
    organism = base_store.Organism.query.first()

    # WHEN adding a new microbial sample
    new_sample = base_store.add_sample(
        application_version=application_version,
        internal_id=internal_id,
        name=name,
        organism=organism,
        priority=priority,
        reference_genome=reference_genome,
        sex="unknown",
        ticket=ticket_number,
    )
    new_sample.customer = customer_obj
    base_store.add_commit(new_sample)

    # THEN it should be stored in the database
    assert base_store.Sample.query.first() == new_sample
    stored_microbial_sample = base_store.Sample.query.first()
    assert stored_microbial_sample.name == name
    assert stored_microbial_sample.internal_id == internal_id
    assert stored_microbial_sample.reference_genome == reference_genome
    assert stored_microbial_sample.application_version == application_version
    assert stored_microbial_sample.priority_human == priority
    assert stored_microbial_sample.organism == organism


def test_add_pool(store: Store):
    # GIVEN a valid customer and a valid application_version

    customer_group = store.add_customer_group("dummy_group", "dummy group")
    new_customer = store.add_customer(
        internal_id="cust000",
        name="Test customer",
        scout_access=True,
        customer_group=customer_group,
        invoice_address="skolgatan 15",
        invoice_reference="abc",
    )
    store.add_commit(new_customer)

    application = store.add_application(
        tag="RMLS05R150",
        category="rml",
        description="Ready-made",
        percent_kth=80,
        percent_reads_guaranteed=75,
        sequencing_depth=0,
    )
    store.add_commit(application)

    app_version = store.add_version(
        application=application,
        version=1,
        valid_from=dt.today(),
        prices={"standard": 12, "priority": 222, "express": 123, "research": 12},
    )
    store.add_commit(app_version)

    # WHEN adding a new pool into the database
    new_pool = store.add_pool(
        customer=new_customer,
        name="Test",
        order="Test",
        ordered=dt.today(),
        application_version=app_version,
        data_analysis=Pipeline.FASTQ,
    )
    store.add_commit(new_pool)

    # THEN the new pool should have no_invoice = False
    pool = store.pools(customer=None).first()
    assert pool.no_invoice is False
