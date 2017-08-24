# -*- coding: utf-8 -*-
from typing import List

import xlrd

from cg.exc import OrderFormError

SEX_MAP = {'male': 'M', 'female': 'F', 'unknown': 'unknown', 'unknown': 'Unknown'}
REV_SEX_MAP = {value: key for key, value in SEX_MAP.items()}


def parse_orderform(excel_path: str) -> dict:
    """Parse out information from an order form."""
    workbook = xlrd.open_workbook(excel_path)

    sheet_name = None
    sheet_names = workbook.sheet_names()
    for name in ['orderform', 'order form']:
        if name in sheet_names:
            sheet_name = name
            break
    if sheet_name is None:
        raise OrderFormError("'orderform' sheet not found in Excel file")
    orderform_sheet = workbook.sheet_by_name(sheet_name)

    raw_samples = relevant_rows(orderform_sheet)
    parsed_samples = [parse_sample(raw_sample) for raw_sample in raw_samples]

    document_title = orderform_sheet.row(0)[1].value
    project_type = get_project_type(document_title, parsed_samples)

    if project_type in ('scout', 'external'):
        parsed_families = group_families(parsed_samples)
        items = []
        customer_ids = set()
        for family_id, parsed_family in parsed_families.items():
            customer_id, family_data = expand_family(family_id, parsed_family)
            customer_ids.add(customer_id)
            items.append(family_data)
    else:
        customer_ids = set(sample['customer'] for sample in parsed_samples)
        items = parsed_samples

    customer_options = len(customer_ids)
    if customer_options == 0:
        raise OrderFormError('customer information missing')
    elif customer_options != 1:
        raise OrderFormError(f"invalid customer information: {customer_ids}")

    data = {
        'customer': customer_ids.pop(),
        'items': items,
        'project_type': project_type,
    }
    return data


def get_project_type(document_title: str, parsed_samples: List) -> str:
    """Determine the project type."""
    if '1604' in document_title:
        return 'rml'
    elif '1541' in document_title:
        return 'external'

    analyses = set(sample['analysis'] for sample in parsed_samples)
    project_type = analyses.pop() if len(analyses) == 1 else 'scout'    
    return project_type


def expand_family(family_id, parsed_family):
    """Fill-in information about families."""
    new_family = {'name': family_id, 'samples': []}
    samples = parsed_family['samples']

    require_qcoks = set(raw_sample['require_qcok'] for raw_sample in samples)
    if True in require_qcoks:
        new_family['require_qcok'] = True

    priorities = set(raw_sample['priority'] for raw_sample in samples)
    if len(priorities) > 1 and 'priority' in priorities:
        new_family['priority'] = 'priority'
    else:
        new_family['priority'] = priorities.pop()

    customers = set(raw_sample['customer'] for raw_sample in samples)
    if len(customers) != 1:
        raise ValueError("invalid customer information: {}".format(customers))
    customer = customers.pop()

    gene_panels = set()
    for raw_sample in samples:
        if raw_sample['panels']:
            gene_panels.update(raw_sample['panels'])
        new_sample = {
            'name': raw_sample['name'],
            'container': raw_sample['container'],
            'container_name': raw_sample['container_name'],
            'sex': raw_sample['sex'],
            'application': raw_sample['application'],
            'source': raw_sample['source'],
        }
        for key in ('container', 'container_name', 'well_position', 'quantity', 'status',
                    'comment', 'capture_kit'):
            if raw_sample[key]:
                new_sample[key] = raw_sample[key]

        for parent_id in ('mother', 'father'):
            if raw_sample[parent_id]:
                new_sample[parent_id] = raw_sample[parent_id]
        new_family['samples'].append(new_sample)
    if len(gene_panels) > 0:
        new_family['panels'] = list(gene_panels)

    return customer, new_family


def group_families(parsed_samples):
    """Group samples on family."""
    raw_families = {}
    for sample in parsed_samples:
        family_id = sample['family']
        if family_id not in raw_families:
            raw_families[family_id] = {
                'samples': [],
            }
        raw_families[family_id]['samples'].append(sample)
    return raw_families


def parse_sample(raw_sample):
    """Parse a raw sample row from order form sheet."""
    if ':' in raw_sample.get('UDF/Gene List', ''):
        raw_sample['UDF/Gene List'] = raw_sample['UDF/Gene List'].replace(':', ';')

    if raw_sample['UDF/priority'].lower() == 'förtur':
        raw_sample['UDF/priority'] = 'priority'

    sample = {
        'name': raw_sample['Sample/Name'],
        'container': raw_sample.get('Container/Type'),
        'container_name': raw_sample.get('Container/Name', raw_sample.get('UDF/RML plate name')),
        'well_position': raw_sample.get('Sample/Well Location',
                                        raw_sample.get('UDF/RML well position')),
        'sex': REV_SEX_MAP.get(raw_sample['UDF/Gender'].strip()),
        'panels': (raw_sample['UDF/Gene List'].split(';') if
                   raw_sample.get('UDF/Gene List') else None),
        'require_qcok': True if raw_sample['UDF/Process only if QC OK'] else False,
        'application': raw_sample['UDF/Sequencing Analysis'],
        'source': raw_sample['UDF/Source'].lower(),
        'status': raw_sample['UDF/Status'].lower() if raw_sample.get('UDF/Status') else None,
        'customer': raw_sample['UDF/customer'],
        'family': raw_sample['UDF/familyID'],
        'priority': raw_sample['UDF/priority'].lower() if raw_sample.get('UDF/priority') else None,
        'capture_kit': (raw_sample['UDF/Capture Library version'] if
                        raw_sample['UDF/Capture Library version'] else None),
        'comment': raw_sample['UDF/Comment'] if raw_sample['UDF/Comment'] else None,
        'index': raw_sample['UDF/Index type'] if raw_sample.get('UDF/Index type') else None,
        'reagent_label': (raw_sample['Sample/Reagent Label'] if
                          raw_sample.get('Sample/Reagent Label') else None),
        'tumour': True if raw_sample.get('UDF/tumor') == 'yes' else False,
    }

    data_analysis = raw_sample.get('UDF/Data Analysis') or 'fastq'
    raw_analysis = 'scout' if 'scout' in data_analysis else data_analysis.split('+', 1)[0]
    sample['analysis'] = 'fastq' if raw_analysis == 'custom' else raw_analysis

    for key, field_key in [('pool', 'pool name'), ('index_number', 'Index number'),
                           ('volume', 'Volume (uL)'), ('concentration', 'Concentration (nM)'),
                           ('quantity', 'Quantity')]:
        excel_key = f"UDF/{field_key}"
        str_value = (raw_sample[excel_key] if raw_sample.get(excel_key, '').rstrip('.0').isdigit()
                     else None)
        sample[key] = int(float(str_value)) if str_value else None

    for parent in ['mother', 'father']:
        parent_key = f"UDF/{parent}ID"
        sample[parent] = (raw_sample[parent_key] if
                          raw_sample.get(parent_key) and (raw_sample[parent_key] != '0.0')
                          else None)

    return sample


def relevant_rows(orderform_sheet):
    """Get the relevant rows from an order form sheet."""
    raw_samples = []
    current_row = None
    for row in orderform_sheet.get_rows():
        if row[0].value == '</SAMPLE ENTRIES>':
            break

        if current_row == 'header':
            header_row = [cell.value for cell in row]
            current_row = None
        elif current_row == 'samples':
            values = [str(cell.value) for cell in row]
            if values[0]:
                # skip empty rows
                sample_dict = dict(zip(header_row, values))
                raw_samples.append(sample_dict)

        if row[0].value == '<TABLE HEADER>':
            current_row = 'header'
        elif row[0].value == '<SAMPLE ENTRIES>':
            current_row = 'samples'
    return raw_samples
