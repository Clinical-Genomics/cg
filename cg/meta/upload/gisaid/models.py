from pathlib import Path
from typing import Optional, Any
from typing_extensions import Annotated
from pydantic import (
    BaseModel,
    BeforeValidator,
    FieldValidationInfo,
    field_validator,
    model_validator,
)
from datetime import datetime

from cg.meta.upload.gisaid.constants import AUTHORS


class FastaFile(BaseModel):
    header: str
    sequence: str


class GisaidAccession(BaseModel):
    log_message: str
    accession_nr: Optional[str] = None
    sample_id: Optional[str] = None

    @field_validator("accession_nr")
    @classmethod
    def parse_accession(cls, _, info: FieldValidationInfo):
        return info.data.get("log_message").split(";")[-1]

    @field_validator("sample_id")
    @classmethod
    def parse_sample_id(cls, _, info: FieldValidationInfo):
        return info.data.get("log_message").split("/")[2].split("_")[2]


class UploadFiles(BaseModel):
    csv_file: Path
    fasta_file: Path
    log_file: Path


class GisaidSample(BaseModel):
    case_id: str
    cg_lims_id: str
    submitter: str
    region: str
    region_code: str
    fn: str
    covv_collection_date: str
    covv_subm_sample_id: str
    covv_virus_name: Optional[str] = None
    covv_orig_lab: Optional[str] = None
    covv_type: Optional[str] = "betacoronavirus"
    covv_passage: Optional[str] = "Original"
    covv_location: Optional[str] = None
    covv_host: Optional[str] = "Human"
    covv_gender: Optional[str] = "unknown"
    covv_patient_age: Annotated[Optional[str], BeforeValidator(lambda v: str(v))] = "unknown"
    covv_patient_status: Optional[str] = "unknown"
    covv_seq_technology: Optional[str] = "Illumina NovaSeq"
    covv_orig_lab_addr: Optional[str] = None
    covv_subm_lab: Optional[str] = "Karolinska University Hospital"
    covv_subm_lab_addr: Optional[str] = "171 76 Stockholm, Sweden"
    covv_authors: Optional[str] = " ,".join(AUTHORS)

    @model_validator(mode="before")
    @classmethod
    def set_generated_fields(cls, data: Any):
        if isinstance(data, dict):
            data.setdefault("covv_location", _generate_covv_location(data.get("region")))
            data["covv_subm_sample_id"] = _generate_covv_subm_sample_id(
                subm_sample_id=data.get(
                    "covv_subm_sample_id",
                ),
                region_code=data.get("region_code"),
            )
            data.setdefault(
                "covv_virus_name",
                _generate_covv_virus_name(
                    covv_subm_sample_id=data.get("covv_subm_sample_id"),
                    covv_collection_date=data.get("covv_collection_date"),
                ),
            )
        return data


def _generate_covv_location(region):
    return f"Europe/Sweden/{region}"


def _generate_covv_subm_sample_id(subm_sample_id, region_code):
    return f"{region_code}_SE100_{subm_sample_id}"


def _generate_covv_virus_name(covv_subm_sample_id, covv_collection_date):
    datetime_date = datetime.strptime(covv_collection_date, "%Y-%m-%d")
    return f"hCoV-19/Sweden/{covv_subm_sample_id}/{datetime_date.year}"
