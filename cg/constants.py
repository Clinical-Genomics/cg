"""Constans for cg"""

TMP_DIR = "/home/proj/production/rare-disease/temp-dir/"

PRIORITY_MAP = {"research": 0, "standard": 1, "priority": 2, "express": 3, "clinical trials": 4}
REV_PRIORITY_MAP = {value: key for key, value in PRIORITY_MAP.items()}
PRIORITY_OPTIONS = list(PRIORITY_MAP.keys())
FAMILY_ACTIONS = ("analyze", "running", "hold")
PREP_CATEGORIES = ("wgs", "wes", "tgs", "wts", "mic", "rml")
SEX_OPTIONS = ("male", "female", "unknown")
STATUS_OPTIONS = ("affected", "unaffected", "unknown")
CONTAINER_OPTIONS = ("Tube", "96 well plate")
CAPTUREKIT_OPTIONS = (
    "Agilent Sureselect CRE",
    "Agilent Sureselect V5",
    "SureSelect Focused Exome",
    "Twist_Target_hg19.bed",
    "other",
)
CAPTUREKIT_CANCER_OPTIONS = (
    "GIcfDNA",
    "GMCKsolid",
    "GMSmyeloid",
    "LymphoMATIC",
    "other (specify in comment field)",
)
DEFAULT_CAPTURE_KIT = "twistexomerefseq_9.1_hg19_design.bed"

COMBOS = {
    "DSD": ("DSD", "HYP", "SEXDIF", "SEXDET"),
    "CM": ("CNM", "CM"),
    "Horsel": ("Horsel", "141217", "141201"),
}
COLLABORATORS = ("cust000", "cust002", "cust003", "cust004", "cust042")
MASTER_LIST = (
    "BRAIN",
    "Cardiology",
    "CTD",
    "ENDO",
    "EP",
    "IBMFS",
    "IEM",
    "IF",
    "NEURODEG",
    "NMD",
    "mcarta",
    "MIT",
    "MOVE",
    "mtDNA",
    "PEDHEP",
    "PID",
    "PIDCAD",
    "OMIM-AUTO",
    "SKD",
)
FLOWCELL_STATUS = ("ondisk", "removed", "requested", "processing")
METAGENOME_SOURCES = (
    "blood",
    "skin",
    "respiratory",
    "urine",
    "CSF",
    "faeces",
    "environmental",
    "unknown",
    "other",
)
ANALYSIS_SOURCES = (
    "blood",
    "buccal swab",
    "cell-free DNA",
    "cell line",
    "cytology (FFPE)",
    "cytology (not fixed/fresh)",
    "muscle",
    "nail",
    "saliva",
    "skin",
    "tissue (FFPE)",
    "tissue (fresh frozen)",
    "bone marrow",
    "other",
)
NO_PARENT = "0"

# Constants for crunchy
FASTQ_FIRST_READ_SUFFIX = "_R1_001.fastq.gz"
FASTQ_SECOND_READ_SUFFIX = "_R2_001.fastq.gz"
SPRING_SUFFIX = ".spring"
# Number of days until fastqs counts as old
FASTQ_DELTA = 21

# tags for storing analyses in Housekeeper
HK_TAGS = {
    "wes": ["mip-dna", "wes"],
    "wgs": ["mip-dna", "wgs"],
    "wts": ["mip-rna"],
    "microbial": ["microsalt"],
}
HK_FASTQ_TAGS = ["fastq"]

# used to convert MIP tags derived from the deliverables to MIP standard tags and to check for
# presence of mandatory files. Keys = tags found in deliverables, values = MIP standard tags and
# mandatory flag
MIP_DNA_TAGS = {
    ("chanjo_sexcheck",): {"tags": ["chanjo", "sex-check"], "is_mandatory": False},
    ("chromograph_ar",): {"tags": ["chromograph"], "is_mandatory": False},
    ("endvariantannotationblock", "clinical"): {
        "tags": ["vcf-snv-clinical"],
        "index_tags": ["vcf-snv-clinical-index"],
        "is_mandatory": True,
    },
    ("endvariantannotationblock", "research"): {
        "tags": ["vcf-snv-research"],
        "index_tags": ["vcf-snv-research-index"],
        "is_mandatory": True,
    },
    ("expansionhunter", "sv_str"): {
        "tags": ["vcf-str"],
        "index_tags": ["vcf-str-index"],
        "is_mandatory": False,
    },
    ("gatk_baserecalibration",): {
        "tags": ["cram"],
        "index_tags": ["cram-index"],
        "is_mandatory": False,
    },
    ("gatk_combinevariantcallsets",): {
        "tags": ["snv-gbcf", "snv-bcf"],
        "index_tags": ["gbcf-index"],
        "is_mandatory": True,
    },
    ("mip_analyse", "config"): {"tags": ["mip-analyse", "config"], "is_mandatory": True},
    ("mip_analyse", "config_analysis"): {"tags": ["mip-config"], "is_mandatory": True},
    ("mip_analyse", "log"): {"tags": ["mip-log"], "is_mandatory": True},
    ("mip_analyse", "pedigree"): {"tags": ["pedigree-yaml"], "is_mandatory": True},
    ("mip_analyse", "pedigree_fam"): {"tags": ["pedigree"], "is_mandatory": True},
    ("mip_analyse", "references_info"): {
        "tags": ["mip-analyse", "reference-info"],
        "is_mandatory": True,
    },
    ("mip_analyse", "sample_info"): {"tags": ["sampleinfo"], "is_mandatory": True},
    ("multiqc_ar", "html"): {"tags": ["multiqc-html"], "is_mandatory": True},
    ("multiqc_ar", "json"): {"tags": ["multiqc-json"], "is_mandatory": True},
    ("peddy_ar", "ped_check"): {"tags": ["peddy", "ped-check"], "is_mandatory": True},
    ("peddy_ar", "peddy"): {"tags": ["peddy", "ped"], "is_mandatory": True},
    ("peddy_ar", "sex_check"): {"tags": ["peddy", "sex-check"], "is_mandatory": True},
    ("qccollect_ar",): {"tags": ["qcmetrics"], "is_mandatory": True},
    ("sambamba_depth", "coverage"): {"tags": ["coverage", "sambamba-depth"], "is_mandatory": True},
    ("samtools_subsample_mt",): {
        "tags": ["bam-mt"],
        "index_tags": ["bam-mt-index"],
        "is_mandatory": False,
    },
    ("smncopynumbercaller",): {
        "tags": ["smn-calling", "smncopynumbercaller"],
        "is_mandatory": False,
    },
    ("star_caller",): {
        "tags": ["cyrius", "star-caller"],
        "is_mandatory": False,
    },
    ("sv_combinevariantcallsets",): {
        "tags": ["sv-bcf"],
        "index_tags": ["sv-bcf-index"],
        "is_mandatory": True,
    },
    ("sv_reformat", "clinical"): {
        "tags": ["vcf-sv-clinical"],
        "index_tags": ["vcf-sv-clinical-index"],
        "is_mandatory": False,
    },
    ("sv_reformat", "research"): {
        "tags": ["vcf-sv-research"],
        "index_tags": ["vcf-sv-research-index"],
        "is_mandatory": False,
    },
    ("telomerecat_ar",): {
        "tags": ["telomere-calling", "telomerecat"],
        "is_mandatory": False,
    },
    ("tiddit_coverage",): {
        "tags": ["tiddit-coverage", "bigwig"],
        "is_mandatory": False,
    },
    ("version_collect_ar",): {"tags": ["exe-ver"], "is_mandatory": True},
    ("vcf2cytosure_ar",): {"tags": ["vcf2cytosure"], "is_mandatory": False},
}


MIP_RNA_TAGS = {
    ("arriba_ar", "arriba_ar"): {"tags": ["arriba-ar"], "is_mandatory": True},
    ("arriba_ar", "arriba_report"): {"tags": ["arriba-ar", "arriba-report"], "is_mandatory": True},
    ("bcftools_merge",): {"tags": ["bcftools-merge"], "is_mandatory": True},
    ("blobfish",): {"tags": ["blobfish"], "is_mandatory": False},
    ("bootstrapann",): {"tags": ["bootstrapann"], "is_mandatory": True},
    ("gatk_asereadcounter",): {"tags": ["gatk-asereadcounter"], "is_mandatory": True},
    ("gffcompare_ar",): {"tags": ["gffcompare-ar"], "is_mandatory": True},
    ("markduplicates",): {"tags": ["cram"], "index_tags": ["cram-index"], "is_mandatory": True},
    ("mip_analyse", "config"): {"tags": ["mip-analyse", "config"], "is_mandatory": True},
    ("mip_analyse", "config_analysis"): {
        "tags": ["mip-analyse", "config-analysis"],
        "is_mandatory": True,
    },
    ("mip_analyse", "log"): {"tags": ["mip-analyse", "log"], "is_mandatory": True},
    ("mip_analyse", "pedigree"): {"tags": ["mip-analyse", "pedigree"], "is_mandatory": True},
    ("mip_analyse", "pedigree_fam"): {
        "tags": ["mip-analyse", "pedigree-fam"],
        "is_mandatory": True,
    },
    ("mip_analyse", "references_info"): {
        "tags": ["mip-analyse", "reference-info"],
        "is_mandatory": True,
    },
    ("mip_analyse", "sample_info"): {"tags": ["mip-analyse", "sample-info"], "is_mandatory": True},
    ("multiqc_ar", "html"): {"tags": ["multiqc-html"], "is_mandatory": True},
    ("multiqc_ar", "json"): {"tags": ["multiqc-json"], "is_mandatory": True},
    ("salmon_quant",): {"tags": ["salmon-quant"], "is_mandatory": True},
    ("star_fusion",): {"tags": ["star-fusion"], "is_mandatory": True},
    ("stringtie_ar",): {"tags": ["stringtie-ar"], "is_mandatory": True},
    ("varianteffectpredictor",): {"tags": ["varianteffectpredictor"], "is_mandatory": True},
    ("version_collect_ar",): {"tags": ["version-collect-ar"], "is_mandatory": True},
}

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

# Symbols
SINGLE_QUOTE = "'"
SPACE = " "

# Processes
RETURN_SUCCESS = 0
EXIT_SUCCESS = 0
EXIT_FAIL = 1
