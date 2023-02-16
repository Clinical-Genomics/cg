"""
    Module to upload cases to mutacc
"""

import logging
import os
from collections import namedtuple
from typing import Dict

from cg.apps.mutacc_auto import MutaccAutoAPI
from cg.apps.scout import scout_export
from cg.apps.scout.scoutapi import ScoutAPI

LOG = logging.getLogger(__name__)


class UploadToMutaccAPI:

    """API to upload finished cases to mutacc"""

    def __init__(self, scout_api: ScoutAPI, mutacc_auto_api: MutaccAutoAPI):
        self.scout = scout_api
        self.mutacc_auto = mutacc_auto_api

    def extract_reads(self, case: scout_export.ScoutExportCase):
        """Use mutacc API to extract reads from case"""
        data: dict = self.data(case)
        if data:
            LOG.info("Extracting reads from case %s", case.id)
            self.mutacc_auto.extract_reads(case=data["case"], variants=data["causatives"])

    def import_cases(self):
        """Use mutacc API to import cases to database"""
        LOG.info("importing cases into mutacc database")
        self.mutacc_auto.import_reads()

    def data(self, case: scout_export.ScoutExportCase) -> Dict[str, dict]:
        """
        Find the necessary data for the case

        Args:
            case (dict): case dictionary from scout

        Returns:
            data (dict): dictionary with case data, and data on causative variants
        """

        if all([self._has_bam(case), self._has_causatives(case)]):
            causatives = self.scout.get_causative_variants(case_id=case.id)
            mutacc_case = remap(case.dict(), SCOUT_TO_MUTACC_CASE)
            mutacc_variants = [
                remap(variant.dict(), SCOUT_TO_MUTACC_VARIANTS) for variant in causatives
            ]
            return {"case": mutacc_case, "causatives": mutacc_variants}
        return {}

    @staticmethod
    def _has_bam(case: scout_export.ScoutExportCase) -> bool:
        """
        Check that all samples in case has a given path to a bam file,
        and that the file exists

        Args:
            case (dict): case dictionary from scout

        Returns:
            (bool): True if all samples has valid paths to a bam-file

        """
        sample: scout_export.Individual
        for sample in case.individuals:
            if sample.bam_file is None:
                LOG.info(
                    "sample %s in case %s is missing bam file. skipping",
                    sample.individual_id,
                    case.id,
                )
                return False

            if not os.path.isfile(sample.bam_file):
                LOG.info(
                    "sample %s in %s has non existing bam file. skipping",
                    sample.individual_id,
                    case.id,
                )
                return False

        return True

    @staticmethod
    def _has_causatives(case: scout_export.ScoutExportCase) -> bool:
        """
        Check that the case has marked causative variants in scout

        Args:
            case (dict): case dictionary from scout

        Returns:
            (bool): True if case has marked causative variants in scout
        """
        if case.causatives:
            return True

        LOG.info("case %s has no marked causatives in scout", case.id)
        return False


# Reformat scout noutput to mutacc input

MAPPER = namedtuple("mapper", ["field_name_1", "field_name_2", "conv"])


def remap(input_dict: dict, mapper_list: tuple) -> dict:
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
        if input_dict.get(field.field_name_1) is not None:
            output_dict[field.field_name_2] = field.conv(input_dict[field.field_name_1])
    return output_dict


def resolve_sex(scout_sex: str) -> str:
    """Convert scout sex value to mutacc valid value"""
    if scout_sex == "1":
        mutacc_sex = "male"
    elif scout_sex == "2":
        mutacc_sex = "female"
    else:
        mutacc_sex = "unknown"
    return mutacc_sex


def resolve_parent(scout_parent: str) -> str:
    """Convert parent (father/mother) value to mutacc"""
    if scout_parent == "":
        mutacc_parent = "0"
    else:
        mutacc_parent = scout_parent
    return mutacc_parent


def resolve_phenotype(scout_phenotype: int) -> str:
    """Convert scout phenotype to mutacc phenotype"""
    mutacc_phenotype = "unknown"
    if scout_phenotype == 1:
        mutacc_phenotype = "unaffected"
    if scout_phenotype == 2:
        mutacc_phenotype = "affected"
    return mutacc_phenotype


def get_gene_string(genes):
    """
    Function to convert the 'genes' field in the scout variant document
    to a string format that can be read by mutacc
    """
    gene_fields = (
        "hgnc_symbol",
        "region_annotation",
        "functional_annotation",
        "sift_prediction",
        "polyphen_prediction",
    )

    gene_annotation_info = []
    for gene in genes:
        gene_info = "|".join([gene[ann_id] if gene.get(ann_id) else "" for ann_id in gene_fields])
        gene_annotation_info.append(gene_info)
    gene_annotation_info = ",".join(gene_annotation_info)

    return gene_annotation_info


SCOUT_TO_MUTACC_SAMPLE = (
    MAPPER("individual_id", "sample_id", str),
    MAPPER("sex", "sex", resolve_sex),
    MAPPER("phenotype", "phenotype", resolve_phenotype),
    MAPPER("father", "father", resolve_parent),
    MAPPER("mother", "mother", resolve_parent),
    MAPPER("analysis_type", "analysis_type", str),
    MAPPER("bam_file", "bam_file", str),
)

SCOUT_TO_MUTACC_CASE = (
    MAPPER("id", "case_id", str),
    MAPPER("genome_build", "genome_build", str),
    MAPPER("panels", "panels", lambda panels: [panel["panel_name"] for panel in panels]),
    MAPPER("rank_model_version", "rank_model_version", str),
    MAPPER("sv_rank_model_version", "sv_rank_model_version", str),
    MAPPER("rank_score_threshold", "rank_score_threshold", int),
    MAPPER("phenotype_terms", "phenotype_terms", list),
    MAPPER("phenotype_groups", "phenotype_groups", list),
    MAPPER("diagnosis_phenotypes", "diagnosis_phenotypes", list),
    MAPPER("diagnosis_genes", "diagnosis_genes", list),
    MAPPER(
        "individuals",
        "samples",
        lambda samples: [remap(sample, SCOUT_TO_MUTACC_SAMPLE) for sample in samples],
    ),
)

SCOUT_TO_MUTACC_FORMAT = (
    MAPPER("genotype_call", "GT", str),
    MAPPER("allele_depths", "AD", lambda AD: ",".join([str(element) for element in AD])),
    MAPPER("read_depth", "DP", int),
    MAPPER("genotype_quality", "GQ", int),
    MAPPER("sample_id", "sample_id", str),
)


SCOUT_TO_MUTACC_VARIANTS = (
    MAPPER("chromosome", "CHROM", str),
    MAPPER("position", "POS", int),
    MAPPER("dbsnp_id", "ID", str),
    MAPPER("reference", "REF", str),
    MAPPER("alternative", "ALT", str),
    MAPPER("quality", "QUAL", float),
    MAPPER("filters", "FILTER", lambda filters: ",".join([str(filter) for filter in filters])),
    MAPPER("end", "END", int),
    MAPPER("rank_score", "RankScore", int),
    MAPPER("category", "category", str),
    MAPPER("sub_category", "sub_category", str),
    MAPPER("genes", "ANN", get_gene_string),
    MAPPER(
        "samples",
        "FORMAT",
        lambda samples: [remap(sample, SCOUT_TO_MUTACC_FORMAT) for sample in samples],
    ),
)
