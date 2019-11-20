""" Common microsalt related functionality """
import logging
import re

from cg.store.models import Sample
from cg.apps.lims import LimsAPI

#    Organism - Fallback based on reference, ‘Other species’ and ‘Comment’. Default to “Unset”.
#    Priority = Default to empty string. Weird response. Typically “standard” or “research”.
#    Reference = Defaults to “None”
#    Method: Outputted as “1273:23”. Defaults to “Not in LIMS”
#    Date: Returns latest == most recent date. Outputted as DT object “YYYY MM DD”. Defaults to
#    datetime.min


class MicrosaltAPI():
    """ Group microSALT specific functionality """

    def __init__(self, lims: LimsAPI, logger=logging.getLogger(__name__)):
        self.log = logger
        self.lims = lims

    def get_organism(self, sample_obj: Sample) -> str:
        """Organism
           - Fallback based on reference, ‘Other species’ and ‘Comment’.
           Default to "Unset"."""

        organism = sample_obj.organism.internal_id.strip()
        lims_sample = self.lims.sample(sample_obj.internal_id)

        comment = re.match(r'\w{4}\d{2,3}', lims_sample.get('comment') or '')
        has_comment = True if comment else False

        if 'gonorrhoeae' in organism:
            organism = "Neisseria spp."
        elif 'Cutibacterium acnes' in organism:
            organism = "Propionibacterium acnes"

        if organism == 'VRE':
            reference = sample_obj.organism.reference_genome
            if reference == 'NC_017960.1':
                organism = 'Enterococcus faecium'
            elif reference == 'NC_004668.1':
                organism = 'Enterococcus faecalis'
            elif has_comment:
                organism = comment

        if has_comment and organism == "Unset":
            organism = comment
        # Consistent safe-guard
        elif organism == "Unset":
            self.log.warning("Unable to resolve ambigious organism found in sample %s",
                             sample_obj.internal_id)

        return organism
