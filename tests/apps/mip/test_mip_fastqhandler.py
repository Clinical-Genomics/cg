# -*- coding: utf-8 -*-
"""Test FastqHandler"""
from datetime import datetime

from cg.apps import tb
from cg.apps.mip.fastq import MipFastqHandler
from cg.store import Store


def test_link_file_count(cg_config, link_family, simple_files_data,
                         store: Store, tb_api: tb.TrailblazerAPI):
    """Test method to test that the right number of files are created by linking"""

    # given some fastq-files belonging to family and sample
    link_files = simple_files_data
    sample = add_sample(store)

    # when calling the method to link
    MipFastqHandler(cg_config, store, tb_api).link(case=link_family, sample=sample.internal_id,
                                                   files=link_files)

    assert tb_api.link_was_called()


def ensure_application_version(disk_store, application_tag='dummy_tag'):
    """utility function to return existing or create application version for tests"""
    application = disk_store.application(tag=application_tag)
    if not application:
        application = disk_store.add_application(tag=application_tag, category='wgs',
                                                 description='dummy_description')
        disk_store.add_commit(application)

    prices = {'standard': 10, 'priority': 20, 'express': 30, 'research': 5}
    version = disk_store.application_version(application, 1)
    if not version:
        version = disk_store.add_version(application, 1, valid_from=datetime.now(),
                                         prices=prices)

        disk_store.add_commit(version)
    return version.id


def ensure_customer(disk_store, customer_id='cust_test'):
    """utility function to return existing or create customer for tests"""
    customer_group = disk_store.customer_group('dummy_group')
    if not customer_group:
        customer_group = disk_store.add_customer_group('dummy_group', 'dummy group')

        customer = disk_store.add_customer(internal_id=customer_id, name="Test Customer",
                                           scout_access=False, customer_group=customer_group,
                                           invoice_address='dummy_address',
                                           invoice_reference='dummy_reference')
        disk_store.add_commit(customer)
    customer = disk_store.customer(customer_id)
    return customer


def add_sample(disk_store, sample_id='sample_test', gender='female'):
    """utility function to add a sample to use in tests"""
    customer = ensure_customer(disk_store)
    application_version_id = ensure_application_version(disk_store)
    sample = disk_store.add_sample(name=sample_id, sex=gender)
    sample.application_version_id = application_version_id
    sample.customer = customer
    disk_store.add_commit(sample)
    return sample
