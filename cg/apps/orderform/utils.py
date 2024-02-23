from cg.models.orders.excel_sample import ExcelSample


def are_all_samples_metagenome(samples: list[ExcelSample]) -> bool:
    """Check if all samples are metagenome samples"""
    return all(sample.application.startswith("ME") for sample in samples)
