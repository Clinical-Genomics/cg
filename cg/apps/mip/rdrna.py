""" Common MIP rare disease RNA related functionality """
import logging

from .base import MipAPI

CLI_OPTIONS = {
    'config': {'option': '--config_file'},
    'priority': {'option': '--slurm_quality_of_service'},
    'email': {'option': '--email'},
    'base': {'option': '--cluster_constant_path'},
    'dryrun': {'option': '--dry_run_all'},
    'gene_list': {'option': '--vcfparser_slt_fl'},
    'max_gaussian': {'option': '--gatk_varrecal_snv_max_gau'},
    'skip_evaluation': {'option': '--qccollect_skip_evaluation'},
    'start_with': {'option': '--start_with_recipe'},
}

class MipRDRNAAPI(MipAPI):
    """ Group MIP rare disease RNA specific functionality """

    def __init__(self, script, logger=logging.getLogger(__name__)):
        """Initialize MIP command line interface."""
        super().__init__(script, 'analyse rd_rna', logger)
