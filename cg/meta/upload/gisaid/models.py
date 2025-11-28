from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator

from cg.meta.upload.gisaid.constants import AUTHORS


class GisaidAccession(BaseModel):
    log_message: str
    accession_nr: str | None = None
    sample_id: str | None = None

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
    covv_virus_name: str | None = None
    covv_orig_lab: str | None = None
    covv_type: str | None = "betacoronavirus"
    covv_passage: str | None = "Original"
    covv_location: str | None = None
    covv_host: str | None = "Human"
    covv_gender: str | None = "unknown"
    covv_patient_age: str | None = "unknown"
    covv_patient_status: str | None = "unknown"
    covv_seq_technology: str | None = "Illumina NovaSeq"
    covv_orig_lab_addr: str | None = None
    covv_subm_lab: str | None = "Karolinska University Hospital"
    covv_subm_lab_addr: str | None = "171 76 Stockholm, Sweden"
    covv_authors: str | None = " ,".join(AUTHORS)

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
