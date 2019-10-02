""" Common MIP rare disease RNA related functionality """
import logging

from .base import MipAPI

class MipRDRNAAPI(MipAPI):
    """ Group MIP rare disease RNA specific functionality """

    def __init__(self, script, logger=logging.getLogger(__name__)):
        """Initialize MIP command line interface."""
        super().__init__(script, 'analyse rd_rna', logger)
