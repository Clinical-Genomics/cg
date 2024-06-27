from enum import StrEnum

from cg.constants.constants import Workflow


class OrderType(StrEnum):
    BALSAMIC: str = Workflow.BALSAMIC
    BALSAMIC_QC: str = Workflow.BALSAMIC_QC
    BALSAMIC_UMI: str = Workflow.BALSAMIC_UMI
    FASTQ: str = Workflow.FASTQ
    FLUFFY: str = Workflow.FLUFFY
    METAGENOME: str = "metagenome"
    MICROSALT: str = Workflow.MICROSALT
    MIP_DNA: str = Workflow.MIP_DNA
    MIP_RNA: str = Workflow.MIP_RNA
    RML: str = "rml"
    RNAFUSION: str = Workflow.RNAFUSION
    SARS_COV_2: str = "sars-cov-2"
    TOMTE: str = Workflow.TOMTE


class ExcelSampleAliases(StrEnum):
    AGE_AT_SAMPLING = "UDF/age_at_sampling"
    APPLICATION = "UDF/Sequencing Analysis"
    CAPTURE_KIT = "UDF/Capture Library version"
    COHORTS = "UDF/cohorts"
    COLLECTION_DATE = "UDF/Collection Date"
    COMMENT = "UDF/Comment"
    CONCENTRATION = "UDF/Concentration (nM)"
    CONCENTRATION_NG_UL = "UDF/Concentration (ng/ul)"
    CONCENTRATION_SAMPLE = "UDF/Sample Conc."
    CONTAINER = "Container/Type"
    CONTAINER_NAME = "Container/Name"
    CONTROL = "UDF/Control"
    CUSTOM_INDEX = "UDF/Custom index"
    CUSTOMER = "UDF/customer"
    DATA_ANALYSIS = "UDF/Data Analysis"
    DATA_DELIVERY = "UDF/Data Delivery"
    ELUTION_BUFFER = "UDF/Sample Buffer"
    EXTRACTION_METHOD = "UDF/Extraction method"
    FAMILY_NAME = "UDF/familyID"
    FATHER = "UDF/fatherID"
    FORMALIN_FIXATION_TIME = "UDF/Formalin Fixation Time"
    INDEX = "UDF/Index type"
    INDEX_NUMBER = "UDF/Index number"
    LAB_CODE = "UDF/Lab Code"
    MOTHER = "UDF/motherID"
    NAME = "Sample/Name"
    ORGANISM = "UDF/Strain"
    ORGANISM_OTHER = "UDF/Other species"
    ORIGINAL_LAB = "UDF/Original Lab"
    ORIGINAL_LAB_ADDRESS = "UDF/Original Lab Address"
    PANELS = "UDF/Gene List"
    POOL = "UDF/pool name"
    POST_FORMALIN_FIXATION_TIME = "UDF/Post Formalin Fixation Time"
    PRE_PROCESSING_METHOD = "UDF/Pre Processing Method"
    PRIMER = "UDF/Primer"
    PRIORITY = "UDF/priority"
    QUANTITY = "UDF/Quantity"
    REAGENT_LABEL = "Sample/Reagent Label"
    REFERENCE_GENOME = "UDF/Reference Genome Microbial"
    REGION = "UDF/Region"
    REGION_CODE = "UDF/Region Code"
    REQUIRE_QC_OK = "UDF/Process only if QC OK"
    RML_PLATE_NAME = "UDF/RML plate name"
    SELECTION_CRITERIA = "UDF/Selection Criteria"
    SEX = "UDF/Gender"
    SOURCE = "UDF/Source"
    STATUS = "UDF/Status"
    SUBJECT_ID = "UDF/subjectID"
    SYNOPSIS = "UDF/synopsis"
    TISSUE_BLOCK_SIZE = "UDF/Tissue Block Size"
    TUMOUR = "UDF/tumor"
    TUMOUR_PURITY = "UDF/tumour purity"
    VOLUME = "UDF/Volume (uL)"
    WELL_POSITION = "Sample/Well Location"
    WELL_POSITION_RML = "UDF/RML well position"
