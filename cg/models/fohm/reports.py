"""FOHM report models."""

from pydantic import BaseModel, Field


class FohmComplementaryReport(BaseModel):
    """Model for validating FOHM complementary reports."""

    gisaid_accession: str = Field(str, alias="GISAID_accession")
    internal_id: str | None = Field(None, alias="clinical_genomics_prov_id")
    sample_number: str = Field(str, alias="provnummer")
    selection_criteria: str = Field(str, alias="urvalskriterium")
    region_lab: str | None = Field(None, alias="region_laboratorium")


class FohmPangolinReport(BaseModel):
    """Model for validating FOHM Pangolin reports."""

    ambiguity_score: str
    conflict: str
    constellation_version: str
    internal_id: str | None = None
    is_designated: str
    lineage: str
    note: str
    pangolin_version: str
    qc_notes: str
    region_lab: str | None = None
    qc_status: str
    scorpio_call: str
    scorpio_conflict: str
    scorpio_notes: str
    scorpio_support: str
    scorpio_version: str
    taxon: str
    version: str
