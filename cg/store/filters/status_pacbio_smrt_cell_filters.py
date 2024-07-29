"""Filters for the PacBio SMRT cell model."""

from enum import Enum

from sqlalchemy.orm import Query


def filter_pac_bio_smrt_cell_by_internal_id(smrt_cells: Query, internal_id: str, **kwargs) -> Query:
    """Get a PacBio SMRT cell by its internal id."""
    return smrt_cells.filter_by(internal_id=internal_id)


def apply_pac_bio_smrt_cell_filters(
    smrt_cells: Query, filter_functions: list[callable], internal_id: str
) -> Query:
    """Apply filtering functions and return filtered results."""
    for function in filter_functions:
        smrt_cells: Query = function(
            smrt_cells=smrt_cells,
            internal_id=internal_id,
        )
    return smrt_cells


class PacBioSMRTCellFilter(Enum):
    """Define SMRT cell filter functions."""

    BY_INTERNAL_ID: callable = filter_pac_bio_smrt_cell_by_internal_id
