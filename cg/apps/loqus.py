# -*- coding: utf-8 -*-
from loqusdb.plugins import MongoAdapter
from loqusdb.utils import load_database
from loqusdb.vcf_tools.vcf import get_file_handle, check_vcf


class LoqusdbAPI(MongoAdapter):

    def __init__(self, config: dict):
        super(LoqusdbAPI, self).__init__()
        self.connect(uri=config['loqusdb']['database'])

    def load(self, family_id: str, ped_path: str, vcf_path: str) -> dict:
        """Add observations from a VCF."""
        variant_handle = get_file_handle(vcf_path)
        nr_variants = check_vcf(variant_handle)
        nr_inserted = load_database(
            adapter=self,
            variant_file=vcf_path,
            family_file=ped_path,
            family_type='ped',
            gq_treshold=20,
            nr_variants=nr_variants,
            case_id=family_id,
        )
        return dict(variants=nr_variants, inserted=nr_inserted)
