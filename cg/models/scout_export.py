"""Schemas for scout serialisation"""

from typing import List, Optional
from typing_extensions import Literal
from pydantic import BaseModel
from datetime import datetime


class Individual(BaseModel):
    bam_file: Optional[str]
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
    region_annotation: Optional[str]
    functional_annotation: Optional[str]
    sift_prediction: Optional[str]
    polyphen_prediction: Optional[str]


class Case(BaseModel):
    _id: str
    analysis_date: datetime
    owner: str
    causatives: Optional[List[str]]
    collaborators: List[str]
    individuals: List[Individual]
    genoe_build: str
    panels: Optional[List[Panel]]
    rank_model_version: Optional[str]
    sv_rank_model_version: Optional[str]
    rank_score_treshold: int
    phenotype_terms: Optional[List[Phenotype]]
    phenotype_groups: Optional[List[Phenotype]]
    diagnosis_phenotypes: Optional[List[Phenotype]]
    diagnosis_genes: Optional[List[Gene]]
