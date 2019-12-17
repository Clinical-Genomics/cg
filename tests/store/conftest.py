# -*- coding: utf-8 -*-
import datetime as dt

import pytest


@pytest.fixture
def microbial_submitted_order():
    """Build an example order as it looks after submission to ."""
    order = {'customer': 'cust000',
             'name': 'test order',
             'internal_id': 'lims_reference',
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
                      tumour=False, custom_index=None, elution_buffer='Nuclease-free water',
                      organism='C. Jejuni', reference_genome='NC_111',
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
                      tumour=False, custom_index=None, elution_buffer='Nuclease-free water',
                      organism='M.upium', reference_genome='NC_222',
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
                      tumour=False, custom_index=None, elution_buffer='Nuclease-free water',
                      organism='C. difficile', reference_genome='NC_333',
                      extraction_method='MagNaPure 96 (contact Clinical Genomics before '
                                        'submission)',
                      analysis='fastq', mother=None, father=None)], 'project_type': 'microbial'}
    return order


@pytest.yield_fixture(scope='function')
def microbial_store(base_store, microbial_submitted_order):
    """Setup a store instance for testing analysis API."""
    customer = base_store.customer(microbial_submitted_order['customer'])

    order = base_store.MicrobialOrder(internal_id=microbial_submitted_order['internal_id'],
                                      name=microbial_submitted_order['name'],
                                      ticket_number=microbial_submitted_order['ticket_number'],
                                      comment=microbial_submitted_order['comment'],
                                      created_at=dt.datetime(2012, 3, 3, 10, 10, 10),
                                      updated_at=dt.datetime(
                                          2012, 3, 3, 10, 10, 10),
                                      ordered_at=dt.datetime(2012, 3, 3, 10, 10, 10))

    order.customer = customer
    base_store.add(order)

    for sample_data in microbial_submitted_order['items']:
        application_version = base_store.application(sample_data['application']).versions[0]
        organism = base_store.Organism(internal_id=sample_data['organism'], name=sample_data[
            'organism'])
        base_store.add(organism)
        sample = base_store.add_microbial_sample(name=sample_data['name'], sex=sample_data['sex'],
                                                 internal_id=sample_data['internal_id'],
                                                 ticket=microbial_submitted_order['ticket_number'],
                                                 reads=sample_data['reads'],
                                                 comment=sample_data['comment'],
                                                 organism=organism,
                                                 priority=sample_data['priority'],
                                                 reference_genome=sample_data['reference_genome'],
                                                 application_version=application_version
                                                 )
        sample.microbial_order = order
        sample.application_version = application_version
        sample.customer = customer
        sample.organism = organism

        base_store.add(sample)

    base_store.commit()
    yield base_store


def _analysis_family():
    """Build an example family."""
    family = {
        'name': 'family',
        'internal_id': 'yellowhog',
        'panels': ['IEM', 'EP'],
        'samples': [{
            'name': 'son',
            'sex': 'male',
            'internal_id': 'ADM1',
            'father': 'ADM2',
            'mother': 'ADM3',
            'status': 'affected',
            'ticket_number': 123456,
            'reads': 5000000,
        }, {
            'name': 'father',
            'sex': 'male',
            'internal_id': 'ADM2',
            'status': 'unaffected',
            'ticket_number': 123456,
            'reads': 6000000,
        }, {
            'name': 'mother',
            'sex': 'female',
            'internal_id': 'ADM3',
            'status': 'unaffected',
            'ticket_number': 123456,
            'reads': 7000000,
        }]
    }
    return family


@pytest.yield_fixture(scope='function')
def analysis_store(base_store):
    """Setup a store instance for testing analysis API."""
    analysis_family = _analysis_family()
    customer = base_store.customer('cust000')
    family = base_store.Family(name=analysis_family['name'], panels=analysis_family[
        'panels'], internal_id=analysis_family['internal_id'], priority='standard')
    family.customer = customer
    base_store.add(family)
    application_version = base_store.application('WGTPCFC030').versions[0]
    for sample_data in analysis_family['samples']:
        sample = base_store.add_sample(name=sample_data['name'], sex=sample_data['sex'],
                                       internal_id=sample_data['internal_id'],
                                       ticket=sample_data['ticket_number'],
                                       reads=sample_data['reads'], )
        sample.family = family
        sample.application_version = application_version
        sample.customer = customer
        base_store.add(sample)
    base_store.commit()
    for sample_data in analysis_family['samples']:
        sample_obj = base_store.sample(sample_data['internal_id'])
        link = base_store.relate_sample(
            family=family,
            sample=sample_obj,
            status=sample_data['status'],
            father=base_store.sample(sample_data['father']) if sample_data.get('father') else None,
            mother=base_store.sample(sample_data['mother']) if sample_data.get('mother') else None,
        )
        base_store.add(link)

    _analysis = base_store.add_analysis(pipeline='pipeline', version='version')
    _analysis.family = family
    _analysis.config_path = 'dummy_path'

    base_store.commit()
    yield base_store
