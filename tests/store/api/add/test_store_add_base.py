from datetime import datetime as dt

from cg.store import Store
from cg.store.models import ApplicationVersion, Collaboration, Customer, Organism, Sample, User


def test_add_collaboration(store: Store):
    # GIVEN an empty database
    collaboration_query = store._get_query(table=Collaboration)
    assert collaboration_query.first() is None
    internal_id, name = "cust_group", "Test customer group"

    # WHEN adding a new customer group
    new_collaboration = store.add_collaboration(internal_id=internal_id, name=name)
    store.session.add(new_collaboration)
    store.session.commit()

    # THEN it should be stored in the database
    assert collaboration_query.first() == new_collaboration


def test_add_user(store: Store):
    # GIVEN a database with a customer in it that we can connect the user to
    customer = store.add_customer(
        internal_id="custtest",
        name="Test Customer",
        scout_access=False,
        invoice_address="dummy street 1",
        invoice_reference="dummy nr",
    )
    store.session.add(customer)

    # WHEN adding a new user
    name, email = "Paul T. Anderson", "paul.anderson@magnolia.com"
    new_user = store.add_user(customer=customer, email=email, name=name)

    store.session.add(new_user)
    store.session.commit()

    # THEN it should be stored in the database
    assert store._get_query(table=User).first() == new_user


def test_add_microbial_sample(base_store: Store, helpers):
    # GIVEN an empty database
    sample_query = base_store._get_query(table=Sample)
    assert sample_query.first() is None
    customer_obj = helpers.ensure_customer(base_store)
    assert customer_obj
    name = "microbial_sample"
    organism_name = "e. coli"
    internal_id = "lims-id"
    reference_genome = "ref_gen"
    priority = "research"
    application_version = base_store._get_query(table=ApplicationVersion).first()
    base_store.add_organism(organism_name, organism_name, reference_genome)
    organism = base_store._get_query(table=Organism).first()

    # WHEN adding a new microbial sample
    new_sample = base_store.add_sample(
        name=name,
        sex="unknown",
        internal_id=internal_id,
        priority=priority,
        application_version=application_version,
        organism=organism,
        reference_genome=reference_genome,
    )
    new_sample.customer = customer_obj
    base_store.session.add(new_sample)
    base_store.session.commit()

    # THEN it should be stored in the database
    assert sample_query.first() == new_sample
    stored_microbial_sample = sample_query.first()
    assert stored_microbial_sample.name == name
    assert stored_microbial_sample.internal_id == internal_id
    assert stored_microbial_sample.reference_genome == reference_genome
    assert stored_microbial_sample.application_version == application_version
    assert stored_microbial_sample.priority_human == priority
    assert stored_microbial_sample.organism == organism


def test_add_pool(rml_pool_store: Store):
    """Tests whether new pools are invoiced as default."""
    # GIVEN a valid customer and a valid application_version
    customer: Customer = rml_pool_store.get_customers()[0]
    application = rml_pool_store.get_application_by_tag(tag="RMLP05R800")
    app_version = (
        rml_pool_store._get_query(table=ApplicationVersion)
        .filter(ApplicationVersion.application_id == application.id)
        .first()
    )

    # WHEN adding a new pool
    new_pool = rml_pool_store.add_pool(
        customer=customer,
        name="pool2",
        order="123456",
        ordered=dt.now(),
        application_version=app_version,
    )

    rml_pool_store.session.add(new_pool)
    rml_pool_store.session.commit()
    # THEN the new pool should have no_invoice = False
    pool = rml_pool_store.get_pool_by_entry_id(entry_id=2)
    assert pool.no_invoice is False
