"""NF-core pipelines related constants."""


class MetricConditions:
    RNAFUSION_METRIC_CONDITIONS: dict = {
        "uniquely_mapped_percent": {"norm": "gt", "threshold": 60},
        "PCT_MRNA_BASES": {"norm": "gt", "threshold": 80},
        "PCT_RIBOSOMAL_BASES": {"norm": "lt", "threshold": 5},
        "PERCENT_DUPLICATION": {"norm": "lt", "threshold": 0.7},
    }

    TAXPROFILER_METRIC_CONDITIONS: dict = {}

    @classmethod
    def get(cls, metric_name, param):
        pass
