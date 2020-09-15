""" Common microsalt related functionality """
from datetime import datetime
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


class LimsMicrosaltAPI:
    """ Group microSALT specific functionality """

    def __init__(self, lims: LimsAPI, logger=logging.getLogger(__name__)):
        self.log = logger
        self.lims = lims

    def get_lims_comment(self, sample_id: str) -> str:
        """ returns the comment associated with a sample stored in lims"""
        lims_sample = self.lims.sample(sample_id)
        comment = lims_sample.get("comment") or ""
        if re.match(r"\w{4}\d{2,3}", comment):
            return comment

        return ""

    def get_organism(self, sample_obj: Sample) -> str:
        """Organism
        - Fallback based on reference, ‘Other species’ and ‘Comment’.
        Default to "Unset"."""

        organism = sample_obj.organism.internal_id.strip()
        comment = self.get_lims_comment(sample_obj.internal_id)
        has_comment = bool(comment)

        if "gonorrhoeae" in organism:
            organism = "Neisseria spp."
        elif "Cutibacterium acnes" in organism:
            organism = "Propionibacterium acnes"

        if organism == "VRE":
            reference = sample_obj.organism.reference_genome
            if reference == "NC_017960.1":
                organism = "Enterococcus faecium"
            elif reference == "NC_004668.1":
                organism = "Enterococcus faecalis"
            elif has_comment:
                organism = comment

        return organism

    def get_parameters(self, sample_obj: Sample):
        """Fill a dict with case config information for one sample """
        method_library_prep = self.lims.get_prep_method(sample_obj.internal_id)
        if method_library_prep:
            method_library_prep, _ = method_library_prep.split(" ", 1)
        method_sequencing = self.lims.get_sequencing_method(sample_obj.internal_id)
        if method_sequencing:
            method_sequencing, _ = method_sequencing.split(" ", 1)
        organism = self.get_organism(sample_obj)
        priority = "research" if sample_obj.priority == 0 else "standard"

        parameter_dict = {
            "CG_ID_project": sample_obj.microbial_order.internal_id,
            "Customer_ID_project": sample_obj.microbial_order.ticket_number,
            "CG_ID_sample": sample_obj.internal_id,
            "Customer_ID_sample": sample_obj.name,
            "organism": organism,
            "priority": priority,
            "reference": sample_obj.organism.reference_genome,
            "Customer_ID": sample_obj.microbial_order.customer.internal_id,
            "application_tag": sample_obj.application_version.application.tag,
            "date_arrival": str(sample_obj.received_at or datetime.min),
            "date_sequencing": str(sample_obj.sequenced_at or datetime.min),
            "date_libprep": str(sample_obj.prepared_at or datetime.min),
            "method_libprep": method_library_prep or "Not in LIMS",
            "method_sequencing": method_sequencing or "Not in LIMS",
        }

        return parameter_dict
