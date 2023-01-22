from cg.store import Store


def test_microbial_sample_to_dict(microbial_store: Store, helpers):

    # GIVEN a store with a Microbial sample
    sample_obj = helpers.add_microbial_sample(microbial_store)
    microbial_store.add_commit(sample_obj)
    assert sample_obj

    # WHEN running to dict on that sample
    a_dict = sample_obj.to_dict(links=True)

    # THEN you should get a dictionary with
    assert a_dict["id"]
    assert a_dict["internal_id"]
    assert a_dict["name"]
    assert a_dict["application_version_id"]
    assert a_dict["created_at"]
    assert a_dict["priority"]
    assert a_dict["reads"]
    assert a_dict["comment"]
    assert a_dict["application"]
    assert a_dict["application_version"]


def test_no_collaborators(base_store):
    # GIVEN a customer without collaborations
    new_customer_id = "cust004"
    customer = base_store.add_customer(
        new_customer_id,
        "No-colab",
        scout_access=True,
        invoice_address="Test street",
        invoice_reference="ABCDEF",
    )
    # WHEN calling the collaborators property
    collaborators = customer.collaborators
    # THEN only the customer should be returned
    assert len(collaborators) == 1
    assert collaborators.pop().internal_id == new_customer_id


def test_collaborators(base_store, customer_id):
    # GIVEN a customer with one collaboration
    customer = base_store.customer(customer_id)
    assert all(
        customer_obj.internal_id
        in [
            "cust001",
            "cust002",
            "cust003",
            customer_id,
        ]
        for customer_obj in customer.collaborations[0].customers
    )

    # WHEN calling the collaborators property
    # THEN the customer and the collaborators should be returned
    collaborators = customer.collaborators
    assert len(collaborators) == 4
    assert all(
        collaborator.internal_id
        in [
            "cust001",
            "cust002",
            "cust003",
            customer_id,
        ]
        for collaborator in collaborators
    )


def test_multiple_collaborations(base_store, customer_id):
    # Given a customer in two collaborations
    collaboration = base_store.add_collaboration("small_collaboration", "small collaboration")
    new_customer_id = "cust004"
    new_customer = base_store.add_customer(
        new_customer_id,
        "No-colab",
        scout_access=True,
        invoice_address="Test street",
        invoice_reference="ABCDEF",
    )
    prod_customer = base_store.customer(customer_id)
    collaboration.customers.extend([prod_customer, new_customer])
    base_store.add_commit(new_customer, collaboration)
    base_store.refresh(collaboration)
    # WHEN calling the collaborators property
    collaborators = prod_customer.collaborators
    # THEN all customers in both collaborations should be returned
    assert len(collaborators) == 5
    assert all(
        collaborator.internal_id in ["cust001", new_customer_id, "cust002", "cust003", customer_id]
        for collaborator in collaborators
    )
