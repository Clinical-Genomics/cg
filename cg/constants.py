# -*- coding: utf-8 -*-

PRIORITY_MAP = {'research': 0, 'standard': 1, 'priority': 2, 'express': 3, 'clinical trials': 4}
REV_PRIORITY_MAP = {value: key for key, value in PRIORITY_MAP.items()}
PRIORITY_OPTIONS = list(PRIORITY_MAP.keys())
FAMILY_ACTIONS = ('analyze', 'running', 'hold')
PREP_CATEGORIES = ('wgs', 'wes', 'tgs', 'wts', 'mic', 'rml')
SEX_OPTIONS = ('male', 'female', 'unknown')
STATUS_OPTIONS = ('affected', 'unaffected', 'unknown')
CONTAINER_OPTIONS = ('Tube', '96 well plate')
CAPTUREKIT_OPTIONS = ('Agilent Sureselect CRE',
                      'Agilent Sureselect V5',
                      'SureSelect Focused Exome',
                      'Twist_Target_hg19.bed',
                      'other')
CAPTUREKIT_CANCER_OPTIONS = (
    'GIcfDNA',
    'GMCKsolid',
    'GMSmyeloid',
    'LymphoMATIC',
    'other (specify in comment field)'
                             )
FLOWCELL_STATUS = ('ondisk', 'removed', 'requested', 'processing')
METAGENOME_SOURCES = (
    'blood',
    'skin',
    'respiratory',
    'urine',
    'CSF',
    'faeces',
    'environmental',
    'unknown',
    'other')
ANALYSIS_SOURCES = (
    'blood',
    'buccal swab',
    'cell-free DNA',
    'cell line',
    'cytology (FFPE)',
    'cytology (not fixed/fresh)',
    'muscle',
    'nail',
    'saliva',
    'skin',
    'tissue (FFPE)',
    'tissue (fresh frozen)',
    'bone marrow',
    'other')
