"""Constans for cg"""

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

# used to convert MIP tags derived from the deliverables to standard MIP tags.
MIP_TAGS = {
    tuple(["config"]): ["mip-config"],
    tuple(["sampleinfo"]): ["sampleinfo"],
    tuple(["multiqc_ar", "html"]): ["multiqc-html"],
    tuple(["multiqc_ar", "json"]): ["multiqc-json"],
    tuple(["pedigree"]): ["pedigree-yaml"],
    tuple(["pedigree_fam"]): ["pedigree"],
    tuple(["log"]): ["mip-log"],
    tuple(["qccollect_ar"]): ["qcmetrics"],
    tuple(["gatk_combinevariantcallsets", "bcf"]): ["snv-gbcf", "snv-bcf"],
    tuple(["sv_combinevariantcallsets", "bcf"]): ["sv-bcf"],
    tuple(["peddy_ar", "ped_check"]): ["peddy", "ped-check"],
    tuple(["peddy_ar", "peddy"]): ["peddy", "ped"],
    tuple(["peddy_ar", "sex_check"]): ["peddy", "sex-check"],
    tuple(["version_collect_ar"]): ["exe-ver"],
    tuple(["sv_str"]): ["vcf-str"],
    tuple(["clinical", "endvariantannotationblock"]): ["vcf-snv-clinical"],
    tuple(["research", "endvariantannotationblock"]): ["vcf-snv-research"],
    tuple(["clinical", "sv_reformat"]): ["vcf-sv-clinical"],
    tuple(["research", "sv_reformat"]): ["vcf-sv-research"],
    tuple(["samtools_subsample_mt", "bam"]): ["bam-mt"],
    tuple(["chromograph_ar"]): ["chromograph"],
    tuple(["vcf2cytosure_ar"]): ["vcf2cytosure"],
}
