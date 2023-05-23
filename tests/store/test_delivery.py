"""Tests for the samples to deliver api"""

import datetime as dt
from typing import List, Set

from cg.constants import DataDelivery
from cg.store.models import Family, Sample
from cgmodels.cg.constants import Pipeline


def test_get_delivery_arguments(case: Family):
    """Testing the parsing of delivery arguments from the case data_delivery."""
    # GIVEN a DataDelivery
    case.data_delivery = DataDelivery.FASTQ_ANALYSIS_SCOUT

    # WHEN parsing the delivery types
    delivery_types: Set[str] = case.get_delivery_arguments()

    # THEN the correct delivery types should be returned
    assert delivery_types == {Pipeline.MIP_DNA, Pipeline.FASTQ}


def test_list_samples_to_deliver(base_store, helpers):
    """Test to fetch samples ready for delivery"""
    store = base_store
    # GIVEN a populated store without samples
    assert len(store._get_query(table=Sample).all()) == 0
    # GIVEN inserting a sample that should be delivered
    helpers.add_sample(store, sequenced_at=dt.datetime.now())
    assert len(store._get_query(table=Sample).all()) == 1

    # WHEN asking for samples to deliver
    samples_to_deliver: List[Sample] = store.get_samples_to_deliver()
    # THEN it should return the sample which is ready to deliver
    assert len(samples_to_deliver) == 1
    assert isinstance(samples_to_deliver[0].sequenced_at, dt.datetime)


def test_list_samples_to_deliver_multiple_samples(base_store, helpers):
    """Test to fetch samples ready for delivery and avoid the ones that are not"""
    store = base_store
    # GIVEN a populated store with two samples where one is scheduled for delivery
    helpers.add_sample(store, sequenced_at=dt.datetime.now())
    helpers.add_sample(
        store,
        name="delivered",
        sequenced_at=dt.datetime.now(),
        delivered_at=dt.datetime.now(),
    )
    assert len(store._get_query(table=Sample).all()) == 2

    # WHEN asking for samples to deliver
    samples_to_deliver: List[Sample] = store.get_samples_to_deliver()
    # THEN it should return the sample which is ready to deliver
    assert len(samples_to_deliver) == 1
    assert isinstance(samples_to_deliver[0].sequenced_at, dt.datetime)
