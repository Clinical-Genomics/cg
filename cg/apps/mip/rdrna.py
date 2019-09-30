""" Common microsalt related functionality """
import logging


class MipRDRNAAPI():
    """ Group MIP rare disease RNA specific functionality """

    def __init__(self, logger=logging.getLogger(__name__)):
        self.log = logger
