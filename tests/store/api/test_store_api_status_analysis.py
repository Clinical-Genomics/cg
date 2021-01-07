"""This script tests the cli methods to add families to status-db"""
from datetime import datetime, timedelta

from cg.constants import Pipeline, DataDelivery
from cg.store import Store


def test_that_many_families_can_have_one_sample_each(base_store: Store, helpers):
    """Test that tests that families are returned even if there are many result rows in the query"""

    # GIVEN a database with two families one with 50 sequenced samples
    # the other family with one
    n_test_families = 50
    test_families = add_families_with_samples(
        base_store, helpers, n_test_families, sequenced_at=datetime.now()
    )

    # WHEN getting families to analyse
    families = base_store.cases_to_analyze(pipeline=Pipeline.MIP_DNA)

    # THEN families should contain the test family
    assert len(families) == len(test_families)


def test_that_families_can_have_many_samples(base_store: Store, helpers):
    """Test that tests that families are returned even if there are many result rows in the query"""

    # GIVEN a database with two families one with 50 sequenced samples
    # the other family with one
    default_limit = 50
    test_family_50 = add_family_with_samples(
        base_store, helpers, "test_family_50åäp+ölo0l", default_limit, sequenced_at=datetime.now()
    )
    test_sample = helpers.add_sample(base_store, sequenced_at=datetime.now())
    test_family = helpers.add_case(base_store, "family_one_sample")
    base_store.relate_sample(test_family, test_sample, "unknown")

    # WHEN getting families to analyse
    families = base_store.cases_to_analyze(pipeline=Pipeline.MIP_DNA)

    # THEN families should contain the test family
    assert families
    assert test_family_50 in families
    assert test_family in families


def test_external_sample_to_re_analyse(base_store: Store, helpers):
    """Test that a family marked for re-analyse with one sample external not sequenced inhouse and
    with completed analysis do show up among the families to analyse"""

    # GIVEN a database with a family with one not sequenced external sample and completed analysis
    pipeline = Pipeline.MIP_DNA
    test_sample = helpers.add_sample(base_store, sequenced_at=None, is_external=True)
    test_analysis = helpers.add_analysis(base_store, completed_at=datetime.now(), pipeline=pipeline)
    test_analysis.family.action = "analyze"
    base_store.relate_sample(test_analysis.family, test_sample, "unknown")

    # WHEN getting families to analyse
    families = base_store.cases_to_analyze(pipeline=pipeline)

    # THEN families should contain the test family
    assert families
    assert test_analysis.family in families


def test_family_to_re_analyse(base_store: Store, helpers):
    """Test that a family marked for re-analyse with one sample that has been sequenced and
    with completed analysis do show up among the families to analyse"""

    # GIVEN a database with a family with one of one sequenced samples and completed analysis
    pipeline = Pipeline.MIP_DNA
    test_sample = helpers.add_sample(base_store, sequenced_at=datetime.now())
    assert test_sample.sequenced_at
    test_analysis = helpers.add_analysis(base_store, completed_at=datetime.now(), pipeline=pipeline)
    assert test_analysis.completed_at
    test_analysis.family.action = "analyze"
    assert test_analysis.family.action == "analyze"
    base_store.relate_sample(test_analysis.family, test_sample, "unknown")

    # WHEN getting families to analyse
    families = base_store.cases_to_analyze(pipeline=pipeline)

    # THEN families should contain the test family
    assert families
    assert test_analysis.family in families


def test_all_samples_and_analysis_completed(base_store: Store, helpers):
    """Test that a family with one sample that has been sequenced and with completed
    analysis don't show up among the families to analyse"""

    # GIVEN a database with a family with one of one sequenced samples and completed analysis
    test_sample = helpers.add_sample(base_store, sequenced_at=datetime.now())
    test_analysis = helpers.add_analysis(base_store, completed_at=datetime.now())
    test_analysis.family.action = "analyze"
    base_store.relate_sample(test_analysis.family, test_sample, "unknown")

    # WHEN getting families to analyse
    families = base_store.cases_to_analyze(pipeline=Pipeline.MIP_DNA)

    # THEN families should not contain the test family

    assert not families


def test_specified_analysis_in_result(base_store: Store, helpers):
    """Test that a family with one sample that has specified data_analysis does show up"""

    # GIVEN a database with a family with one sequenced samples for MIP analysis
    pipeline = Pipeline.BALSAMIC
    test_sample = helpers.add_sample(base_store, sequenced_at=datetime.now())
    test_family = helpers.add_case(base_store, data_analysis=pipeline)
    base_store.relate_sample(test_family, test_sample, "unknown")

    # WHEN getting families to analyse
    families = base_store.cases_to_analyze(pipeline=pipeline)

    # THEN families should contain the test family
    assert families
    assert test_family in families


def test_exclude_other_pipeline_analysis_from_result(base_store: Store, helpers):
    """Test that a family with specified analysis and with one sample does not show up among
    others"""

    # GIVEN a database with a family with one sequenced samples for specified analysis
    test_sample = helpers.add_sample(base_store, sequenced_at=datetime.now())
    test_family = helpers.add_case(base_store, data_analysis=Pipeline.BALSAMIC)
    base_store.relate_sample(test_family, test_sample, "unknown")

    # WHEN getting families to analyse
    families = base_store.cases_to_analyze(pipeline=Pipeline.MIP_DNA)

    # THEN families should not contain the test family
    assert not families


def test_one_of_two_sequenced_samples(base_store: Store, helpers):
    """Test that a family with one of one samples that has been sequenced shows up among the
    families to analyse"""

    # GIVEN a database with a family with one of one sequenced samples and no analysis
    test_family = helpers.add_case(base_store)
    test_sample1 = helpers.add_sample(base_store, sequenced_at=datetime.now())
    test_sample2 = helpers.add_sample(base_store, sequenced_at=None)
    base_store.relate_sample(test_family, test_sample1, "unknown")
    base_store.relate_sample(test_family, test_sample2, "unknown")

    # WHEN getting families to analyse
    families = base_store.cases_to_analyze(pipeline=Pipeline.MIP_DNA)

    # THEN families should not contain the test family
    assert not families


def test_one_of_one_sequenced_samples(base_store: Store, helpers):
    """Test that a family with one of one samples that has been sequenced shows up among the
    families to analyse"""

    # GIVEN a database with a family with one of one sequenced samples and no analysis
    test_family = helpers.add_case(base_store)
    test_sample = helpers.add_sample(base_store, sequenced_at=datetime.now())
    base_store.relate_sample(test_family, test_sample, "unknown")
    assert test_sample.sequenced_at is not None

    # WHEN getting families to analyse
    families = base_store.cases_to_analyze(pipeline=Pipeline.MIP_DNA)

    # THEN families should contain the test family
    assert families
    assert test_family in families


def relate_samples(base_store, family, samples):
    """utility function to relate many samples to one family"""

    for sample in samples:
        base_store.relate_sample(family, sample, "unknown")


def add_family_with_samples(base_store, helpers, family_name, n_samples, sequenced_at):
    """utility function to add one family with many samples to use in tests"""

    test_samples = helpers.add_samples(base_store, n_samples)
    for sample in test_samples:
        sample.sequenced_at = sequenced_at
    test_family = helpers.add_case(base_store, family_name)
    relate_samples(base_store, test_family, test_samples)
    return test_family


def add_families_with_samples(base_store, helpers, n_families, sequenced_at):
    """utility function to add many families with two samples to use in tests"""

    families = []
    for i in range(n_families):
        family = add_family_with_samples(base_store, helpers, f"f{i}", 2, sequenced_at=sequenced_at)
        families.append(family)
    return families
