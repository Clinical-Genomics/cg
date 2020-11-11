"""Parse the MIP qc_metric file"""


def set_bamstats_metrics(file_metrics: dict, sample_data: dict) -> None:
    """Set bamstats metrics. Sum the total mapped reads for all sample BAM files"""
    total_reads = sample_data.get("reads", 0)
    sample_data["reads"] = int(file_metrics["bamstats"]["raw_total_sequences"]) + total_reads

    total_mapped = sample_data.get("total_mapped", 0)
    sample_data["total_mapped"] = int(file_metrics["bamstats"]["reads_mapped"]) + total_mapped


def set_chanjo_sexcheck_metrics(file_metrics: dict, sample_data: dict) -> None:
    """Set chanjo_sexcheck metrics"""
    sample_data["predicted_sex"] = file_metrics["chanjo_sexcheck"]["gender"]


def set_collecthsmetrics_metrics(file_metrics: dict, sample_data: dict) -> None:
    """Set collecthsmetrics metrics"""
    hs_metrics = file_metrics["collecthsmetrics"]["header"]["data"]
    sample_data["at_dropout"] = float(hs_metrics["AT_DROPOUT"])
    sample_data["completeness_target"] = {
        10: float(hs_metrics["PCT_TARGET_BASES_10X"]),
        20: float(hs_metrics["PCT_TARGET_BASES_20X"]),
        50: float(hs_metrics["PCT_TARGET_BASES_50X"]),
        100: float(hs_metrics["PCT_TARGET_BASES_100X"]),
    }
    sample_data["gc_dropout"] = float(hs_metrics["GC_DROPOUT"])
    sample_data["target_coverage"] = float(hs_metrics["MEAN_TARGET_COVERAGE"])


def set_collectmultiplemetrics_metrics(file_metrics: dict, sample_data: dict) -> None:
    """Set collectmultiplemetrics metrics"""
    mm_metrics = file_metrics["collectmultiplemetrics"]["header"]["pair"]
    sample_data["strand_balance"] = float(mm_metrics["STRAND_BALANCE"])


def set_collectmultiplemetricsinsertsize_metrics(file_metrics: dict, sample_data: dict) -> None:
    """Set collectmultiplemetricsinsertsize metrics"""
    mm_insert_metrics = file_metrics["collectmultiplemetricsinsertsize"]["header"]["data"]
    sample_data["median_insert_size"] = int(mm_insert_metrics["MEDIAN_INSERT_SIZE"])
    sample_data["insert_size_standard_deviation"] = float(mm_insert_metrics["STANDARD_DEVIATION"])


def set_markduplicates_metrics(file_metrics: dict, sample_data: dict) -> None:
    """Set markduplicates metrics"""
    sample_data["duplicates"] = float(file_metrics["markduplicates"]["fraction_duplicates"])


def get_sample_metrics(sample_metrics: dict, sample_data: dict) -> dict:
    """Get tool qc metrics from sample metrics"""
    get_metrics = {
        "bamstats": set_bamstats_metrics,
        "chanjo_sexcheck": set_chanjo_sexcheck_metrics,
        "collecthsmetrics": set_collecthsmetrics_metrics,
        "collectmultiplemetrics": set_collectmultiplemetrics_metrics,
        "collectmultiplemetricsinsertsize": set_collectmultiplemetricsinsertsize_metrics,
        "markduplicates": set_markduplicates_metrics,
    }

    for file_metrics in sample_metrics.values():

        for tool in file_metrics:

            if get_metrics.get(tool):
                get_metrics[tool](file_metrics=file_metrics, sample_data=sample_data)
    return sample_data


def parse_qcmetrics(metrics: dict) -> dict:
    """Parse MIP qc metrics file
    Args:
        metrics (dict): raw YAML input from MIP qc metrics file
    Returns:
        dict: parsed qc metrics metrics
    """
    qc_metric = {}

    for sample_id, sample_metrics in metrics["sample"].items():

        sample_data = {
            "id": sample_id,
        }
        sample_data = get_sample_metrics(sample_metrics=sample_metrics, sample_data=sample_data)
        sample_data["mapped"] = sample_data["total_mapped"] / sample_data["reads"]
        qc_metric[sample_id] = sample_data
    return qc_metric
