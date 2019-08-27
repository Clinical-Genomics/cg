from cg.apps.gt import GenotypeAPI
from cg.apps.vogue import VogueAPI


class UploaVogueAPI():

    def __init__(self, genotype_api: GenotypeAPI, vogue_api: VogueAPI):
        self.genotype_api = genotype_api
        self.vogue_api = vogue_api
 

    def load_genotype(self, days):
        """Loading genotype data from the genotype database into the trending database"""
        
        trending_obj = self.genotype_api.get_trending(days = 30)
        for sample_doc in trending_obj:
            self.vogue_api.load_genotype(sample_doc)
            