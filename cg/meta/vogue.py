from cg.apps import gt, vogue


class VogueAPI(vogue.VogueAPI):

    def __init__(self, db: Store):
        self.db = db
 

    def load_genotype(self, sample_id):
        """Loading genotype data from the genotype database into the trending database"""
        
        genotype_doc = gt.get_trending(sample_id)
        self.load_genotype(genotype_doc)


    def load_application_tag(self):
        """Loading application tag data from statusDB into the trending database"""


