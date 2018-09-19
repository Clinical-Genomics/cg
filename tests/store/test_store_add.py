from cg.store import Store


def test_add_customer(store: Store):
    # GIVEN an empty database
    assert store.Customer.query.first() is None
    internal_id, name, scout_access = 'cust000', 'Test customer', True

    # WHEN adding a new user
    new_customer = store.add_customer(internal_id=internal_id, name=name, scout_access=scout_access)
    store.add_commit(new_customer)

    # THEN it should be stored in the database
    assert store.Customer.query.first() == new_customer


def test_add_user(store: Store):
    # GIVEN a database with a customer in it that we can connect the user to
    customer = store.add_customer(internal_id='custtest', name="Test Customer", scout_access=False)
    store.add_commit(customer)

    # WHEN adding a new user
    name, email = 'Paul T. Anderson', 'paul.anderson@magnolia.com'
    new_user = store.add_user(customer=customer, email=email, name=name)

    # THEN it should be stored in the database
    assert store.User.query.first() == new_user


def test_add_microbial_sample(base_store: Store):
    # GIVEN an empty database
    assert base_store.MicrobialSample.query.first() is None
    name = 'microbial_sample'
    strain = 'other'
    strain_other = 'e. coli'
    internal_id = 'lims-id'
    reference_genome = 'ref_gen'
    priority = 'research'
    application_version = base_store.ApplicationVersion.query.first()
    microbial_order_id = 'dummy_order_id'

    # WHEN adding a new microbial sample
    new_microbial_sample = base_store.add_microbial_sample(microbial_order_id=microbial_order_id,
                                                           name=name,
                                                           strain=strain,
                                                           strain_other=strain_other,
                                                           internal_id=internal_id,
                                                           reference_genome=reference_genome,
                                                           application_version=application_version,
                                                           priority=priority)
    base_store.add_commit(new_microbial_sample)

    # THEN it should be stored in the database
    assert base_store.MicrobialSample.query.first() == new_microbial_sample
    stored_microbial_sample = base_store.MicrobialSample.query.first()
    assert stored_microbial_sample.name == name
    assert stored_microbial_sample.internal_id == internal_id
    assert stored_microbial_sample.reference_genome == reference_genome
    assert stored_microbial_sample.application_version == application_version
    assert stored_microbial_sample.priority_human == priority
    assert stored_microbial_sample.strain == strain
    assert stored_microbial_sample.strain_other == strain_other
