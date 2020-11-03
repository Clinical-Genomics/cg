from typing import List
from pathlib import Path
import ruamel
from cg.apps.tb.models import TrailblazerAnalysis


def get_sample_data_from_config(config: dict) -> List[dict]:
    """Get sample data from config"""
    samples = []
    for sample_id, analysis_type in config["analysis_type"].items():
        samples.append({"id": sample_id, "type": analysis_type})
    return samples


def parse_config(data: dict) -> dict:
    """Parse MIP config file

    Args:
        data (dict): raw YAML input from MIP analysis config file

    Returns:
        dict: parsed data
    """
    return {
        "email": data.get("email"),
        "case": data.get("case_id") or data.get("family_id"),
        "samples": get_sample_data_from_config(config=data),
        "config_path": data.get("config_file_analysis"),
        "is_dryrun": "dry_run_all" in data,
        "log_path": data.get("log_file"),
        "out_dir": data.get("outdata_dir"),
        "priority": data.get("slurm_quality_of_service"),
        "sampleinfo_path": data.get("sample_info_file"),
    }


def parse_sampleinfo_light(data: dict) -> dict:
    """Parse MIP sample info file and retrieve mip_version, date, and status

    Args:
        data (dict): raw YAML input from MIP qc sample info file

    Returns:
        dict: {'version': str, 'date': str, 'is_finished': str}


    """

    outdata = {
        "date": data.get("analysis_date"),
        "version": data.get("mip_version"),
        "is_finished": data.get("analysisrunstatus") == "finished",
    }

    return outdata


def get_rank_model_version(sample_info: dict, rank_model_type: str, step: str) -> str:
    """Get rank model version"""
    for key in ("recipe", "program"):
        if key in sample_info:
            return sample_info[key][step][rank_model_type]["version"]


def get_genome_build(sample_info: dict) -> str:
    """Get genome build"""
    genome_build = sample_info["human_genome_build"]
    return f"{genome_build['source']}{genome_build['version']}"


def parse_sampleinfo(data: dict) -> dict:
    """Parse MIP sample info file.

    Args:
        data (dict): raw YAML input from MIP qc sample info file

    Returns:
        dict: parsed data
    """
    outdata = {
        "date": data.get("analysis_date"),
        "genome_build": get_genome_build(sample_info=data),
        "case": data.get("case_id") or data.get("family_id"),
        "is_finished": data.get("analysisrunstatus") == "finished",
        "rank_model_version": get_rank_model_version(
            sample_info=data, rank_model_type="rank_model", step="genmod"
        ),
        "samples": [{"id": sample_id} for sample_id in data["sample"].items()],
        "sv_rank_model_version": get_rank_model_version(
            sample_info=data, rank_model_type="sv_rank_model", step="sv_genmod"
        ),
        "version": data["mip_version"],
    }

    return outdata


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
    raw_data = ruamel.yaml.safe_load(Path(analysis_obj.config_path).open())
    data = parse_config(raw_data)
    return data["sampleinfo_path"]
