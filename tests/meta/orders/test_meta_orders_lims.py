from cg.meta.orders.lims import LimsHandler


def test_to_lims_scout(scout_order_to_submit):
    # GIVEN a scout order for a trio
    # WHEN parsing the order to format for LIMS import
    samples = LimsHandler.to_lims(customer='cust003', samples=scout_order_to_submit['samples'])
    # THEN it should list all samples
    assert len(samples) == 3
    # ... and determine the container, container name, and well position
    assert set(sample['container'] for sample in samples) == set(['96 well plate', 'Tube'])
    container_names = set(sample['container_name'] for sample in samples if
                          sample['container_name'])
    assert container_names == set(['CMMS'])
    assert samples[0]['well_position'] == 'A:1'
    # ... and pick out relevant UDFs
    first_sample = samples[0]
    assert first_sample['udfs']['family_name'] == '17093'
    assert first_sample['udfs']['priority'] == 'standard'
    assert first_sample['udfs']['application'] == 'WGTPCFC030'
    assert first_sample['udfs']['source'] == 'blood'
    assert first_sample['udfs']['quantity'] == '2200'
    assert first_sample['udfs']['require_qcok'] is False
    assert first_sample['udfs']['customer'] == 'cust003'
    assert isinstance(samples[1]['udfs']['comment'], str)


def test_to_lims_external(external_order_to_submit):
    # GIVEN an external order for two samples
    # WHEN parsing the order to format for LIMS
    samples = LimsHandler.to_lims(customer='dummyCust', samples=external_order_to_submit['samples'])
    # THEN should "work"
    assert len(samples) == 2
    # ... and make up a container for each sample
    assert samples[0]['container'] == 'Tube'


def test_to_lims_fastq(fastq_order_to_submit):
    # GIVEN a fastq order for two samples; normal vs. tumour
    # WHEN parsing the order to format for LIMS
    samples = LimsHandler.to_lims(customer='dummyCust', samples=fastq_order_to_submit['samples'])
    # THEN should "work"
    assert len(samples) == 2
    # ... and pick out relevant UDF values
    assert samples[0]['udfs']['tumour'] is False
    assert samples[1]['udfs']['tumour'] is True


def test_to_lims_rml(rml_order_to_submit):
    # GIVEN a rml order for three samples
    # WHEN parsing for LIMS
    samples = LimsHandler.to_lims(customer='dummyCust', samples=rml_order_to_submit['samples'])
    # THEN it should "work"
    assert len(samples) == 3
    # ... and pick out relevant UDFs
    first_sample = samples[0]
    assert first_sample['udfs']['pool'] == '1'
    assert first_sample['udfs']['volume'] == '35'
    assert first_sample['udfs']['concentration'] == '5'
    assert first_sample['udfs']['index'] == 'TruSeq DNA HT Dual-index (D7-D5)'
    assert first_sample['udfs']['index_number'] == '65'


def test_to_lims_microbial(microbial_order_to_submit):
    # GIVEN a microbial order for three samples
    # WHEN parsing for LIMS
    samples = LimsHandler.to_lims(customer='cust000', samples=microbial_order_to_submit['samples'])
    # THEN it should "work"
    assert len(samples) == 5
    # ... and pick out relevant UDFs
    first_sample = samples[0]
    assert first_sample['udfs']['priority'] == 'research'
    assert first_sample['udfs']['organism'] == 'M.upium'
    assert first_sample['udfs']['reference_genome'] == 'NC_111'
    assert first_sample['udfs']['extraction_method'] == 'MagNaPure 96 (contact Clinical Genomics ' \
                                                        'before submission)'
