"""
    Module to upload cases to mutacc
"""

import os
import logging

from cg.apps import scoutapi, mutacc_auto

LOG = logging.getLogger(__name__)

class UploadToMutaccAPI():

    """API to upload finished cases to mutacc"""

    def __init__(self, scout_api: scoutapi.ScoutAPI, mutacc_auto_api: mutacc_auto.MutaccAutoAPI):

        self.scout = scout_api
        self.mutacc_auto = mutacc_auto_api

    def data(self, case) -> dict:
        """
            Find the necessary data for the case

            Args:
                case (dict): case dictionary from scout

            Returns:
                data (dict): dictionary with case data, and data on causative variants
        """

        if all([self.has_bam(case), self.has_causatives(case)]):
            causatives = self.scout.get_causative_variants(case_id=case['_id'])
            return {'case': case, 'causatives': causatives}

        return {}

    def extract_reads(self, data: dict):
        pass

    def import_cases(self):
        pass


    @staticmethod
    def has_bam(case: dict) -> bool:

        """
            Check that all samples in case has a given path to a bam file,
            and that the file exists

            Args:
                case (dict): case dictionary from scout

            Returns:
                (bool): True if all samples has valid paths to a bam-file

        """

        bam_exists = True
        for sample in case['individuals']:

            if sample.get('bam_file', None) is None:
                bam_exists = False
                LOG.warning("sample %s in case %s is missing bam fille",
                            sample['individual_id'], case['_id'])

            else:

                if not os.path.isfile(sample['bam_file']):
                    bam_exists = False
                    LOG.warning("sample %s in %s has non existing bam_file",
                                sample['individual_id'], case['_id'])

        return bam_exists


    @staticmethod
    def has_causatives(case: dict) -> bool:
        """
            Check that the case has marked causative variants in scout

            Args:
                case (dict): case dictionary from scout

            Returns:
                (bool): True if case has marked causative variants in scout
        """
        if case.get('causatives'):
            return True

        LOG.debug("case %s has no marked causatives in scout", case['_id'])
        return False
