# -*- coding: utf-8 -*-

PRIORITY_MAP = {'research': 0, 'standard': 1, 'priority': 2, 'express': 3}
REV_PRIORITY_MAP = {value: key for key, value in PRIORITY_MAP.items()}
PRIORITY_OPTIONS = list(PRIORITY_MAP.keys())
FAMILY_ACTIONS = ('analyze', 'running', 'hold')
PREP_CATEGORIES = ('wgs', 'wes', 'tgs', 'wts', 'mic', 'rml')
SEX_OPTIONS = ('male', 'female', 'unknown')
STATUS_OPTIONS = ('affected', 'unaffected', 'unknown')
CAPTUREKIT_OPTIONS = ('Agilent Sureselect CRE',
                      'Agilent Sureselect V5',
                      'SureSelect Focused Exome',
                      'Twist_Target_hg19',
                      'other')
FLOWCELL_STATUS = ('ondisk', 'removed', 'requested', 'processing')
