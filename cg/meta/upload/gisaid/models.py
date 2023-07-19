from pathlib import Path
from typing import Optional
from pydantic import BaseModel, field_validator
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
    def parse_accession(cls, v, values):
        return values["log_message"].split(";")[-1]

    @field_validator("sample_id")
    def parse_sample_id(cls, v, values):
        return values["log_message"].split("/")[2].split("_")[2]


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
    covv_patient_age: Optional[str] = "unknown"
    covv_patient_status: Optional[str] = "unknown"
    covv_seq_technology: Optional[str] = "Illumina NovaSeq"
    covv_orig_lab_addr: Optional[str] = None
    covv_subm_lab: Optional[str] = "Karolinska University Hospital"
    covv_subm_lab_addr: Optional[str] = "171 76 Stockholm, Sweden"
    covv_authors: Optional[str] = " ,".join(AUTHORS)

    @field_validator("covv_location")
    def parse_location(cls, v, values):
        region: str = values.get("region")
        return f"Europe/Sweden/{region}"

    @field_validator("covv_subm_sample_id")
    def parse_subm_sample_id(cls, v, values):
        region_code = values.get("region_code")
        return f"{region_code}_SE100_{v}"

    @field_validator("covv_virus_name")
    def parse_virus_name(cls, v, values):
        sample_name = values.get("covv_subm_sample_id")
        date = values.get("covv_collection_date")
        datetime_date = datetime.strptime(date, "%Y-%m-%d")
        return f"hCoV-19/Sweden/{sample_name}/{datetime_date.year}"
