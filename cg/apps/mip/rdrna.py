""" Common microsalt related functionality """
import logging

from .base import MipAPI, CLI_OPTIONS


class MipRDRNAAPI(MipAPI):
    """ Group MIP rare disease RNA specific functionality """

    def __init__(self, script, logger=logging.getLogger(__name__)):
        """Initialize MIP command line interface."""
        super().__init__(script, 'rd_rna', logger)
