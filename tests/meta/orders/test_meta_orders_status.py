import datetime as dt

from cg.meta.orders.status import StatusHandler


def test_pools_to_status(rml_order):
    # GIVEN a rml order with three samples in one pool
    # WHEN parsing for status
    data = StatusHandler.pools_to_status(rml_order)
    # THEN it should pick out the general information
    assert data['customer'] == 'cust001'
    assert data['order'] == 'ctDNA sequencing - order 9'
    # ... and information about the pool(s)
    assert len(data['pools']) == 1
    assert data['pools'][0]['name'] == '1'
    assert data['pools'][0]['application'] == 'RMLS05R150'


def test_samples_to_status(fastq_order):
    # GIVEN fastq order with two samples
    # WHEN parsing for status
    data = StatusHandler.samples_to_status(fastq_order)
    # THEN it should pick out samples and relevant information
    assert len(data['samples']) == 2
    first_sample = data['samples'][0]
    assert first_sample['name'] == 'sample-normal'
    assert first_sample['application'] == 'WGSPCFC060'
    assert first_sample['priority'] == 'priority'
    assert first_sample['tumour'] is False

    # ... and the other sample is a tumour
    assert data['samples'][1]['tumour'] is True


def test_families_to_status(scout_order):
    # GIVEN a scout order with a trio family
    # WHEN parsing for status
    data = StatusHandler.families_to_status(scout_order)
    # THEN it should pick out the family
    assert len(data['families']) == 1
    family = data['families'][0]
    assert family['name'] == '17093'
    assert family['priority'] == 'standard'
    assert set(family['panels']) == set(['IEM', 'EP'])
    assert len(family['samples']) == 3

    first_sample = family['samples'][0]
    assert first_sample['name'] == '17093-I-2A'
    assert first_sample['application'] == 'WGTPCFC030'
    assert first_sample['sex'] == 'female'
    assert first_sample['status'] == 'affected'
    assert first_sample['mother'] == '17093-II-2U'
    assert first_sample['father'] == '17093-II-1U'

    # ... second sample has a comment
    assert isinstance(family['samples'][1]['comment'], str)


def test_store_pools(orders_api, base_store, rml_status_data):
    # GIVEN a basic store with no samples and a rml order
    assert base_store.pools().count() == 0
    # WHEN storing the order
    new_pools = orders_api.store_pools(
        customer=rml_status_data['customer'],
        order=rml_status_data['order'],
        ordered=dt.datetime.now(),
        ticket=1234348,
        pools=rml_status_data['pools'],
    )
    # THEN it should update the database with new pools
    assert len(new_pools) == 1
    assert base_store.pools().count() == 1
    new_pool = base_store.pools().first()
    assert new_pool == new_pools[0]
    assert new_pool.name == '1'
    assert new_pool.application_version.application.tag == 'RMLS05R150'
    # ... and add a delivery
    assert len(new_pool.deliveries) == 1
    assert new_pool.deliveries[0].destination == 'caesar'


def test_store_samples(orders_api, base_store, fastq_status_data):
    # GIVEN a basic store with no samples and a fastq order
    assert base_store.samples().count() == 0
    assert base_store.families().count() == 0
    # WHEN stoting the order
    new_samples = orders_api.store_samples(
        customer=fastq_status_data['customer'],
        order=fastq_status_data['order'],
        ordered=dt.datetime.now(),
        ticket=1234348,
        samples=fastq_status_data['samples'],
    )
    # THEN it should store the samples and create a "fake" family for
    # the non-tumour sample
    assert len(new_samples) == 2
    assert base_store.samples().count() == 2
    assert base_store.families().count() == 1
    first_sample = new_samples[0]
    assert len(first_sample.links) == 1
    family_link = first_sample.links[0]
    assert family_link.family == base_store.families().first()
    for sample in new_samples:
        assert len(sample.deliveries) == 1


def test_store_families(orders_api, base_store, scout_status_data):
    # GIVEN a basic store with no samples or nothing in it + scout order
    assert base_store.samples().first() is None
    assert base_store.families().first() is None
    # WHEN storing the order
    new_families = orders_api.store_families(
        customer=scout_status_data['customer'],
        order=scout_status_data['order'],
        ordered=dt.datetime.now(),
        ticket=1234567,
        families=scout_status_data['families'],
    )
    # THEN it should create and link samples and the family
    family_obj = base_store.families().first()
    assert len(new_families) == 1
    new_family = new_families[0]
    assert new_family == family_obj
    assert new_family.name == '17093'
    assert set(new_family.panels) == set(['IEM', 'EP'])
    assert new_family.priority_human == 'standard'

    assert len(new_family.links) == 3
    new_link = new_family.links[0]
    assert new_link.status == 'affected'
    assert new_link.mother.name == '17093-II-2U'
    assert new_link.father.name == '17093-II-1U'
    assert new_link.sample.name == '17093-I-2A'
    assert new_link.sample.sex == 'female'
    assert new_link.sample.application_version.application.tag == 'WGTPCFC030'
    assert isinstance(new_family.links[1].sample.comment, str)

    assert base_store.deliveries().count() == base_store.samples().count()
    for link in new_family.links:
        assert len(link.sample.deliveries) == 1
