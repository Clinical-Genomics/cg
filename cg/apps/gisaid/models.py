from pydantic import BaseModel


def GisaidSample(BaseModel):
    submitter: str
    fn: str
    covv_collection_date: str
    covv_orig_lab: str
    covv_virus_name: str = f"hCoV-19/Sweden/{regionnumber(01/09}SE100/"
    covv_type: Optional[str] = "betacoronavirus"
    covv_passage: Optional[str] = "Original"
    covv_location: Optional[str] = f"Europe/Sweden/{Gotland/stockholm}"
    covv_host: Optional[str] = "Human"
    covv_gender: Optional[str] = "unknown"
    covv_patient_age: Optional[str] = "unknown"
    covv_patient_status: Optional[str] = "unknown"
    covv_seq_technology: Optional[str] = "Illumina NovaSeq"
    covv_orig_lab_addr: Optional[
        str
    ] = f"<Parse from orig lab: 621 84 Visby, Sweden/171 76 Stockholm, Sweden>"
    covv_subm_lab: Optional[str] = "Karolinska University Hospital"
    covv_subm_lab_addr: Optional[str] = "171 76 Stockholm, Sweden"
    covv_subm_sample_id: Optional[str] = "<region nummer>_SE100_<lims sample name>"
    covv_authors: Optional[
        str
    ] = "Jan Albert, Tobias Allander, Annelie Bjerkner, Sandra Broddesson, Robert Dyrdak, Martin Ekman, Lynda Eneh, Lina Guerra Blomqvist, Karolina Ininbergs, Tanja Normark, Isak Sylvin, Zhibing Yun, Martina Wahlund, Valtteri Wirta"
