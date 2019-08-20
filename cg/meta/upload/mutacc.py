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
            mutacc_case = assemble_mutacc_case(case)
            mutacc_variants = [assemble_mutacc_variant(variant) for variant in causatives]
            return {'case': mutacc_case, 'causatives': mutacc_variants}
        return {}

    def extract_reads(self, case: dict):
        """Use mutacc API to extract reads from case"""
        data = self.data(case)
        if data:
            LOG.info("Extracting reads from case %s", case['_id'])
            self.mutacc_auto.extract_reads(case=data['case'], variants=data['causatives'])

    def import_cases(self):
        """Use mutacc API to import cases to database"""
        LOG.info('importing cases into mutacc database')
        self.mutacc_auto.import_reads()

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


# Fields in a scout case document to be included as meta-data to mutacc-auto
SCOUT_CASE_FIELDS = (
    '_id',
    'genome_build',
    'genome_version',
    'dynamic_gene_list',
    'panels',
    'rank_model_version',
    'rank_score_threshold',
    'phenotype_terms',
    'phenotype_groups',
    'diagnosis_phenotypes',
    'diagnosis_genes'
)

SCOUT_SAMPLE_FIELDS = (
    'individual_id',
    'sex',
    'phenotype',
    'father',
    'mother',
    'analysis_type',
    'bam_file'
)

SCOUT_VARIANT_FIELDS = (
    'chromosome',
    'position',
    'dbsnp_id',
    'reference',
    'alternative',
    'quality',
    'filters',
    'samples',
    'genes'
)


def assemble_mutacc_case(case: dict):
    """ Find necessary data from scout case object """
    mutacc_case = {}
    for field in SCOUT_CASE_FIELDS:
        if case.get(field, None) is not None:
            mutacc_case[field] = case[field]
    mutacc_samples = [assemble_mutacc_sample(sample) for sample in case['individuals']]
    mutacc_case['samples'] = mutacc_samples

    return mutacc_case


def assemble_mutacc_sample(sample: dict):
    """ Find necessary data from scout sample object """
    mutacc_sample = {}
    for field in SCOUT_SAMPLE_FIELDS:
        if sample.get(field, None) is not None:
            mutacc_sample[field] = sample[field]
    return mutacc_sample


def assemble_mutacc_variant(variant: dict):
    """ Find necessary data from scout variant object """
    mutacc_variant = {}
    for field in SCOUT_VARIANT_FIELDS:
        if variant.get(field, None) is not None:
            mutacc_variant[field] = variant[field]
    return mutacc_variant
