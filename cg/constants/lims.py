PROP2UDF = {
    "application": "Sequencing Analysis",
    "bait_set": "Bait Set",
    "capture_kit": "Capture Library version",
    "comment": "Comment",
    "concentration": "Concentration (nM)",
    "concentration_weight": "Sample Conc.",
    "customer": "customer",
    "data_analysis": "Data Analysis",
    "elution_buffer": "Sample Buffer",
    "extraction_method": "Extraction method",
    "family_name": "familyID",
    "formalin_fixation_time": "Formalin Fixation Time",
    "index": "Index type",
    "index_number": "Index number",
    "organism": "Strain",
    "organism_other": "Other species",
    "pool": "pool name",
    "post_formalin_fixation_time": "Post Formalin Fixation Time",
    "priority": "priority",
    "quantity": "Quantity",
    "reference_genome": "Reference Genome Microbial",
    "require_qcok": "Process only if QC OK",
    "rml_plate_name": "RML plate name",
    "sex": "Gender",
    "source": "Source",
    "tissue_block_size": "Tissue Block Size",
    "target_reads": "Reads missing (M)",
    "tumour": "tumor",
    "tumour_purity": "tumour purity",
    "volume": "Volume (uL)",
    "well_position_rml": "RML well position",
    "verified_organism": "Verified organism",
}

MASTER_STEPS_UDFS = {
    "capture_kit_step": {
        "obsolete_CG002 - Hybridize Library  (SS XT)": "SureSelect capture library/libraries used",
        "Hybridize Library TWIST v1": "Bait Set",
        "Hybridize Library TWIST v2": "Bait Set",
    },
    "prep_method_step": {
        "CG002 - End repair Size selection A-tailing and Adapter ligation (TruSeq PCR-free DNA)": {
            "method_number": "Method document",
            "method_version": "Method document version",
        },
        "End repair Size selection A-tailing and Adapter ligation (TruSeq PCR-free DNA)": {
            "method_number": "Method document",
            "method_version": "Method document version",
        },
        "obsolete_CG002 - Hybridize Library  (SS XT)": {
            "method_number": "Method document",
            "method_version": "Method document versio",
        },
        "CG002 - Microbial Library Prep (Nextera)": {
            "method_number": "Method",
            "method_version": "Method Version",
        },
        "End-Repair and A-tailing TWIST v1": {
            "method_number": "Method document",
            "method_version": "Document version",
        },
        "KAPA Library Preparation TWIST v1": {
            "method_number": "Method document",
            "method_version": "Document version",
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
        },
    },
    "delivery_method_step": {
        "CG002 - Delivery": {
            "method_number": "Method Document",
            "method_version": "Method Version",
        },
        "Delivery v1": {"method_number": "Method Document", "method_version": "Method Version"},
    },
}

PROCESSES = {"sequenced_date": "AUTOMATED - NovaSeq Run"}
