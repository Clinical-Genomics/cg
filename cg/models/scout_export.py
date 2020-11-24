"""Schemas for scout serialisation"""

from typing import List, Optional
from typing_extensions import Literal
from pydantic import BaseModel, Field
from datetime import datetime


class Individual(BaseModel):
    bam_file: Optional[str] = None
    individual_id: str
    sex: Literal["0", "1", "2"]
    father: str
    mother: str
    phenotype: Literal[1, 2, 0]
    analysis_type: str


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


class Case(BaseModel):
    id: str = Field(str, alias="_id")
    analysis_date: datetime
    owner: str
    causatives: Optional[List[str]] = None
    collaborators: List[str]
    individuals: List[Individual]
    genome_build: str
    panels: Optional[List[Panel]]
    rank_model_version: Optional[str]
    sv_rank_model_version: Optional[str]
    rank_score_threshold: int
    phenotype_terms: Optional[List[Phenotype]]
    phenotype_groups: Optional[List[Phenotype]]
    diagnosis_phenotypes: Optional[List[Phenotype]]
    diagnosis_genes: Optional[List[Gene]]


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
    genes: List[Gene]
    samples: List[Genotype]
