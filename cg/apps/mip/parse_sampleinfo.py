from typing import Dict, List, Literal

from pydantic import BaseModel, EmailStr, parse_obj_as
import yaml
from cg.apps.tb.models import TrailblazerAnalysis


class MipBaseConfig(BaseModel):
    """This model is used when validating the mip analysis config"""

    analysis_type: Dict[str, str]
    case_id: str = None
    config_file_analysis: str
    email: EmailStr
    family_id: str = None
    dry_run_all: bool
    log_file: str
    outdata_dir: str
    slurm_quality_of_service: Literal["low", "normal", "high"]
    sample_info_file: str


class MipBaseSampleinfo(BaseModel):
    """This model is used when validating the mip samplinfo file"""

    analysisrunstatus: str
    analysis_date: str
    case_id: str
    family_id: str = None
    human_genome_build: dict
    mip_version: str
    program: dict = None
    recipe: dict = None


def get_sample_data_from_config(config: MipBaseConfig) -> List[dict]:
    """Get sample data from config"""
    samples = []
    for sample_id, analysis_type in config.analysis_type.items():
        samples.append({"id": sample_id, "type": analysis_type})
    return samples


def parse_config(data: dict) -> dict:
    """Validate and parse MIP config file

    Args:
        data (dict): raw YAML input from MIP analysis config file

    Returns:
        dict: parsed data
    """
    mip_config = parse_obj_as(MipBaseConfig, data)
    return {
        "email": mip_config.email,
        "case": mip_config.case_id or mip_config.family_id,
        "samples": get_sample_data_from_config(config=mip_config),
        "config_path": mip_config.config_file_analysis,
        "is_dryrun": mip_config.dry_run_all,
        "log_path": mip_config.log_file,
        "out_dir": mip_config.outdata_dir,
        "priority": mip_config.slurm_quality_of_service,
        "sampleinfo_path": mip_config.sample_info_file,
    }


def get_rank_model_version(sample_info: MipBaseSampleinfo, rank_model_type: str, step: str) -> str:
    """Get rank model version"""
    if sample_info.recipe:
        return sample_info.recipe[step][rank_model_type]["version"]
    if sample_info.program:
        return sample_info.program[step][rank_model_type]["version"]


def get_genome_build(sample_info: MipBaseSampleinfo) -> str:
    """Get genome build"""
    version = sample_info.human_genome_build["version"]
    source = sample_info.human_genome_build["source"]
    return f"{source}{version}"


def parse_sampleinfo(data: dict) -> dict:
    """Parse MIP sample info file.

    Args:
        data (dict): raw YAML input from MIP qc sample info file

    Returns:
        dict: parsed data
    """
    mip_sampleinfo = parse_obj_as(MipBaseSampleinfo, data)
    outdata = {
        "date": mip_sampleinfo.analysis_date,
        "genome_build": get_genome_build(sample_info=mip_sampleinfo),
        "case": mip_sampleinfo.case_id or mip_sampleinfo.family_id,
        "is_finished": mip_sampleinfo.analysisrunstatus == "finished",
        "rank_model_version": get_rank_model_version(
            sample_info=mip_sampleinfo, rank_model_type="rank_model", step="genmod"
        ),
        "sv_rank_model_version": get_rank_model_version(
            sample_info=mip_sampleinfo, rank_model_type="sv_rank_model", step="sv_genmod"
        ),
        "version": mip_sampleinfo.mip_version,
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
