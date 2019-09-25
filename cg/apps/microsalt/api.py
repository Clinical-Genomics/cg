import logging
import os
import re

from cg.apps.lims import Sample as LimsSample


class MicrosaltAPI():

    def __init__(self, logger=logging.getLogger(__name__)):
        self.LOG = logger

    def get_organism(self, lims_sample: LimsSample) -> str:
        organism = "Unset"
        reference = "None"
        if 'Reference Genome Microbial' in lims_sample.udf:
            reference = lims_sample.udf['Reference Genome Microbial'].strip()

        if 'Strain' in lims_sample.udf and organism == "Unset":
            # Predefined genus usage. All hail buggy excel files
            if 'gonorrhoeae' in lims_sample.udf['Strain']:
                organism = "Neisseria spp."
            elif 'Cutibacterium acnes' in lims_sample.udf['Strain']:
                organism = "Propionibacterium acnes"
            # Backwards compat, MUST hit first
            elif lims_sample.udf['Strain'] == 'VRE':
                if reference == 'NC_017960.1':
                    organism = 'Enterococcus faecium'
                elif reference == 'NC_004668.1':
                    organism = 'Enterococcus faecalis'
                elif 'Comment' in lims_sample.udf and not re.match('\w{4}\d{2,3}', lims_sample.udf['Comment']):
                    organism = lims_sample.udf['Comment']
            elif lims_sample.udf['Strain'] != 'Other' and lims_sample.udf['Strain'] != 'other':
                organism = lims_sample.udf['Strain']
            elif (lims_sample.udf['Strain'] == 'Other' or lims_sample.udf['Strain'] == 'other') and 'Other species' in lims_sample.udf:
                # Other species predefined genus usage
                if 'gonorrhoeae' in lims_sample.udf['Other species']:
                    organism = "Neisseria spp."
                elif 'Cutibacterium acnes' in lims_sample.udf['Other species']:
                    organism = "Propionibacterium acnes"
                else:
                    organism = lims_sample.udf['Other species']
        if reference != 'None' and organism == "Unset":
            if reference == 'NC_002163':
                organism = "Campylobacter jejuni"
            elif reference == 'NZ_CP007557.1':
                organism = 'Klebsiella oxytoca'
            elif reference == 'NC_000913.3':
                organism = 'Citrobacter freundii'
            elif reference == 'NC_002516.2':
                organism = 'Pseudomonas aeruginosa'
        elif 'Comment' in lims_sample.udf and not re.match('\w{4}\d{2,3}', lims_sample.udf['Comment']) and organism == "Unset":
            organism = lims_sample.udf['Comment'].strip()
        # Consistent safe-guard
        elif organism == "Unset":
            organism = "Other"
            self.logger.warn(f"Unable to resolve ambigious organism found in sample {lims_sample.internal_id}.")

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
