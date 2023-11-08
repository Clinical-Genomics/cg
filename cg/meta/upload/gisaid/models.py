from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, model_validator

from cg.meta.upload.gisaid.constants import AUTHORS


class FastaFile(BaseModel):
    header: str
    sequence: str


class GisaidAccession(BaseModel):
    log_message: str
    accession_nr: Optional[str] = None
    sample_id: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def set_generated_fields(cls, data: Any) -> Any:
        """Constructs the fields that are generated from other fields."""
        if isinstance(data, dict):
            data.setdefault("accession_nr", _parse_accession_nr(data["log_message"]))
            data.setdefault("sample_id", _parse_sample_id_from_log(data["log_message"]))
        return data


def _parse_accession_nr(log_message: str) -> str:
    return log_message.split(";")[-1]


def _parse_sample_id_from_log(log_message: str) -> str:
    return log_message.split("/")[2].split("_")[2]


class UploadFiles(BaseModel):
    csv_file: Path
    fasta_file: Path
    log_file: Path


class GisaidSample(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=True)
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
    covv_patient_age: Optional[str] = "unknown"
    covv_patient_status: Optional[str] = "unknown"
    covv_seq_technology: Optional[str] = "Illumina NovaSeq"
    covv_orig_lab_addr: Optional[str] = None
    covv_subm_lab: Optional[str] = "Karolinska University Hospital"
    covv_subm_lab_addr: Optional[str] = "171 76 Stockholm, Sweden"
    covv_authors: Optional[str] = " ,".join(AUTHORS)

    @model_validator(mode="before")
    @classmethod
    def set_generated_fields(cls, data: Any) -> Any:
        """Constructs the fields that are generated from other fields."""
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


def _generate_covv_location(region: str) -> str:
    return f"Europe/Sweden/{region}"


def _generate_covv_subm_sample_id(subm_sample_id: str, region_code: str) -> str:
    return f"{region_code}_SE100_{subm_sample_id}"


def _generate_covv_virus_name(covv_subm_sample_id: str, covv_collection_date: str) -> str:
    datetime_date: datetime = datetime.strptime(covv_collection_date, "%Y-%m-%d")
    return f"hCoV-19/Sweden/{covv_subm_sample_id}/{datetime_date.year}"
