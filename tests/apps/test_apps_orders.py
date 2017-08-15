# -*- coding: utf-8 -*-
import pytest
import datetime as dt

from cg.apps import orders


@pytest.yield_fixture
def example(store):
    store.add_commit(store.add_customer(name='CMMS', internal_id='cust003', scout=True))

    applications = [{'tag': 'EXXCUSR000', 'category': 'wes', 'description': ''},
                    {'tag': 'WGSPCFC030', 'category': 'wgs', 'description': ''}]
    for data in applications:
        new_application = store.add_application(**data)
        store.add_commit(new_application)
        prices = dict(standard=10, priority=20, express=30, research=5)
        new_version = store.add_version(version=1, valid=dt.datetime.now(), prices=prices)
        new_version.application = new_application
        store.add_commit(new_version)
    yield {'store': store, 'application_tag': applications[0]['tag']}


def test_order_external(example):
    # GIVEN an order for external samples
    assert example['store'].families().first() is None
    assert example['store'].samples().first() is None
    data = dict(
        name='My order',
        customer='cust003',
        samples=[dict(
            name='sample1',
            application=example['application_tag'],
            sex='male',
            status='affected',
            capture_kit='Agilent SureSelect V5',
            family_name='My family',
            panels=['OMIM-AUTO']
        )]
    )

    # WHEN submitting it to the orders api
    orders_api = orders.OrdersAPI(lims=None, status=example['store'])
    order_data = orders_api.accept('external', data)

    # THEN it should update the status database with information
    assert len(order_data['families']) == 1
    assert example['store'].families().count() == 1
    new_family = example['store'].families().first()
    assert new_family.name == data['samples'][0]['family_name']
    assert isinstance(new_family.internal_id, str)

    assert example['store'].samples().count() == 1
    new_sample = example['store'].samples().first()
    assert new_sample.name == data['samples'][0]['name']
    assert isinstance(new_sample.internal_id, str)
    assert new_sample.application_version.application.tag == example['application_tag']

    assert len(new_family.links) == 1
    assert new_family.links[0].sample == new_sample


def test_order_scout(example):
    store = example['store']
    # GIVEN an empty database
    data = dict(
        name='My order 2',
        customer=store.customers().first().internal_id,
        samples=[dict(
            name='sample45',
            application=store.applications(category='wgs').first().tag,
            sex='female',
            status='affected',
            source='blood',
            container='Tube',
            father='father',
            family_name='child',
            panels=['IEM', 'EP'],
            priority='priority',
        ), dict(
            name='father',
            application=store.applications(category='wgs').first().tag,
            sex='male',
            status='unaffected',
            source='blood',
            container='Tube',
            family_name='child',
            panels=['IEM', 'EP'],
            priority='priority',
        )]
    )

    # WHEN submitting it to the orders API
    orders_api = orders.OrdersAPI(lims=None, status=example['store'])
    orders_api.accept('scout', data)

    # THEN it should store relevant info in the database
    assert example['store'].families().count() == 1
    new_family = example['store'].families().first()
    assert len(new_family.links) == 2
    for link_obj in new_family.links:
        assert link_obj.father.name == 'father' if link_obj.father else True
        assert isinstance(link_obj.status, str)
