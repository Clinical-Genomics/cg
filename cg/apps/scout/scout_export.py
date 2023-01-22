"""Schemas for scout serialisation"""

from datetime import datetime
from typing import List, Optional, Dict

from pydantic import BaseModel, Field, validator
from typing_extensions import Literal

from cg.constants.gene_panel import GENOME_BUILD_37
from cg.constants.subject import (
    PlinkGender,
    Gender,
    PlinkPhenotypeStatus,
    RelationshipStatus,
)
from cg.constants.pedigree import Pedigree


class Individual(BaseModel):
    bam_file: Optional[str] = None
    individual_id: str
    sex: Literal[PlinkGender.UNKNOWN, PlinkGender.MALE, PlinkGender.FEMALE, Gender.OTHER]
    father: Optional[str]
    mother: Optional[str]
    phenotype: PlinkPhenotypeStatus
    analysis_type: str = "wgs"

    @validator(Pedigree.FATHER, Pedigree.MOTHER)
    def convert_to_zero(cls, value):
        if value is None:
            return RelationshipStatus.HAS_NO_PARENT
        return value

    @validator(Pedigree.SEX)
    def convert_sex_to_zero(cls, value):
        if value == Gender.OTHER:
            return PlinkGender.UNKNOWN
        return value


class Panel(BaseModel):
    panel_name: str


class Phenotype(BaseModel):
    phenotype_id: str
    feature: str


class Gene(BaseModel):
    hgnc_id: int
    hgnc_symbol: Optional[str]
    region_annotation: Optional[str]
    functional_annotation: Optional[str]
    sift_prediction: Optional[str]
    polyphen_prediction: Optional[str]


class DiagnosisPhenotypes(BaseModel):
    disease_nr: int
    disease_id: str
    description: str
    individuals: Optional[List[Dict[str, str]]]


class ScoutExportCase(BaseModel):
    id: str = Field(str, alias="_id")
    analysis_date: datetime
    owner: str
    causatives: Optional[List[str]] = None
    collaborators: List[str] = []
    individuals: List[Individual]
    genome_build: Optional[str]
    panels: Optional[List[Panel]]
    rank_model_version: Optional[str]
    sv_rank_model_version: Optional[str]
    rank_score_threshold: int = 5
    phenotype_terms: Optional[List[Phenotype]]
    phenotype_groups: Optional[List[Phenotype]]
    diagnosis_phenotypes: Optional[List[DiagnosisPhenotypes]]
    diagnosis_genes: Optional[List[int]]

    @validator("genome_build")
    def convert_genome_build(cls, value):
        if value is None:
            return GENOME_BUILD_37
        return value


class Genotype(BaseModel):
    genotype_call: str
    allele_depths: List[int]
    read_depth: int
    genotype_quality: int
    sample_id: str


class Variant(BaseModel):
    document_id: str
    variant_id: str
    chromosome: str
    position: int
    dbsnp_id: Optional[str] = None
    reference: str
    alternative: str
    quality: Optional[float] = None
    filters: Optional[List[str]] = None
    end: int
    rank_score: int
    category: str
    sub_category: str
    genes: Optional[List[Gene]]
    samples: List[Genotype]
