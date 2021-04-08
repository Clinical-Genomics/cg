from typing import Optional, Literal
from pydantic import BaseModel, validator


class Lab(BaseModel):
    city: str
    address: str
    region_nr: str
    institute: str


class GisaidSample(BaseModel):
    lab: Lab
    submitter: str
    fn: str
    covv_collection_date: str
    covv_orig_lab: Optional[str]
    covv_virus_name: Optional[str]
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
    covv_subm_sample_id: str
    covv_authors: Optional[
        str
    ] = "Jan Albert, Tobias Allander, Annelie Bjerkner, Sandra Broddesson, Robert Dyrdak, Martin Ekman, Lynda Eneh, Lina Guerra Blomqvist, Karolina Ininbergs, Tanja Normark, Isak Sylvin, Zhibing Yun, Martina Wahlund, Valtteri Wirta"

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

    @validator("covv_virus_name", always=True)
    def parse_virus_name(cls, v, values):
        lab = values.get("lab")
        return f"hCoV-19/Sweden/{lab.region_nr}_SE100/"

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
