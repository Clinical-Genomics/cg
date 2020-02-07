def test_microbial_sample_to_dict(microbial_store):

    # GIVEN a store with a Microbial sample
    assert microbial_store.microbial_samples().count() > 0

    # WHEN running to dict on that sample
    a_dict = microbial_store.microbial_samples().first().to_dict(order=True)

    # THEN you should get a dictionary with
    assert a_dict["id"]
    assert a_dict["internal_id"]
    assert a_dict["name"]
    assert a_dict["application_version_id"]
    assert a_dict["microbial_order_id"]
    assert a_dict["created_at"]
    assert a_dict["organism"]
    assert a_dict["organism_id"]
    assert a_dict["reference_genome"]
    assert a_dict["priority"]
    assert a_dict["reads"]
    assert a_dict["comment"]
    assert a_dict["microbial_order"]
    assert a_dict["application"]
    assert a_dict["application_version"]


def test_order_sample_to_dict(microbial_store):

    # GIVEN a store with a Microbial sample
    assert microbial_store.microbial_orders().count() > 0

    # WHEN running to dict on that sample
    a_dict = microbial_store.microbial_orders().first().to_dict(samples=True)

    # THEN you should get a dictionary with
    assert a_dict["id"]
    assert a_dict["internal_id"]
    assert a_dict["name"]
    assert a_dict["ticket_number"]
    assert a_dict["comment"]
    assert a_dict["created_at"]
    assert a_dict["updated_at"]
    assert a_dict["ordered_at"]
    assert a_dict["customer_id"]
    assert a_dict["microbial_samples"]
    assert a_dict["customer"]
