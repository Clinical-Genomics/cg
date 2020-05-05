"""Constans for cg"""

PRIORITY_MAP = {
    "research": 0,
    "standard": 1,
    "priority": 2,
    "express": 3,
    "clinical trials": 4,
}
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

# Constants for crunchy
BAM_SUFFIX = ".bam"
BAM_INDEX_SUFFIX = ".bai"
CRAM_SUFFIX = ".cram"
CRAM_INDEX_SUFFIX = ".crai"
FASTQ_FIRST_READ_SUFFIX = "R1_001.fastq.gz"
FASTQ_SECOND_READ_SUFFIX = "R2_001.fastq.gz"
SPRING_SUFFIX = ".spring"

# tags for storing analyses in Housekeeper
HK_TAGS = {
    "wes": ["mip-dna", "wes"],
    "wgs": ["mip-dna", "wgs"],
    "wts": ["mip-rna"],
}

# used to convert MIP tags derived from the deliverables to MIP standard tags and to check for
# presence of mandatory files. Keys = tags found in deliverables, values = MIP standard tags and
# mandatory flag
MIP_TAGS = {
    tuple(["config"]): {"tags": ["mip-config"], "is_mandatory": True,},
    tuple(["sample_info"]): {"tags": ["sampleinfo"], "is_mandatory": True,},
    tuple(["multiqc_ar", "html"]): {"tags": ["multiqc-html"], "is_mandatory": True,},
    tuple(["multiqc_ar", "json"]): {"tags": ["multiqc-json"], "is_mandatory": True,},
    tuple(["pedigree"]): {"tags": ["pedigree-yaml"], "is_mandatory": True,},
    tuple(["pedigree_fam"]): {"tags": ["pedigree"], "is_mandatory": True,},
    tuple(["log"]): {"tags": ["mip-log"], "is_mandatory": True,},
    tuple(["qccollect_ar"]): {"tags": ["qcmetrics"], "is_mandatory": True,},
    tuple(["gatk_combinevariantcallsets", "bcf"]): {
        "tags": ["snv-gbcf", "snv-bcf"],
        "is_mandatory": True,
    },
    tuple(["sv_combinevariantcallsets", "bcf"]): {
        "tags": ["sv-bcf"],
        "is_mandatory": True,
    },
    tuple(["peddy_ar", "ped_check"]): {
        "tags": ["peddy", "ped-check"],
        "is_mandatory": True,
    },
    tuple(["peddy_ar", "peddy"]): {"tags": ["peddy", "ped"], "is_mandatory": True,},
    tuple(["peddy_ar", "sex_check"]): {
        "tags": ["peddy", "sex-check"],
        "is_mandatory": True,
    },
    tuple(["version_collect_ar"]): {"tags": ["exe-ver"], "is_mandatory": True,},
    tuple(["sv_str"]): {"tags": ["vcf-str"], "is_mandatory": True,},
    tuple(["clinical", "endvariantannotationblock"]): {
        "tags": ["vcf-snv-clinical"],
        "is_mandatory": True,
    },
    tuple(["research", "endvariantannotationblock"]): {
        "tags": ["vcf-snv-research"],
        "is_mandatory": True,
    },
    tuple(["clinical", "sv_reformat"]): {
        "tags": ["vcf-sv-clinical"],
        "is_mandatory": False,
    },
    tuple(["research", "sv_reformat"]): {
        "tags": ["vcf-sv-research"],
        "is_mandatory": False,
    },
    tuple(["samtools_subsample_mt", "bam"]): {
        "tags": ["bam-mt"],
        "is_mandatory": False,
    },
    tuple(["chromograph_ar"]): {"tags": ["chromograph"], "is_mandatory": False,},
    tuple(["vcf2cytosure_ar"]): {"tags": ["vcf2cytosure"], "is_mandatory": False,},
}
