"""API to run Vogue"""
# -*- coding: utf-8 -*-
import json

from cg.apps.gt import GenotypeAPI
from cg.apps.vogue import VogueAPI


class UploadVogueAPI():
    """API to load data into Vogue"""

    def __init__(self, genotype_api: GenotypeAPI, vogue_api: VogueAPI):
        self.genotype_api = genotype_api
        self.vogue_api = vogue_api

    def load_genotype(self, days):
        """Loading genotype data from the genotype database into the trending database"""
        samples = self.genotype_api.prepare_sample(days=days)
        samples = json.loads(samples)
        for sample_id in samples:
            self.vogue_api.load_genotype(samples[sample_id])
        
        samples_analysis = self.genotype_api.prepare_analysis(days=days)
        samples_analysis = json.loads(samples_analysis)
        for sample_id in samples_analysis:
            self.vogue_api.load_genotype(samples_analysis[sample_id])
