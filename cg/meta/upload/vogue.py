"""API to run Vogue"""

import json

from cg.apps.gt import GenotypeAPI
from cg.apps.vogue import VogueAPI
from cg.store import Store


class UploadVogueAPI:
    """API to load data into Vogue"""

    def __init__(self, genotype_api: GenotypeAPI, vogue_api: VogueAPI, store: Store):
        self.genotype_api = genotype_api
        self.vogue_api = vogue_api
        self.store = store

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
        apptags = self.store.applications()
        apptags_for_vogue = []
        for tag in apptags.all():
            apptags_for_vogue.append({"tag": tag.tag, "prep_category": tag.prep_category})

        self.vogue_api.load_apptags(apptags_for_vogue)

    def load_samples(self, days):
        """Loading samples from lims into the trending database"""

        self.vogue_api.load_samples(days=days)

    def load_flowcells(self, days):
        """Loading flowcells from lims into the trending database"""

        self.vogue_api.load_flowcells(days=days)

    def load_bioinfo_raw(self, load_bioinfo_raw_inputs):
        """Running vogue load bioinfo raw."""

        self.vogue_api.load_bioinfo_raw(load_bioinfo_raw_inputs)
