"""API to run Vogue"""
# -*- coding: utf-8 -*-
import json

from cg.apps.gt import GenotypeAPI
from cg.apps.vogue import VogueAPI
from cg.store.api.findbasicdata import FindBasicDataHandler


class UploadVogueAPI:
    """API to load data into Vogue"""

    def __init__(
        self,
        genotype_api: GenotypeAPI,
        vogue_api: VogueAPI,
        find_basic: FindBasicDataHandler,
    ):
        self.genotype_api = genotype_api
        self.vogue_api = vogue_api
        self.find_basic = find_basic

    def load_genotype(self, days):
        """Loading genotype data from the genotype database into the trending database"""
        samples = self.genotype_api.export_sample(days=days)
        samples = json.loads(samples)
        for sample_id, sample_dict in samples.items():
            sample_dict["_id"] = sample_id
            self.vogue_api.load_genotype_data(sample_dict)

        samples_analysis = self.genotype_api.export_sample_analysis(days=days)
        samples_analysis = json.loads(samples_analysis)
        for sample_id, sample_dict in samples_analysis.items():
            sample_dict["_id"] = sample_id
            self.vogue_api.load_genotype_data(sample_dict)

    def load_apptags(self):
        """Loading application tags from statusdb into the trending database"""
        apptags = self.find_basic.applications()
        apptags_for_vogue = []
        for tag in apptags.all():
            apptags_for_vogue.append({"tag": tag.tag, "category": tag.category})

        self.vogue_api.load_apptags(apptags_for_vogue)
