# -*- coding: utf-8 -*-
from loqusdb.plugins import MongoAdapter
from loqusdb.utils import load_database
from loqusdb.vcf_tools.vcf import (get_file_handle, check_vcf)


def connect(config):
    """Connect to LoqusDB mongo database."""
    adapter = MongoAdapter()
    adapter.connect(uri=config['loqusdb']['uri'])
    return adapter


def add(adapter, ped_path, vcf_path, case_id):
    """Add observations from a VCF."""
    variant_handle = get_file_handle(vcf_path)
    nr_variants = check_vcf(variant_handle)
    nr_inserted = load_database(
        adapter=adapter,
        variant_file=vcf_path,
        family_file=ped_path,
        family_type='ped',
        gq_treshold=20,
        nr_variants=nr_variants,
        case_id=case_id,
    )

    return dict(variants=nr_variants, inserted=nr_inserted)
