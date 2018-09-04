# -*- coding: utf-8 -*-
import datetime as dt

import pytest


@pytest.fixture
def microbial_order():
    """Build an example order."""
    order = {'customer': 'cust000',
             'name': 'test order',
             'internal_id': 'limsreference',
             'comment': 'test comment',
             'ticket_number': '123456',
             'items': [
                 dict(name='Jag', internal_id='ms1', reads='1000', container='96 well plate',
                      container_name='hej',
                      rml_plate_name=None,
                      well_position='D:5', well_position_rml=None, sex=None, panels=None,
                      require_qcok=True,
                      application='MWRNXTR003', source=None, status=None, customer='cust015',
                      family=None,
                      priority='standard', capture_kit=None, comment=None, index=None,
                      reagent_label=None,
                      tumour=False, custom_index=None, eluation_buffer='Nuclease-free water',
                      strain='C. Jejuni', strain_other='', reference_genome='NC_111',
                      extraction_method='MagNaPure 96 (contact Clinical Genomics before '
                                        'submission)',
                      analysis='fastq', concentration_weight='1', mother=None, father=None),
                 dict(name='testar', internal_id='ms2', reads='1000', container='96 well plate',
                      container_name='hej',
                      rml_plate_name=None,
                      well_position='H:5', well_position_rml=None, sex=None, panels=None,
                      require_qcok=True,
                      application='MWRNXTR003', source=None, status=None, customer='cust015',
                      family=None,
                      priority='standard', capture_kit=None, comment=None, index=None,
                      reagent_label=None,
                      tumour=False, custom_index=None, eluation_buffer='Nuclease-free water',
                      strain='Other',
                      strain_other='M.upium', reference_genome='NC_222',
                      extraction_method='MagNaPure 96 (contact Clinical Genomics before '
                                        'submission)',
                      analysis='fastq', quantity='2', mother=None, father=None),
                 dict(name='lite', internal_id='ms3', reads='1000', container='96 well plate',
                      container_name='hej',
                      rml_plate_name=None,
                      well_position='A:6', well_position_rml=None, sex=None, panels=None,
                      require_qcok=True,
                      application='MWRNXTR003', source=None, status=None, customer='cust015',
                      family=None,
                      priority='standard', capture_kit=None, comment='3', index=None,
                      reagent_label=None,
                      tumour=False, custom_index=None, eluation_buffer='Nuclease-free water',
                      strain='C. difficile', strain_other='', reference_genome='NC_333',
                      extraction_method='MagNaPure 96 (contact Clinical Genomics before '
                                        'submission)',
                      analysis='fastq', mother=None, father=None)], 'project_type': 'microbial'}
    return order


@pytest.yield_fixture(scope='function')
def microbial_store(base_store, microbial_order):
    """Setup a store instance for testing analysis API."""
    customer = base_store.customer(microbial_order['customer'])

    order = base_store.MicrobialOrder(internal_id=microbial_order['internal_id'],
                                      name=microbial_order['name'],
                                      ticket_number=microbial_order['ticket_number'],
                                      comment=microbial_order['comment'],
                                      created_at=dt.datetime(2012, 3, 3, 10, 10, 10),
                                      updated_at=dt.datetime(
                                          2012, 3, 3, 10, 10, 10),
                                      ordered_at=dt.datetime(2012, 3, 3, 10, 10, 10))

    order.customer = customer
    base_store.add(order)

    for sample_data in microbial_order['items']:
        application_version = base_store.application(sample_data['application']).versions[0]
        sample = base_store.add_microbial_sample(name=sample_data['name'], sex=sample_data['sex'],
                                                 internal_id=sample_data['internal_id'],
                                                 ticket=microbial_order['ticket_number'],
                                                 reads=sample_data['reads'],
                                                 comment=sample_data['comment'],
                                                 strain=sample_data['strain'],
                                                 strain_other=sample_data['strain_other'],
                                                 reference_genome=sample_data['reference_genome'],
                                                 application_version=application_version
                                                 )
        sample.microbial_order = order
        sample.application_version = application_version
        sample.customer = customer
        base_store.add(sample)

    base_store.commit()
    yield base_store
