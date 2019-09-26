""" Common microsalt related functionality """
import logging
import os
import re

from cg.store.models import Sample


class MicrosaltAPI():

    def __init__(self, logger=logging.getLogger(__name__)):
        self.LOG = logger

    def get_organism(self, sample_obj: Sample) -> str:
        organism = sample_obj.organism.internal_id.strip()
        reference = sample_obj.reference_genome

        # Predefined genus usage. All hail buggy excel files
        if 'gonorrhoeae' in organism:
            organism = "Neisseria spp."
        elif 'Cutibacterium acnes' in organism:
            organism = "Propionibacterium acnes"
        # Backwards compat, MUST hit first
        elif organism == 'VRE':
            if reference == 'NC_017960.1':
                organism = 'Enterococcus faecium'
            elif reference == 'NC_004668.1':
                organism = 'Enterococcus faecalis'
            elif 'Comment' in sample_obj.udf and not re.match('\w{4}\d{2,3}', sample_obj.udf['Comment']):
                organism = sample_obj.udf['Comment']
        elif (sample_obj.udf['Strain'] == 'Other' or sample_obj.udf['Strain'] == 'other') and 'Other species' in sample_obj.udf:
            # Other species predefined genus usage
            if 'gonorrhoeae' in sample_obj.udf['Other species']:
                organism = "Neisseria spp."
            elif 'Cutibacterium acnes' in sample_obj.udf['Other species']:
                organism = "Propionibacterium acnes"
            else:
                organism = sample_obj.udf['Other species']

        if 'Comment' in sample_obj.udf and not re.match('\w{4}\d{2,3}', sample_obj.udf['Comment']) and organism == "Unset":
            organism = sample_obj.udf['Comment'].strip()
        # Consistent safe-guard
        elif organism == "Unset":
            organism = "Other"
            self.logger.warn(f"Unable to resolve ambigious organism found in sample {sample_obj.internal_id}.")

    def get_organism_refname(self, sample_name):
        """Finds which reference contains the same words as the LIMS reference
           and returns it in a format for database calls."""
        self.load_lims_sample_info(sample_name)
        lims_organ = self.data['organism'].lower()
        orgs = os.listdir(self.config["folders"]["references"])
        organism = re.split('\W+', lims_organ)
        try:
            for target in orgs:
                hit = 0
                for piece in organism:
                    if len(piece) == 1:
                        if target.startswith(piece):
                            hit += 1
                    else:
                        if piece in target:
                            hit += 1
                        # For when people misspell the strain in the orderform
                        elif piece == "pneumonsiae" and "pneumoniae" in target:
                            hit += 1
                        else:
                            break
                if hit == len(organism):
                    return target
        except Exception as e:
            self.logger.warn("Unable to find existing reference for {}, strain {} has no reference match\nSource: {}"
                             .format(sample_name, lims_organ, e))
