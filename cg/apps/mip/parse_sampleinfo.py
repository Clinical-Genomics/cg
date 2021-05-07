"""MIP sample info file"""

import yaml

from cg.apps.tb.models import TrailblazerAnalysis
from cg.models.mip.mip_config import MipBaseConfig
from cg.models.mip.mip_sample_info import MipBaseSampleinfo


def parse_config(data: dict) -> MipBaseConfig:
    """Validate and parse MIP config file

    Args:
        data (dict): raw YAML input from MIP analysis config file

    Returns:
        dict: parsed data
    """
    return MipBaseConfig(**data)


def parse_sampleinfo(data: dict) -> MipBaseSampleinfo:
    """Parse MIP sample info file.

    Args:
        data (dict): raw YAML input from MIP qc sample info file

    Returns:
        dict: parsed data
    """
    return MipBaseSampleinfo(**data)


def parse_sampleinfo_rna(data: dict) -> dict:
    """Parse MIP sample info file (RNA).

    Args:
        data (dict): raw YAML input from MIP qc sample info file (RNA)

    Returns:
        dict: parsed data
    """
    case = data["case"]
    qcmetrics_parse = data["recipe"]["qccollect_ar"]

    outdata = {
        "date": data["analysis_date"],
        "is_finished": data["analysisrunstatus"] == "finished",
        "case": case,
        "config_file_path": data["config_file_analysis"],
        "version": data["mip_version"],
        "pedigree_path": data["pedigree_minimal"],
        "bcftools_merge": data["recipe"]["bcftools_merge"]["path"],
        "multiqc_html": data["recipe"]["multiqc"][f"{case}_html"]["path"],
        "multiqc_json": data["recipe"]["multiqc"][f"{case}_json"]["path"],
        "qcmetrics_path": qcmetrics_parse if not isinstance(qcmetrics_parse, dict) else None,
        "vep_path": data["recipe"]["varianteffectpredictor"]["path"],
        "version_collect_ar_path": data["recipe"]["version_collect_ar"]["path"],
        "samples": [],
    }

    for sample_id, sample_data in data["sample"].items():

        sample = {
            "id": sample_id,
            "bam": sample_data["most_complete_bam"]["path"],
            "star_fusion": sample_data["recipe"]["star_fusion"]["path"],
            "bootstrap_vcf": get_multiple_paths(sample_data, "bootstrapann"),
            "gatk_asereadcounter": get_multiple_paths(sample_data, "gatk_asereadcounter"),
            "gatk_baserecalibration": get_multiple_paths(sample_data, "gatk_baserecalibration"),
            "gffcompare_ar": get_multiple_paths(sample_data, "gffcompare_ar"),
            "mark_duplicates": get_multiple_paths(sample_data, "markduplicates"),
            "salmon_quant": get_multiple_paths(sample_data, "salmon_quant"),
            "stringtie_ar": get_multiple_paths(sample_data, "stringtie_ar"),
        }

        outdata["samples"].append(sample)

    return outdata


def get_multiple_paths(sample_data: dict, path_key: str) -> list:
    """Get all paths to files of a given type. Use this method if the exact filename is not
    known beforehand.
    Args:
        sample_data (dict): YAML file containing qc sample info
        path_key (str)    : Type of file paths to retrieve

    Returns:
        list: paths to all files of given type
    """
    paths = [file_data["path"] for file_data in sample_data["recipe"][path_key].values()]

    return paths


def get_sampleinfo(analysis_obj: TrailblazerAnalysis) -> str:
    """Get the sample info path for an analysis."""
    with open(analysis_obj.config_path, "r") as config_handle:
        raw_data = yaml.full_load(config_handle)
    data = parse_config(raw_data)
    return data["sampleinfo_path"]


def get_is_finished(sampleinfo: dict) -> bool:
    """Return true if analysis is finished"""
    if sampleinfo["is_finished"]:
        return True
    return False


def parse_qc_sample_info_file(sampleinfo_raw: dict) -> dict:
    return parse_sampleinfo(sampleinfo_raw)
