from pathlib import Path
from typing import Optional
from pydantic import BaseModel, validator
from datetime import date, datetime

from cg.meta.upload.gisaid.constants import AUTHORS


class FastaFile(BaseModel):
    header: str
    sequence: str


class GisaidAccession(BaseModel):
    log_message: str
    accession_nr: Optional[str]
    sample_id: Optional[str]

    @validator("accession_nr", always=True)
    def parse_accession(cls, v, values):
        return values["log_message"].split(";")[-1]

    @validator("sample_id", always=True)
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
    covv_virus_name: Optional[str]
    covv_orig_lab: Optional[str]
    covv_type: Optional[str] = "betacoronavirus"
    covv_passage: Optional[str] = "Original"
    covv_location: Optional[str]
    covv_host: Optional[str] = "Human"
    covv_gender: Optional[str] = "unknown"
    covv_patient_age: Optional[str] = "unknown"
    covv_patient_status: Optional[str] = "unknown"
    covv_seq_technology: Optional[str] = "Illumina NovaSeq"
    covv_orig_lab_addr: Optional[str]
    covv_subm_lab: Optional[str] = "Karolinska University Hospital"
    covv_subm_lab_addr: Optional[str] = "171 76 Stockholm, Sweden"
    covv_authors: Optional[str] = " ,".join(AUTHORS)

    @validator("covv_location", always=True)
    def parse_location(cls, v, values):
        region: str = values.get("region")
        return f"Europe/Sweden/{region}"

    @validator("covv_subm_sample_id", always=True)
    def parse_subm_sample_id(cls, v, values):
        region_code = values.get("region_code")
        return f"{region_code}_SE100_{v}"

    @validator("covv_virus_name", always=True)
    def parse_virus_name(cls, v, values):
        sample_name = values.get("covv_subm_sample_id")
        date = values.get("covv_collection_date")
        datetime_date = datetime.strptime(date, "%Y-%m-%d")
        return f"hCoV-19/Sweden/{sample_name}/{datetime_date.year}"
