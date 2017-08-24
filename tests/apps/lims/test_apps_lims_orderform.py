# -*- coding: utf-8 -*-
from cg.apps.lims import orderform


def test_parsing_rml_orderform(rml_orderform):
    # GIVEN a path to a RML orderform with 2 sample in a pool
    # WHEN parsing the file
    data = orderform.parse_orderform(rml_orderform)
    # THEN it should determine the type of project and customer
    assert data['project_type'] == 'rml'
    assert data['customer'] == 'cust001'
    # ... and find all samples
    assert len(data['items']) == 2
    # ... and collect relevant sample data
    sample_data = data['items'][0]
    assert sample_data['well_position'] == 'A:1'
    assert sample_data['pool'] == 1
    assert sample_data['volume'] == 30
    assert sample_data['concentration'] == 5
    assert isinstance(sample_data['container_name'], str)


def test_parsing_fastq_orderform(fastq_orderform):
    # GIVEN a FASTQ orderform with 2 samples, one normal, one tumour
    # WHEN paring the file
    data = orderform.parse_orderform(fastq_orderform)
    # THEN it should determine the project type
    assert data['project_type'] == 'fastq'
    # ... and find all samples
    assert len(data['items']) == 2
    # ... and collect relevant sample info
    normal_sample = data['items'][0]
    tumour_sample = data['items'][1]
    assert normal_sample['name'] == 'prov 1'
    assert normal_sample['container'] == 'Tube'
    assert normal_sample['application'] == 'WGSPCFC030'
    assert normal_sample['sex'] == 'male'
    assert normal_sample['source'] == 'blood'
    assert normal_sample['priority'] == 'priority'
    assert normal_sample['tumour'] is False
    assert tumour_sample['tumour'] is True
    assert tumour_sample['source'] == 'cell line'


def test_parsing_scout_orderform(scout_orderform):
    # GIVEN an order form for a Scout order with 4 samples, 1 trio, in a plate
    # WHEN parsing the order form
    data = orderform.parse_orderform(scout_orderform)
    # THEN it should detect the type of project
    assert data['project_type'] == 'scout'
    # ... and it should find and group all samples in families
    assert len(data['items']) == 2
    # ... and collect relevant data about the families
    trio_family = data['items'][0]
    assert len(trio_family['samples']) == 3
    assert trio_family['name'] == 'family1'
    assert trio_family['priority'] == 'standard'
    assert trio_family['panels'] == ['IEM']
    assert trio_family['require_qcok'] is True
    # ... and collect relevant info about the samples
    proband_sample = trio_family['samples'][0]
    assert proband_sample['container'] == '96 well plate'
    assert proband_sample['container_name'] == 'CMMS'
    assert proband_sample['status'] == 'affected'
    assert proband_sample['mother'] == 'sample2'
    assert proband_sample['father'] == 'sample3'
    mother_sample = trio_family['samples'][1]
    assert mother_sample.get('mother') is None
    assert mother_sample['quantity'] == 220
    assert isinstance(mother_sample['comment'], str)


def test_parsing_external_orderform(external_orderform):
    # GIVEN an orderform for two external samples, one WES, one WGS
    # WHEN parsing the file
    data = orderform.parse_orderform(external_orderform)
    # THEN it should detect the project type
    assert data['project_type'] == 'external'
    # ... and find all families (1) and samples (2)
    assert len(data['items']) == 1
    family = data['items'][0]
    assert set(family['panels']) == set(['CILM', 'CTD'])
    # ... and collect info about the samples
    wes_sample = family['samples'][0]
    wgs_sample = family['samples'][1]
    assert wes_sample['capture_kit'] == 'Agilent Sureselect V5'
    assert wgs_sample.get('capture_kit') is None
