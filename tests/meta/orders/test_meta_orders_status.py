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
