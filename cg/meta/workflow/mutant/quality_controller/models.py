from typing import Annotated, Any
from pydantic import BaseModel, BeforeValidator, Field, ValidationError, ConfigDict
from cg.store.models import Sample


# Validator
def str_to_bool(value: str) -> bool:
    if value == "TRUE":
        return True
    elif value == "FALSE":
        return False
    raise ValidationError(f"String {value} cannot be turned to bool.")


# Models
class ParsedSampleResults(BaseModel):
    sample_name: str = Field(alias="Sample")
    selection: str = Field(alias="Selection")
    region_code: str = Field(alias="Region Code")
    ticket: int = Field(alias="Ticket")
    pct_n_bases: float = Field(alias="%N_bases")
    pct_10x_coverage: float = Field(alias="%10X_coverage")
    passes_qc: Annotated[bool, BeforeValidator(str_to_bool)] = Field(alias="QC_pass")
    lineage: str = Field(alias="Lineage")
    pangolin_data_version: str = Field(alias="Pangolin_data_version")
    voc: str = Field(alias="VOC")
    mutations: str = Field(alias="Mutations")


class MutantPoolSamples(BaseModel):
    samples: list[Sample]
    external_negative_control: Sample
    internal_negative_control: Sample

    model_config = ConfigDict(arbitrary_types_allowed=True)


class SamplePoolAndResults(BaseModel):
    pool: MutantPoolSamples
    results: dict[str, ParsedSampleResults]


class SampleQualityResults(BaseModel):
    sample_id: str
    passes_qc: bool
    passes_reads_threshold: bool
    passes_mutant_qc: bool | None = None


class SamplesQualityResults(BaseModel):
    internal_negative_control: SampleQualityResults
    external_negative_control: SampleQualityResults
    samples: list[SampleQualityResults]

    @property
    def total_samples_count(self) -> int:
        return len(self.samples)

    @property
    def passed_samples_count(self) -> int:
        samples_pass_qc: list[bool] = [sample_result.passes_qc for sample_result in self.samples]
        return sum(samples_pass_qc)

    @property
    def failed_samples_count(self) -> int:
        return self.total_samples_count - self.passed_samples_count


class CaseQualityResult(BaseModel):
    passes_qc: bool
    internal_negative_control_passes_qc: bool
    external_negative_control_passes_qc: bool
    fraction_samples_passes_qc: bool


class MutantQualityResult(BaseModel):
    case_quality_result: CaseQualityResult
    samples_quality_results: SamplesQualityResults
    summary: str

    @property
    def passes_qc(self) -> bool:
        return self.case_quality_result.passes_qc


class MutantReport(BaseModel):
    summary: str
    case: dict[str, Any]
    samples: dict[str, Any]
