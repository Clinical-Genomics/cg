"""Tags for storing analyses in Housekeeper"""

HK_TAGS = {
    "microsalt": ["microsalt"],
}
HK_FASTQ_TAGS = ["fastq"]


MICROSALT_TAGS = {
    ("alignment", "reference-alignment"): {
        "tags": ["alignment", "reference-alignment"],
        "is_mandatory": True,
    },
    ("alignment", "reference-alignment-deduplicated"): {
        "tags": ["alignment", "reference-alignment-deduplicated"],
        "index_tags": ["reference-alignment-deduplicate-index"],
        "is_mandatory": True,
    },
    ("alignment", "reference-alignment-sorted"): {
        "tags": ["alignment", "reference-alignment-sorted"],
        "is_mandatory": True,
    },
    ("analysis", "logfile"): {
        "tags": ["analysis", "log"],
        "is_mandatory": True,
    },
    ("analysis", "runtime-settings"): {
        "tags": ["analysis", "runtime-settings"],
        "is_mandatory": True,
    },
    ("analysis", "sampleinfo"): {
        "tags": ["analysis", "sampleinfo"],
        "is_mandatory": True,
    },
    ("assembly", "assembly"): {
        "tags": ["assembly"],
        "is_mandatory": True,
    },
    ("assembly", "quast-results"): {
        "tags": ["assembly", "quast-results"],
        "is_mandatory": True,
    },
    ("concatination", "trimmed-forward-reads"): {
        "tags": ["concatination", "trimmed-forward-reads"],
        "is_mandatory": True,
    },
    ("concatination", "trimmed-reverse-reads"): {
        "tags": ["concatination", "trimmed-reverse-reads"],
        "is_mandatory": True,
    },
    ("result_aggregation", "microsalt-json"): {
        "tags": ["result-aggregation-json"],
        "is_mandatory": True,
    },
    ("result_aggregation", "microsalt-qc"): {
        "tags": ["result-aggregration-qc"],
        "is_mandatory": True,
    },
    ("result_aggregation", "microsalt-type"): {
        "tags": ["result-aggregation-type"],
        "is_mandatory": True,
    },
    ("insertsize_calc", "picard-insertsize"): {
        "tags": ["insertsize-calc", "picard-insertsize"],
        "is_mandatory": True,
    },
}
