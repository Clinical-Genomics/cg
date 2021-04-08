from typing import Optional, Literal
from pydantic import BaseModel, validator


def Lab(BaseModel):
    city: str
    address: str
    region_nr: str


def GisaidSample(BaseModel):
    lab: Lab
    submitter: str
    fn: str
    covv_collection_date: str
    covv_orig_lab: Optional[Literal["Stockholm", "Visby"]]
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

    @validator("lab")
    def lab_info(cls, v):
        if v == "Stockholm":
            return Lab(city="Stockholm", address="171 76 Stockholm, Sweden", region_nr="01")
        elif v == "Visby":
            Lab(city="Visby", address="621 84 Visby, Sweden", region_nr="09")

    @validator("covv_virus_name")
    def parse_virus_name(cls, v, values):
        return f"hCoV-19/Sweden/{values.lab.region_nr}_SE100/"

    @validator("covv_location")
    def parse_location(cls, v, values):
        return f"Europe/Sweden/{values.lab.city}"

    @validator("covv_orig_lab_addr")
    def parse_orig_lab_addr(cls, v, values):
        return values.lab.address

    @validator("covv_subm_sample_id")
    def parse_subm_sample_id(cls, v, values):
        return f"{values.lab.region_nr}_SE100_{v}"
