"""Test get MIP files"""

from pathlib import Path

from cg.apps.tb.add import AddHandler


def test_get_files(files_data) -> dict:
    """
    Args:
    files_raw (dict): With dicts from files
    """
    # GIVEN config data of a "sharp" run (not dry run)
    mip_config = files_data["config"]

    # GIVEN sampleinfo input from a finished analysis
    sampleinfo = files_data["sampleinfo"]

    mip_file_data = AddHandler._get_files(mip_config, sampleinfo)

    # Define test data
    mip_file_test_data = {
        "mip-config": {"path": mip_config["config_path"]},
        "sampleinfo": {"path": mip_config["sampleinfo_path"]},
        "multiqc_html": {"path": sampleinfo["multiqc_html"]},
        "multiqc_json": {"path": sampleinfo["multiqc_json"]},
        "pedigree_yaml": {"path": sampleinfo["pedigree"]},
        "pedigree": {"path": sampleinfo["pedigree_path"]},
        "mip-log": {"path": mip_config["log_path"]},
        "qcmetrics": {"path": sampleinfo["qcmetrics_path"]},
        "snv-gbcf": {"path": sampleinfo["snv"]["bcf"]},
        "snv-gbcf-index": {"path": f"{sampleinfo['snv']['bcf']}.csi"},
        "snv-bcf": {"path": sampleinfo["snv"]["bcf"]},
        "snv-bcf-index": {"path": f"{sampleinfo['snv']['bcf']}.csi"},
        "sv-bcf": {"path": sampleinfo["sv"]["bcf"]},
        "sv-bcf-index": {"path": f"{sampleinfo['sv']['bcf']}.csi"},
        "ped-check": {"path": sampleinfo["peddy"]["ped_check"]},
        "ped": {"path": sampleinfo["peddy"]["ped"]},
        "sex-check": {"path": sampleinfo["peddy"]["sex_check"]},
        "vcf-snv-clinical": {"path": sampleinfo["snv"]["clinical_vcf"]},
        "vcf-snv-clinical-index": {"path": f"{sampleinfo['snv']['clinical_vcf']}.tbi"},
        "vcf-sv-clinical": {"path": sampleinfo["sv"]["clinical_vcf"]},
        "vcf-sv-clinical-index": {"path": f"{sampleinfo['sv']['clinical_vcf']}.csi"},
        "vcf-snv-research": {"path": sampleinfo["snv"]["research_vcf"]},
        "vcf-snv-research-index": {"path": f"{sampleinfo['snv']['research_vcf']}.tbi"},
        "vcf-sv-research": {"path": sampleinfo["sv"]["research_vcf"]},
        "vcf-sv-research-index": {"path": f"{sampleinfo['sv']['research_vcf']}.csi"},
        "vcf-str": {"path": sampleinfo["str_vcf"]},
        "executables_version": {"path": sampleinfo["version_collect"]},
    }

    # Check returns from def
    # Case data
    for tag_id in mip_file_test_data:
        # For every file tag
        for key, value in mip_file_test_data[tag_id].items():
            # For each element
            for element_data in mip_file_data:
                # If file tag exists in the return data tags
                if tag_id in element_data["tags"]:
                    assert value in element_data[key]

    mip_file_test_sample_data = {}

    # Define sample test data
    for sample_data in sampleinfo["samples"]:

        # Cram pre-processing
        cram_path = sample_data["cram"]
        crai_path = f"{cram_path}.crai"
        if not Path(crai_path).exists():
            crai_path = cram_path.replace(".cram", ".crai")
        mip_file_test_sample_data[sample_data["id"]] = {
            "cram": cram_path,
            "cram-index": crai_path,
            "coverage": sample_data["sambamba"],
            "chromograph": sample_data["chromograph"],
            "vcf2cytosure": sample_data["vcf2cytosure"],
        }

        # Only wgs data
        # Downsamples MT bam
        if sample_data["subsample_mt"]:
            mt_bam_path = sample_data["subsample_mt"]
            mt_bai_path = f"{mt_bam_path}.bai"
            if not Path(mt_bai_path).exists():
                mt_bai_path = mt_bam_path.replace(".bam", ".bai")
            mip_file_test_sample_data[sample_data["id"]]["bam-mt"] = mt_bam_path
            mip_file_test_sample_data[sample_data["id"]]["bam-mt-index"] = mt_bai_path

    # Check returns from def
    # Sample data
    for sample_id in mip_file_test_sample_data:
        for key, value in mip_file_test_sample_data[sample_id].items():
            for element_data in mip_file_data:
                # If file tag exists in the return data tags
                if all(k in element_data["tags"] for k in (sample_id, key)):
                    assert value in element_data["path"]


def test_rna_analysis_true(files_raw):
    """
    Args:
    files_raw (dict): With dicts from files
    """
    # GIVEN an raw sample info file
    rna_sampleinfo = files_raw["rna_sampleinfo"]

    # WHEN the analysis type is 'wts'
    rna_sampleinfo["analysis_type"]["sample_id_1"] = "wts"
    rna_analysis = AddHandler._is_rna_analysis(rna_sampleinfo)

    # THEN then function should return TRUE
    assert rna_analysis


def test_rna_analysis_false(files_raw):
    """
    Args:
    files_raw (dict): With dicts from files
    """
    # GIVEN an raw sample info file with one sample
    rna_sampleinfo = files_raw["rna_sampleinfo"]

    # WHEN the analysis type is 'wgs'
    rna_sampleinfo["analysis_type"]["sample_id_1"] = "wgs"
    rna_analysis = AddHandler._is_rna_analysis(rna_sampleinfo)

    # THEN then function should return FALSE
    assert not rna_analysis


def test_rna_analysis_multiple_all_true(files_raw):
    """
    Args:
    files_raw (dict): With dicts from files
    """
    # GIVEN an raw sample info file with more than one sample
    rna_sampleinfo = files_raw["rna_sampleinfo"]

    # WHEN the analysis type is 'wts' for all samples
    rna_sampleinfo["analysis_type"]["sample_id_1"] = "wts"
    rna_sampleinfo["analysis_type"]["sample_id_2"] = "wts"
    rna_sampleinfo["analysis_type"]["sample_id_3"] = "wts"
    rna_analysis = AddHandler._is_rna_analysis(rna_sampleinfo)

    # THEN then function should return TRUE
    assert rna_analysis


def test_rna_analysis_multiple_all_false(files_raw):
    """
    Args:
    files_raw (dict): With dicts from files
    """
    # GIVEN an raw sample info file with more than one sample
    rna_sampleinfo = files_raw["rna_sampleinfo"]

    # WHEN the analysis type is 'wgs' for all samples
    rna_sampleinfo["analysis_type"]["sample_id_1"] = "wgs"
    rna_sampleinfo["analysis_type"]["sample_id_2"] = "wgs"
    rna_sampleinfo["analysis_type"]["sample_id_3"] = "wgs"
    rna_analysis = AddHandler._is_rna_analysis(rna_sampleinfo)

    # THEN then function should return FALSE
    assert not rna_analysis


def test_rna_analysis_multiple_some_true(files_raw):
    """
    Args:
    files_raw (dict): With dicts from files
    """
    # GIVEN an raw sample info file with more than one sample
    rna_sampleinfo = files_raw["rna_sampleinfo"]

    # WHEN the analysis type is not 'wts' for all samples, but only some
    rna_sampleinfo["analysis_type"]["sample_id_1"] = "wts"
    rna_sampleinfo["analysis_type"]["sample_id_2"] = "wts"
    rna_sampleinfo["analysis_type"]["sample_id_3"] = "wgs"
    rna_analysis = AddHandler._is_rna_analysis(rna_sampleinfo)

    # THEN then function should return FALSE
    assert not rna_analysis
