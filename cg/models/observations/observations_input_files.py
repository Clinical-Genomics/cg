from pathlib import Path

from pydantic import BaseModel, Field, validator


def check_observation_file_from_hk(file_tag: str, file: Path) -> bool:
    """Check if file exists in HK and file system"""
    if file is None:
        raise FileNotFoundError(f"No file with {file_tag} tag in housekeeper")
    if not file.exists():
        raise FileNotFoundError(f"{file} does not exist")
    return True


class ObservationsInputFiles(BaseModel):
    """Model for validating input files to Loqus"""

    case_id: str
    pedigree: Path
    snv_gbcf: Path
    sv_vcf: Path = None
    vcf: Path

    @validator("pedigree", always=True)
    def check_pedigree(cls, value) -> Path:
        """Check pedigree file exists in HK and file system"""
        if check_observation_file_from_hk(file_tag="pedigree", file=value):
            return value

    @validator("sv_vcf", always=True)
    def check_sv_vcf(cls, value) -> Path:
        """Check sv_vcf file exists in HK and file system"""
        if not value:
            return value
        if check_observation_file_from_hk(file_tag="sv_vcf", file=value):
            return value

    @validator("snv_gbcf", always=True)
    def check_snv_gbcf(cls, value) -> Path:
        """Check snv_gbcf file exists in HK and file system"""
        if check_observation_file_from_hk(file_tag="snv_gbcf", file=value):
            return value

    @validator("vcf", always=True)
    def check_vcf(cls, value) -> Path:
        """Check vcf file exists in HK and file system"""
        if check_observation_file_from_hk(file_tag="vcf", file=value):
            return value


def parse_input_files(input_file: dict) -> ObservationsInputFiles:
    """Validate and parse MIP config file"""
    return ObservationsInputFiles(**input_file)
