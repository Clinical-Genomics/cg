# LIMS constants

from enum import StrEnum

YES_NO_LIMS_BOOLEANS = ["require_qc_ok", "tumour", "verified_organism"]

PROP2UDF = {
    "application": "Sequencing Analysis",
    "bait_set": "Bait Set",
    "capture_kit": "Capture Library version",
    "collection_date": "Collection Date",
    "comment": "Comment",
    "concentration": "Concentration (nM)",
    "concentration_ng_ul": "Concentration (ng/ul)",
    "concentration_sample": "Sample Conc.",
    "control": "Control",
    "customer": "customer",
    "data_analysis": "Data Analysis",
    "data_delivery": "Data Delivery",
    "dv200": "DV200",
    "elution_buffer": "Sample Buffer",
    "extraction_method": "Extraction method",
    "family_name": "familyID",
    "formalin_fixation_time": "Formalin Fixation Time",
    "index": "Index type",
    "index_number": "Index number",
    "lab_code": "Lab Code",
    "organism": "Strain",
    "organism_other": "Other species",
    "original_lab": "Original Lab",
    "original_lab_address": "Original Lab Address",
    "pool": "pool name",
    "post_formalin_fixation_time": "Post Formalin Fixation Time",
    "pre_processing_method": "Pre Processing Method",
    "primer": "Primer",
    "priority": "priority",
    "quantity": "Quantity",
    "reference_genome": "Reference Genome Microbial",
    "region": "Region",
    "region_code": "Region Code",
    "require_qc_ok": "Process only if QC OK",
    "rin": "RIN",
    "rml_plate_name": "RML plate name",
    "selection_criteria": "Selection Criteria",
    "sequencing_qc_pass": "Passed Sequencing QC",
    "sex": "Gender",
    "skip_reception_control": "Skip Reception Control QC",
    "source": "Source",
    "target_reads": "Reads missing (M)",
    "tissue_block_size": "Tissue Block Size",
    "tumour": "tumor",
    "tumour_purity": "tumour purity",
    "verified_organism": "Verified organism",
    "volume": "Volume (uL)",
    "well_position_rml": "RML well position",
}

MASTER_STEPS_UDFS = {
    "capture_kit_step": {
        "obsolete_CG002 - Hybridize Library  (SS XT)": "SureSelect capture library/libraries used",
        "Hybridize Library TWIST v1": "Bait Set",
        "Hybridize Library TWIST v2": "Bait Set",
        "Target enrichment TWIST v1": "Bait Set",
        "Library Prep (Dev) v3": "Bait Set",
    },
    "rna_prep_step": {
        "Aliquot Samples for Fragmentation (RNA) v1": "Amount needed (ng)",
    },
    "prep_method_step": {
        "Library Preparation (Cov) v1": {
            "method_number": "Method document",
            "method_version": "Document version",
            "atlas_document": "Library Preparation Method",
            "atlas_version": "Atlas Version",
        },
        "Library Prep (Dev) v3": {
            "method_number": "Method Document",
            "method_version": "Document Version",
        },
        "CG002 - End repair Size selection A-tailing and Adapter ligation (TruSeq PCR-free DNA)": {
            "method_number": "Method document",
            "method_version": "Method document version",
        },
        "End repair Size selection A-tailing and Adapter ligation (TruSeq PCR-free DNA)": {
            "method_number": "Method document",
            "method_version": "Method document version",
            "atlas_document": "Library Preparation Method",
            "atlas_version": "Atlas Version",
        },
        "obsolete_CG002 - Hybridize Library  (SS XT)": {
            "method_number": "Method document",
            "method_version": "Method document version",
        },
        "CG002 - Microbial Library Prep (Nextera)": {
            "method_number": "Method",
            "method_version": "Method Version",
            "atlas_document": "Library Preparation Method",
            "atlas_version": "Atlas Version",
        },
        "End-Repair and A-tailing TWIST v1": {
            "method_number": "Method document",
            "method_version": "Document version",
        },
        "KAPA Library Preparation TWIST v1": {
            "method_number": "Method document",
            "method_version": "Document version",
            "atlas_document": "Library Preparation Method",
            "atlas_version": "Atlas Version",
        },
        "A-tailing and Adapter ligation (RNA) v1": {
            "method_number": "Method document",
            "method_version": "Document version",
            "atlas_document": "Library Preparation Method",
            "atlas_version": "Atlas Version",
        },
        "Library Prep PCR-free WGS v1": {
            "atlas_document": "Library Preparation Method",
            "atlas_version": "Atlas Version",
        },
        "SMRTbell library prep (Revio) v1": {
            "atlas_document": "Library Preparation Method",
            "atlas_version": "Atlas Version",
        },
    },
    "sequencing_method_step": {
        "CG002 - Cluster Generation (HiSeq X)": {
            "method_number": "Method",
            "method_version": "Version",
        },
        "CG002 - Cluster Generation (Illumina SBS)": {
            "method_number": "Method Document 1",
            "method_version": "Document 1 Version",
        },
        "Define Run Format and Calculate Volumes (Nova Seq)": {
            "method_number": "Method",
            "method_version": "Version",
            "atlas_document": "Sequencing Method",
            "atlas_version": "Atlas Version",
        },
        "Define Run Format and Calculate Volumes (NovaSeq X)": {
            "atlas_document": "Sequencing Method",
            "atlas_version": "Atlas Version",
        },
        "Set Up Sequencing Run (Revio) v1": {
            "atlas_document": "Sequencing Method",
            "atlas_version": "Atlas Version",
        },
    },
    "delivery_method_step": {
        "CG002 - Delivery": {
            "method_number": "Method Document",
            "method_version": "Method Version",
        },
        "Delivery v1": {
            "method_number": "Method Document",
            "method_document_2": "Method document 2",
            "method_version": "Method Version",
            "atlas_version": "Atlas Version",
        },
    },
}


class DocumentationMethod(StrEnum):
    ATLAS: str = "Atlas"
    AM: str = "AM"


class LimsArtifactTypes(StrEnum):
    ANALYTE: str = "Analyte"
    RESULT_FILE: str = "ResultFile"


class LimsProcess(StrEnum):
    COVID_POOLING_STEP: str = "Pooling and Clean-up (Cov) v1"
