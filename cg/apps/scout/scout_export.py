"""Schemas for scout serialisation"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field
from typing_extensions import Annotated, Literal

from cg.apps.scout.validators import set_gender_if_other, set_parent_if_missing
from cg.constants.gene_panel import GENOME_BUILD_37
from cg.constants.subject import Gender, PlinkGender, PlinkPhenotypeStatus


class Individual(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=True)
    bam_file: Optional[str] = None
    individual_id: str
    sex: Annotated[
        Literal[PlinkGender.UNKNOWN, PlinkGender.MALE, PlinkGender.FEMALE, Gender.OTHER],
        BeforeValidator(set_gender_if_other),
    ]
    father: Annotated[str, BeforeValidator(set_parent_if_missing)]
    mother: Annotated[str, BeforeValidator(set_parent_if_missing)]
    phenotype: PlinkPhenotypeStatus
    analysis_type: str = "wgs"


class Panel(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=True)
    panel_name: str


class Phenotype(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=True)
    phenotype_id: str
    feature: str


class Gene(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=True)
    hgnc_id: int
    hgnc_symbol: Optional[str] = None
    region_annotation: Optional[str] = None
    functional_annotation: Optional[str] = None
    sift_prediction: Optional[str] = None
    polyphen_prediction: Optional[str] = None


class DiagnosisPhenotypes(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=True)
    disease_nr: int
    disease_id: str
    description: str
    individuals: Optional[List[Dict[str, str]]] = None


class ScoutExportCase(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=True)
    id: str = Field(str, alias="_id")
    analysis_date: datetime
    owner: str
    causatives: Optional[List[str]] = None
    collaborators: List[str] = []
    individuals: List[Individual]
    genome_build: str = GENOME_BUILD_37
    panels: Optional[List[Panel]] = None
    rank_model_version: Optional[str] = None
    sv_rank_model_version: Optional[str] = None
    rank_score_threshold: int = 5
    phenotype_terms: Optional[List[Phenotype]] = None
    phenotype_groups: Optional[List[Phenotype]] = None
    diagnosis_phenotypes: Optional[List[DiagnosisPhenotypes]] = None
    diagnosis_genes: Optional[List[int]] = None


class Genotype(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=True)
    genotype_call: str
    allele_depths: List[int]
    read_depth: int
    genotype_quality: int
    sample_id: str


class Variant(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=True)
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
    genes: Optional[List[Gene]] = None
    samples: List[Genotype]
