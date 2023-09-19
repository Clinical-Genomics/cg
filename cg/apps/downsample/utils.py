"""Utility functions for the downsample app."""
from typing import List, Iterator

from cg.store import Store


def format_down_sample_case(
    case_internal_id: str, status_db: Store, number_of_reads: int
) -> List[str]:
    """Format a case identifier to the correct format."""
    sample_internal_ids: Iterator[str] = status_db.get_sample_ids_by_case_id(
        case_id=case_internal_id
    )
    sample_reads: List[str] = []
    for sample_internal_id in sample_internal_ids:
        sample_reads.append(f"{sample_internal_id};{number_of_reads}")
    return sample_reads
