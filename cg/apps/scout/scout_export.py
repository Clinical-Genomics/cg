"""Schemas for scout serialisation"""

from typing import List, Optional
from typing_extensions import Literal
from pydantic import BaseModel, Field, validator
from datetime import datetime


class Individual(BaseModel):
    bam_file: Optional[str] = None
    individual_id: str
    sex: Literal["0", "1", "2", "other"]
    father: Optional[str]
    mother: Optional[str]
    phenotype: Literal[1, 2, 0]
    analysis_type: str = "wgs"

    @validator("father", "mother")
    def convert_to_zero(cls, v):
        if v is None:
            return "0"
        return v

    @validator("sex")
    def convert_sex_to_zero(cls, v):
        if v == "other":
            return "0"
        return v


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
    diagnosis_phenotypes: Optional[List[int]]
    diagnosis_genes: Optional[List[int]]

    @validator("genome_build")
    def convert_genome_build(cls, v):
        if v is None:
            return "37"
        return v


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
