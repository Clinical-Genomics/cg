"""API to run Vogue"""
# -*- coding: utf-8 -*-
import json
from cg.apps.gt import GenotypeAPI
from cg.apps.vogue import VogueAPI
from cg.store.api.findbasicdata import FindBasicDataHandler


class UploadVogueAPI():
    """API to load data into Vogue"""

    def __init__(self, genotype_api: GenotypeAPI, vogue_api: VogueAPI,
                 find_basic: FindBasicDataHandler):
        self.genotype_api = genotype_api
        self.vogue_api = vogue_api
        self.find_basic = find_basic

    def load_genotype(self, days):
        """Loading genotype data from the genotype database into the trending database"""
        samples = self.genotype_api.get_trending(days=days)
        samples = json.loads(samples)

        for sample_id in samples:
            self.vogue_api.load_genotype(samples[sample_id])

    def load_apptags(self):
        """Loading application tags from statusdb into the trending database"""
        apptags = self.find_basic.applications()
        apptags_for_vogue = []
        for tag in apptags.all():
            apptags_for_vogue.append({"tag": tag.tag, "category": tag.category})

        self.vogue_api.load_apptags(apptags_for_vogue)
