from cg.constants import DataDelivery

TOMTE_DELIVERY_TYPES = [
    DataDelivery.ANALYSIS_FILES,
    DataDelivery.FASTQ,
    DataDelivery.FASTQ_ANALYSIS,
    DataDelivery.NO_DELIVERY,
]


def validate_tomte_delivery_type(delivery_type: DataDelivery):
    if delivery_type not in TOMTE_DELIVERY_TYPES:
        raise ValueError("Delivery type not allowed.")
