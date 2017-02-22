# -*- coding: utf-8 -*-


def parse_caseid(raw_caseid):
    """Parse out parts of the case id."""
    customer_id, raw_familyid = raw_caseid.split('-', 1)
    case_id = raw_caseid.split('--')[0]
    family_parts = raw_familyid.split('--')
    family_id = family_parts[0]
    extra = family_parts[1] if len(family_parts) > 1 else None
    return {
        'customer_id': customer_id,
        'family_id': family_id,
        'case_id': case_id,
        'extra': extra,
    }
