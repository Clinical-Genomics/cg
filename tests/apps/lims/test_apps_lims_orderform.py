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
    assert sample_data['name'] == 'AL-P-00110710-N-03099696-TP20170817-CB20170822'
    assert sample_data['pool'] == 'pool-1'
    assert sample_data['application'] == 'RMLP10R150'
    assert sample_data['data_analysis'] == 'fastq'
    assert sample_data['volume'] == '30'
    assert sample_data['concentration'] == '5'
    assert sample_data['index'] == 'TruSeq DNA HT Dual-index (D7-D5)'
    assert sample_data['index_number'] == '1'

    assert sample_data['container_name'] is None
    assert sample_data['rml_plate_name'] == '20170823-ALASCCA 27, #811137, J.Lindberg'
    assert sample_data['well_position'] is None
    assert sample_data['well_position_rml'] == 'A:1'

    assert sample_data['reagent_label'] == 'A01 - D701-D501 (ATTACTCG-TATAGCCT)'

    assert sample_data['custom_index'] == 'B01 - D701-D501 (ATTACTCG-TATAGCCT)'

    assert sample_data['comment'] == 'sample comment'
    assert sample_data['capture_kit'] == 'Agilent Sureselect CRE'


def test_parsing_fastq_orderform(fastq_orderform):

    # GIVEN a FASTQ orderform with 2 samples, one normal, one tumour
    # WHEN parsing the file
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
    assert normal_sample['data_analysis'] == 'fastq'
    assert normal_sample['application'] == 'WGSPCFC030'
    assert normal_sample['sex'] == 'male'
    assert normal_sample['family'] == 'family1'
    assert data['customer'] == 'cust009'
    assert normal_sample['require_qcok'] == True
    assert normal_sample['source'] == 'blood'
    assert normal_sample['priority'] == 'priority'

    assert normal_sample['container_name'] == 'plateA'
    assert normal_sample['well_position'] == 'A:1'

    assert normal_sample['tumour'] is False

    assert normal_sample['quantity'] == '1'
    assert normal_sample['comment'] == 'sample comment'

    assert tumour_sample['tumour'] is True
    assert tumour_sample['source'] == 'cell line'


def test_parsing_scout_orderform(scout_orderform):

    # GIVEN an order form for a Scout order with 4 samples, 1 trio, in a plate
    # WHEN parsing the order form
    data = orderform.parse_orderform(scout_orderform)

    # THEN it should detect the type of project
    assert data['project_type'] == 'scout'
    assert data['customer'] == 'cust003'
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
    assert proband_sample['name'] == 'sample1'
    assert proband_sample['container'] == '96 well plate'
    assert proband_sample['data_analysis'] == 'MIP'
    assert proband_sample['application'] == 'WGSLIFC030'
    assert proband_sample['sex'] == 'female'
    # family-id on the family
    # customer on the order (data)
    # require-qc-ok on the family
    assert proband_sample['source'] == 'tissue (fresh frozen)'

    assert proband_sample['container_name'] == 'CMMS'
    assert proband_sample['well_position'] == 'A:1'

    # panels on the family
    assert proband_sample['status'] == 'affected'

    assert proband_sample['mother'] == 'sample2'
    assert proband_sample['father'] == 'sample3'

    # todo: assert proband_sample['tumour'] is False

    mother_sample = trio_family['samples'][1]
    assert mother_sample.get('mother') is None
    assert mother_sample['quantity'] == '220'
    assert mother_sample['comment'] == 'this is a sample comment'


def test_parsing_external_orderform(external_orderform):

    # GIVEN an orderform for two external samples, one WES, one WGS
    # WHEN parsing the file
    data = orderform.parse_orderform(external_orderform)

    # THEN it should detect the project type
    assert data['project_type'] == 'external'
    assert data['customer'] == 'cust002'

    # ... and find all families (1) and samples (2)
    assert len(data['items']) == 4
    family = data['items'][0]
    assert family['name'] == 'fam2'
    assert family['priority'] == 'standard'
    assert set(family['panels']) == set(['CILM', 'CTD'])
    # todo: assert set(family['additional_gene_list']) == set(['16PDEL'])

    # ... and collect info about the samples
    wes_sample = family['samples'][0]
    wgs_sample = family['samples'][1]

    assert wes_sample['capture_kit'] == 'Agilent Sureselect V5'
    assert wes_sample['application'] == 'EXXCUSR000'
    assert wes_sample['sex'] == 'male'
    # family name on family
    # priority on family
    # customer on order (data)
    assert wes_sample['source'] == 'blood'

    # panels on family
    # additional gene list on family
    assert wes_sample['status'] == 'affected'

    assert wes_sample['mother'] == 'mother'
    assert wes_sample['father'] == 'father'
    # todo: assert wes_sample['other'] == 'other', check if removed in latest OF

    # todo: assert wes_sample['tumour'] == 'Tumor'
    # todo: assert wes_sample['gel_picture'] == 'Y'
    # todo: assert wes_sample['extraction_method'] == 'extraction method'
    assert wes_sample['comment'] == 'sample comment'

    assert wgs_sample.get('capture_kit') == 'Agilent Sureselect CRE'


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
    assert sample['data_analysis'] == 'fastq'
    assert sample['application'] == 'METPCFR020'
    assert sample['customer'] == 'cust000'
    assert sample['require_qcok'] is False
    assert sample['elution_buffer'] == 'EB-buffer'
    assert sample['source'] == 'faeces'
    assert sample['priority'] == 'standard'

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
    assert sample_data['organism'] == 'other'
    assert sample_data['reference_genome'] == 'NC_111'
    assert sample_data['data_analysis'] == 'fastq'
    assert sample_data['application'] == 'MWRNXTR003'
    # customer on order (data)
    assert sample_data['require_qcok'] is True
    assert sample_data['elution_buffer'] == 'Nuclease-free water'
    assert sample_data['extraction_method'] == 'MagNaPure 96 (contact Clinical Genomics before ' \
                                               'submission)'
    assert sample_data['container'] == '96 well plate'
    assert sample_data.get('priority') in 'research'

    assert sample_data['container_name'] == 'name of plate'
    assert sample_data['well_position'] == 'A:1'

    assert sample_data['organism_other'] == 'M.upium'

    assert sample_data['concentration_weight'] == '101'
    assert sample_data['quantity'] == '102'
    assert sample_data['comment'] == 'plate comment'


def test_parsing_cancer_orderform(cancer_orderform):

    # GIVEN an order form for a cancer order with 11 samples,
    # WHEN parsing the order form
    data = orderform.parse_orderform(cancer_orderform)

    # THEN it should detect the type of project
    assert data['project_type'] == 'cancer'

    # ... and it should find and group all samples in case
    assert len(data['items']) == 1

    # ... and collect relevant data about the case
    # ... and collect relevant info about the samples

    case = data['items'][0]
    sample = case['samples'][0]
    assert len(case['samples']) == 1

    # This information is required

    assert sample['name'] == 's1'
    assert sample['container'] == '96 well plate'
    assert sample['data_analysis'] == 'Balsamic '
    assert sample['application'] == 'WGSPCFC015'
    assert sample['sex'] == 'male'
    assert case['name'] == 'c1'
    assert data['customer'] == 'cust000'
    assert case['require_qcok'] is True
    assert sample['source'] == 'blood'
    assert case['priority'] == 'standard'

    # Required if Plate

    assert sample['container_name'] == 'p1'
    assert sample['well_position'] == 'A:1'

    # This information is required for Balsamic analysis (cancer)
    assert sample['tumour'] is True
    assert sample['capture_kit'] == 'Twist exome v1.3'
    assert sample['tumour_purity'] == '1.0'

    assert sample['formalin_fixation_time'] == '3.0'
    assert sample['post_formalin_fixation_time'] == '3.0'

    # This information is optional
    assert sample['quantity'] == '1'
    assert sample['comment'] == 'comment'
