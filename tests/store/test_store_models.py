from cg.store import Store


def test_microbial_sample_to_dict(microbial_store : Store, helpers):

    # GIVEN a store with a Microbial sample
    sample_obj = helpers.add_microbial_sample_and_order(microbial_store)
    microbial_store.add_commit(sample_obj)
    assert sample_obj

    # WHEN running to dict on that sample
    a_dict = sample_obj.to_dict(links=True)

    # THEN you should get a dictionary with
    assert a_dict["id"]
    assert a_dict["internal_id"]
    assert a_dict["name"]
    assert a_dict["application_version_id"]
    assert a_dict["links"]
    assert a_dict["created_at"]
    assert a_dict["priority"]
    assert a_dict["reads"]
    assert a_dict["comment"]
    assert a_dict["application"]
    assert a_dict["application_version"]


def test_microbial_order_to_dict(microbial_store, helpers):

    # GIVEN a store with a Microbial order and sample
    helpers.add_microbial_sample_and_order(microbial_store)
    assert microbial_store.microbial_orders().count() > 0

    # WHEN running to dict on that sample
    a_dict = microbial_store.microbial_orders().first().to_dict(links=True)

    # THEN you should get a dictionary with
    assert a_dict["id"]
    assert a_dict["internal_id"]
    assert a_dict["name"]
    assert a_dict["created_at"]
    assert a_dict["ordered_at"]
    assert a_dict["customer_id"]
    assert a_dict["links"]
    assert a_dict["customer"]
