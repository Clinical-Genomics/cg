# -*- coding: utf-8 -*-
import json
from cg.apps.gt import GenotypeAPI
from cg.apps.vogue import VogueAPI


class UploadVogueAPI():
    """API to run Vogue"""

    def __init__(self, genotype_api: GenotypeAPI, vogue_api: VogueAPI):
        self.genotype_api = genotype_api
        self.vogue_api = vogue_api

    def load_genotype(self, days):
        """Loading genotype data from the genotype database into the trending database"""
        samples = self.genotype_api.get_trending(days=days)
        samples = json.loads(samples)

        for sample_id in samples:
            self.vogue_api.load_genotype(samples[sample_id])