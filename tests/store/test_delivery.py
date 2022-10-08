"""Tests for the samples to deliver api"""

import datetime as dt
from typing import Set

from cgmodels.cg.constants import Pipeline

from cg.constants import DataDelivery
from cg.store import models


def test_get_delivery_arguments(case_obj: models.Family):
    """Testing the parsing of delivery arguments from the case data_delivery."""
    # GIVEN a DataDelivery
    case_obj.data_delivery = DataDelivery.FASTQ_ANALYSIS_SCOUT

    # WHEN parsing the delivery types
    delivery_types: Set[str] = case_obj.get_delivery_arguments()

    # THEN the correct delivery types should be returned
    assert delivery_types == {Pipeline.MIP_DNA, Pipeline.FASTQ}


def test_list_samples_to_deliver(base_store, helpers):
    """Test to fetch samples ready for delivery"""
    store = base_store
    # GIVEN a populated store without samples
    assert store.samples().count() == 0
    # GIVEN inserting a sample that should be delivered
    helpers.add_sample(store, sequenced_at=dt.datetime.now())
    assert store.samples().count() == 1

    # WHEN asking for samples to deliver
    samples_to_deliver = store.samples_to_deliver()
    # THEN it should return the sample which is ready to deliver
    assert samples_to_deliver.count() == 1
    assert isinstance(samples_to_deliver.first().sequenced_at, dt.datetime)


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
    assert store.samples().count() == 2

    # WHEN asking for samples to deliver
    samples_to_deliver = store.samples_to_deliver()
    # THEN it should return the sample which is ready to deliver
    assert samples_to_deliver.count() == 1
    assert isinstance(samples_to_deliver.first().sequenced_at, dt.datetime)
