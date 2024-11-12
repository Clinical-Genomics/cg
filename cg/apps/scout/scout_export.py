"""Schemas for scout serialisation"""

from datetime import datetime

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field
from typing_extensions import Annotated, Literal

from cg.apps.scout.validators import (
    convert_genome_build,
    set_parent_if_missing,
    set_sex_if_other,
)
from cg.constants.gene_panel import GENOME_BUILD_37
from cg.constants.scout import RANK_MODEL_THRESHOLD
from cg.constants.subject import PlinkPhenotypeStatus, PlinkSex, RelationshipStatus, Sex


class Individual(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=True)
    bam_file: str | None = None
    individual_id: str
    sex: Annotated[
        Literal[PlinkSex.UNKNOWN, PlinkSex.MALE, PlinkSex.FEMALE, Sex.OTHER],
        BeforeValidator(set_sex_if_other),
    ]
    father: Annotated[str, BeforeValidator(set_parent_if_missing)] = (
        RelationshipStatus.HAS_NO_PARENT
    )
    mother: Annotated[str, BeforeValidator(set_parent_if_missing)] = (
        RelationshipStatus.HAS_NO_PARENT
    )
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
    hgnc_symbol: str | None = None
    region_annotation: str | None = None
    functional_annotation: str | None = None
    sift_prediction: str | None = None
    polyphen_prediction: str | None = None


class DiagnosisPhenotypes(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=True)
    disease_nr: int
    disease_id: str
    description: str
    individuals: list[dict[str, str]] | None = None


class ScoutExportCase(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=True)
    id: str = Field(str, alias="_id")
    analysis_date: datetime
    owner: str
    causatives: list[str] | None = None
    collaborators: list[str] = []
    individuals: list[Individual]
    genome_build: Annotated[str, BeforeValidator(convert_genome_build)] = GENOME_BUILD_37
    panels: list[Panel] | None = None
    rank_model_version: str | None = None
    sv_rank_model_version: str | None = None
    rank_score_threshold: int = RANK_MODEL_THRESHOLD
    phenotype_terms: list[Phenotype] | None = None
    phenotype_groups: list[Phenotype] | None = None
    diagnosis_phenotypes: list[DiagnosisPhenotypes] | None = None
    diagnosis_genes: list[int] | None = None


class Genotype(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=True)
    genotype_call: str
    allele_depths: list[int]
    read_depth: int
    genotype_quality: int
    sample_id: str


class Variant(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=True)
    document_id: str
    variant_id: str
    chromosome: str
    position: int
    dbsnp_id: str | None = None
    reference: str
    alternative: str
    quality: float | None = None
    filters: list[str] | None = None
    end: int
    rank_score: int
    category: str
    sub_category: str
    genes: list[Gene] | None = None
    samples: list[Genotype]
