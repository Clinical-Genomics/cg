from cg.models.orders.constants import OrderType
from cg.models.orders.excel_sample import ExcelSample

ORDER_TYPES_WITH_CASES = [
    OrderType.BALSAMIC,
    OrderType.BALSAMIC_UMI,
    OrderType.MIP_DNA,
    OrderType.MIP_RNA,
    OrderType.NALLO,
    OrderType.RNAFUSION,
    OrderType.TOMTE,
]


def are_all_samples_metagenome(samples: list[ExcelSample]) -> bool:
    """Check if all samples are metagenome samples"""
    return all(sample.application.startswith("ME") for sample in samples)
