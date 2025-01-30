from pydantic.dataclasses import dataclass


@dataclass
class RNADNACollection:
    """Contains the id for an RNA sample, the name of its connected DNA sample,
    and a list of connected, uploaded DNA cases."""

    rna_sample_id: str
    dna_sample_name: str
    dna_case_ids: list[str]
