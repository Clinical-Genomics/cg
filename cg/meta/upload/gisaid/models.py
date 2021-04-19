from pathlib import Path
from typing import Optional
from pydantic import BaseModel, validator

from cg.meta.upload.gisaid.constants import AUTHORS


class FastaFile(BaseModel):
    header: str
    sequence: str


class UpploadFiles(BaseModel):
    csv_file: Path
    fasta_file: Path


class Lab(BaseModel):
    city: str
    address: str
    region_nr: str
    institute: str


class GisaidSample(BaseModel):
    family_id: str
    cg_lims_id: str
    lab: Lab
    submitter: str
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

    @validator("lab", pre=True)
    def lab_info(cls, v):
        if v == "Stockholm":
            return Lab(
                city="Stockholm",
                address="171 76 Stockholm, Sweden",
                region_nr="01",
                institute="Karolinska University Hospital",
            )
        elif v == "Visby":
            return Lab(
                city="Visby",
                address="621 84 Visby, Sweden",
                region_nr="09",
                institute="LaboratorieMedicinskt Centrum Gotland",
            )
        raise ValueError("must be Stockholm or Visby")

    @validator("covv_location", always=True)
    def parse_location(cls, v, values):
        lab = values.get("lab")
        return f"Europe/Sweden/{lab.city}"

    @validator("covv_orig_lab_addr", always=True)
    def parse_orig_lab_addr(cls, v, values):
        lab = values.get("lab")
        return lab.address

    @validator("covv_orig_lab", always=True)
    def parse_orig_lab(cls, v, values):
        lab = values.get("lab")
        return lab.institute

    @validator("covv_subm_sample_id", always=True)
    def parse_subm_sample_id(cls, v, values):
        lab = values.get("lab")
        return f"{lab.region_nr}_SE100_{v}"

    @validator("covv_virus_name", always=True)
    def parse_virus_name(cls, v, values):
        sample_name = values.get("covv_subm_sample_id")
        date = values.get("covv_collection_date")
        return f"hCoV-19/Sweden/{sample_name}/{date}"
