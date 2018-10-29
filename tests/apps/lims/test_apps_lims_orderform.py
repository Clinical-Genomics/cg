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
    assert sample_data['well_position'] is None
    assert sample_data['well_position_rml'] == 'A:1'
    assert sample_data['pool'] == 'pool-1'
    assert sample_data['volume'] == '30'
    assert sample_data['concentration'] == '5'


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
    assert normal_sample['name'] == 'prov1'
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
    assert mother_sample['quantity'] == '220'
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


def test_parsing_metagenome_orderform(metagenome_orderform):
    # GIVEN an orderform for one metagenome sample
    # WHEN parsing the file
    data = orderform.parse_orderform(metagenome_orderform)
    # THEN it should detect the project type
    assert data['project_type'] == 'metagenome'
    # ... and find all samples
    assert len(data['items']) == 2
    # ... and collect relevant sample info
    sample = data['items'][0]

    assert sample['name'] == 'Bristol'
    assert sample['container'] == '96 well plate'
    assert sample['application'] == 'METPCFR020'
    assert sample['customer'] == 'cust000'
    assert sample['source'] == 'faeces'
    assert sample['priority'] == 'standard'
    assert sample['elution_buffer'] == 'EB-buffer'
    assert sample['container_name'] == 'Platen'
    assert sample['well_position'] == 'A:1'
    assert sample['concentration_weight'] == '2'
    assert sample['quantity'] == '10'
    assert sample['extraction_method'] == 'best'
    assert sample['comment'] == '5 on the chart'

    
def test_parsing_microbial_orderform(microbial_orderform):
    # GIVEN a path to a microbial orderform with 3 samples

    # WHEN parsing the file
    data = orderform.parse_orderform(microbial_orderform)

    # THEN it should determine the type of project and customer
    assert data['project_type'] == 'microbial'
    assert data['customer'] == 'cust015'

    # ... and find all samples
    assert len(data['items']) == 5

    # ... and collect relevant sample data
    sample_data = data['items'][0]

    assert sample_data['name'] == 'all-fields'
    assert sample_data.get('internal_id') is None
    assert sample_data['organism'] == 'Other'
    assert sample_data['reference_genome'] == 'NC_111'
    assert sample_data['application'] == 'MWRNXTR003'
    assert sample_data['require_qcok'] is True
    assert sample_data['elution_buffer'] == 'Nuclease-free water'
    assert sample_data['container'] == '96 well plate'
    assert sample_data['container_name'] == 'name of plate'
    assert sample_data.get('volume') is None
    assert sample_data.get('concentration') is None
    assert sample_data['well_position'] == 'A:1'
    assert sample_data.get('tumour') is False
    assert sample_data.get('source') is None
    assert sample_data.get('priority') in 'research'
    assert sample_data['organism_other'] == 'M.upium'
    assert sample_data['extraction_method'] == 'MagNaPure 96 (contact Clinical Genomics before submission)'
    assert sample_data['comment'] == 'plate comment'
    assert sample_data['concentration_weight'] == '101'
    assert sample_data['quantity'] == '102'
    