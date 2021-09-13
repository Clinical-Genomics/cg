from cg.store import Store, models


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


def test_sample_positive_control_is_positive_control(sample_store: Store, helpers):

    # GIVEN a sample that is not a positive control
    sample: models.Sample = helpers.add_sample(store=sample_store)
    assert not sample.is_positive_control

    # WHEN setting it as negative control
    sample.is_positive_control = True

    # THEN it should report a positive control
    assert sample.is_positive_control


def test_sample_positive_control_is_control(sample_store: Store, helpers):

    # GIVEN a sample that is not a control
    sample: models.Sample = helpers.add_sample(store=sample_store)
    assert not sample.is_control

    # WHEN setting it as positive control
    sample.is_positive_control = True

    # THEN it should report a control
    assert sample.is_control


def test_sample_negative_control_is_negative_control(sample_store: Store, helpers):

    # GIVEN a sample that is not a negative control
    sample: models.Sample = helpers.add_sample(store=sample_store)
    assert not sample.is_negative_control

    # WHEN setting it as negative control
    sample.is_negative_control = True

    # THEN it should report a negative control
    assert sample.is_negative_control


def test_sample_negative_control_is_control(sample_store: Store, helpers):

    # GIVEN a sample that is not a control
    sample: models.Sample = helpers.add_sample(store=sample_store)
    assert not sample.is_control

    # WHEN setting it as negative control
    sample.is_negative_control = True

    # THEN it should report a control
    assert sample.is_control
