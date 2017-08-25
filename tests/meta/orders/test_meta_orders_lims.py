from cg.meta.orders.lims import LimsHandler


def test_to_lims_scout(scout_order):
    # GIVEN a scout order for a trio
    # WHEN parsing the order to format for LIMS import
    data = LimsHandler.to_lims(scout_order)
    # THEN it should list all samples
    assert len(data['samples']) == 3
    # ... and determine the container, container name, and well position
    assert set(sample['container'] for sample in data['samples']) == set(['96 well plate', 'Tube'])
    container_names = set(sample['container_name'] for sample in data['samples'] if
                          sample['container_name'])
    assert container_names == set(['CMMS'])
    assert data['samples'][0]['well_position'] == 'A:1'
    # ... and pick out relevant UDFs
    first_sample = data['samples'][0]
    assert first_sample['udfs']['family_name'] == '17093'
    assert first_sample['udfs']['priority'] == 'standard'
    assert first_sample['udfs']['application'] == 'WGTPCFC030'
    assert first_sample['udfs']['source'] == 'blood'
    assert first_sample['udfs']['quantity'] == '2200'
    assert first_sample['udfs']['require_qcok'] is False
    assert first_sample['udfs']['customer'] == 'cust003'
    assert isinstance(data['samples'][1]['udfs']['comment'], str)


def test_to_lims_external(external_order):
    # GIVEN an external order for two samples
    # WHEN parsing the order to format for LIMS
    data = LimsHandler.to_lims(external_order)
    # THEN should "work"
    assert len(data['samples']) == 2
    # ... and make up a container for each sample
    assert data['samples'][0]['container'] == 'Tube'


def test_to_lims_fastq(fastq_order):
    # GIVEN a fastq order for two samples; normal vs. tumour
    # WHEN parsing the order to format for LIMS
    data = LimsHandler.to_lims(fastq_order)
    # THEN should "work"
    assert len(data['samples']) == 2
    # ... and pick out relevant UDF values
    assert data['samples'][0]['udfs']['tumour'] is False
    assert data['samples'][1]['udfs']['tumour'] is True


def test_to_lims_rml(rml_order):
    # GIVEN a rml order for three samples
    # WHEN parsing for LIMS
    data = LimsHandler.to_lims(rml_order)
    # THEN it should "work"
    assert len(data['samples']) == 3
    # ... and pick out relevant UDFs
    first_sample = data['samples'][0]
    assert first_sample['udfs']['pool'] == '1'
    assert first_sample['udfs']['volume'] == 35
    assert first_sample['udfs']['concentration'] == 5
    assert first_sample['udfs']['index'] == 'TruSeq DNA HT Dual-index (D7-D5)'
    assert first_sample['udfs']['index_number'] == 65
