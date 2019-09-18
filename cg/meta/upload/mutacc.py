"""
    Module to upload cases to mutacc
"""

import os
import logging
from collections import namedtuple

from cg.apps import scoutapi, mutacc_auto

LOG = logging.getLogger(__name__)


class UploadToMutaccAPI():

    """API to upload finished cases to mutacc"""

    def __init__(self, scout_api: scoutapi.ScoutAPI, mutacc_auto_api: mutacc_auto.MutaccAutoAPI):

        self.scout = scout_api
        self.mutacc_auto = mutacc_auto_api

    def _data(self, case) -> dict:
        """
            Find the necessary data for the case

            Args:
                case (dict): case dictionary from scout

            Returns:
                data (dict): dictionary with case data, and data on causative variants
        """

        if all([self._has_bam(case), self._has_causatives(case)]):
            causatives = self.scout.get_causative_variants(case_id=case['_id'])
            mutacc_case = remap(case, SCOUT_TO_MUTACC_CASE)
            mutacc_variants = [remap(variant, SCOUT_TO_MUTACC_VARIANTS) for variant in causatives]
            return {'case': mutacc_case, 'causatives': mutacc_variants}
        return {}

    def extract_reads(self, case: dict):
        """Use mutacc API to extract reads from case"""
        data = self._data(case)
        if data:
            LOG.info("Extracting reads from case %s", case['_id'])
            self.mutacc_auto.extract_reads(case=data['case'], variants=data['causatives'])

    def import_cases(self):
        """Use mutacc API to import cases to database"""
        LOG.info('importing cases into mutacc database')
        self.mutacc_auto.import_reads()

    @staticmethod
    def _has_bam(case: dict) -> bool:

        """
            Check that all samples in case has a given path to a bam file,
            and that the file exists

            Args:
                case (dict): case dictionary from scout

            Returns:
                (bool): True if all samples has valid paths to a bam-file

        """


        for sample in case['individuals']:

            if sample.get('bam_file', None) is None:
                LOG.warning("sample %s in case %s is missing bam fille",
                            sample['individual_id'], case['_id'])
                return False

            elif not os.path.isfile(sample['bam_file']):
                LOG.warning("sample %s in %s has non existing bam_file",
                            sample['individual_id'], case['_id'])
                return False

        return True

    @staticmethod
    def _has_causatives(case: dict) -> bool:
        """
            Check that the case has marked causative variants in scout

            Args:
                case (dict): case dictionary from scout

            Returns:
                (bool): True if case has marked causative variants in scout
        """
        if case.get('causatives'):
            return True

        LOG.warning("case %s has no marked causatives in scout", case['_id'])
        return False


# Reformat scout noutput to mutacc input

MAPPER = namedtuple('mapper', ['field_name_1', 'field_name_2', 'conv'])

def remap(input_dict: dict, mapper_list: list) -> dict:
    """
        Reformat dict from one application to be used by another

        Args:
            input_dict (dict): dictionary to be converted
            mapper_list (list(MAPPER)): list of mapper objects

        Returns:
            output_dict (dict): conveted dictionary

    """
    output_dict = {}
    for field in mapper_list:
        if input_dict.get(field.field_name_1, None) is not None:
            output_dict[field.field_name_2] = field.conv(input_dict[field.field_name_1])
    return output_dict


SCOUT_TO_MUTACC_SAMPLE = (
    MAPPER('individual_id', 'sample_id', str),
    MAPPER('sex', 'sex',
           lambda sex: 'male' if sex == '1' else 'female' if sex == '2' else 'unknown'),
    MAPPER('phenotype', 'phenotype', str),
    MAPPER('father', 'father', lambda father: father if father else '0'),
    MAPPER('mother', 'mother', lambda mother: mother if mother else '0'),
    MAPPER('analysis_type', 'analysis_type', str),
    MAPPER('bam_file', 'bam_file', str)
)

SCOUT_TO_MUTACC_CASE = (
    MAPPER('_id', 'case_id', str),
    MAPPER('genome_build', 'genome_build', str),
    MAPPER('dynamic_gene_list', 'dynamic_gene_list', list),
    MAPPER('panels', 'panels', lambda panels: [panel['panel_name'] for panel in panels]),
    MAPPER('rank_model_version', 'rank_model_version', str),
    MAPPER('rank_score_threshold', 'rank_score_threshold', int),
    MAPPER('phenotype_terms', 'phenotype_terms', list),
    MAPPER('phenotype_groups', 'phenotype_groups', list),
    MAPPER('diagnosis_phenotypes', 'diagnosis_phenotypes', list),
    MAPPER('diagnosis_genes', 'diagnosis_genes', list),
    MAPPER('individuals', 'samples',
           lambda samples: [remap(sample, SCOUT_TO_MUTACC_SAMPLE) for sample in samples])
)

def get_gene_string(genes):
    """
        Function to convert the 'genes' field in the scout variant document
        to a string format that can be read by mutacc
    """
    gene_fields = ('hgnc_symbol',
                   'region_annotation',
                   'functional_annotation',
                   'sift_prediction',
                   'polyphen_prediction')

    ann_info = []
    for gene in genes:
        gene_info = '|'.join([gene[ann_id] if gene.get(ann_id) else '' for ann_id in gene_fields])
        ann_info.append(gene_info)
    ann_info = ','.join(ann_info)

    return ann_info


SCOUT_TO_MUTACC_FORMAT = (
    MAPPER('genotype_call', 'GT', str),
    MAPPER('allele_depths', 'AD', lambda AD: ','.join([str(element) for element in AD])),
    MAPPER('read_depths', 'DP', lambda DP: ','.join([str(element) for element in DP])),
    MAPPER('genotype_quality', 'GQ', float)
)


SCOUT_TO_MUTACC_VARIANTS = (
    MAPPER('chromosome', 'CHROM', str),
    MAPPER('position', 'POS', int),
    MAPPER('dbsnp_id', 'ID', str),
    MAPPER('reference', 'REF', str),
    MAPPER('alternative', 'ALT', str),
    MAPPER('quality', 'QUAL', float),
    MAPPER('filters', 'FILTER', lambda filters: ','.join([str(filter) for filter in filters])),
    MAPPER('end', 'END', int),
    MAPPER('rank_score', 'RankScore', int),
    MAPPER('category', 'category', str),
    MAPPER('sub_category', 'sub_category', str),
    MAPPER('genes', 'ANN', get_gene_string),
    MAPPER('samples', 'FORMAT',
           lambda samples: {sample['sample_id']: remap(sample, SCOUT_TO_MUTACC_FORMAT)
                            for sample in samples})
)
