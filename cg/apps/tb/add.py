# -*- coding: utf-8 -*-
import logging
from pathlib import Path

import ruamel.yaml

from trailblazer.mip import files as mip_dna_files
from cg.apps.mip_rna import files as mip_rna_files
from cg.meta.store import mip_rna
from cg.exc import AnalysisNotFinishedError

LOG = logging.getLogger(__name__)


class AddHandler:
    @classmethod
    def add_analysis(cls, config_stream):
        """Gather information from MIP analysis to store."""
        config_raw = ruamel.yaml.safe_load(config_stream)
        config_data = mip_dna_files.parse_config(config_raw)
        sampleinfo_raw = ruamel.yaml.safe_load(Path(config_data["sampleinfo_path"]).open())
        rna_analysis = cls._is_rna_analysis(sampleinfo_raw)
        if rna_analysis:
            sampleinfo_data = mip_rna_files.parse_sampleinfo_rna(sampleinfo_raw)
        else:
            sampleinfo_data = mip_dna_files.parse_sampleinfo(sampleinfo_raw)

        if sampleinfo_data["is_finished"] is False:
            raise AnalysisNotFinishedError("analysis not finished")

        if rna_analysis:
            new_bundle = mip_rna.build_bundle_rna(config_data, sampleinfo_data)
        else:
            new_bundle = cls._build_bundle(config_data, sampleinfo_data)
        return new_bundle

    @classmethod
    def _build_bundle(cls, config_data: dict, sampleinfo_data: dict) -> dict:
        """Create a new bundle."""
        data = {
            "name": config_data["case"],
            "created": sampleinfo_data["date"],
            "pipeline_version": sampleinfo_data["version"],
            "files": cls._get_files(config_data, sampleinfo_data),
        }
        return data

    @staticmethod
    def _is_rna_analysis(sampleinfo_raw: dict) -> bool:
        """checks if all samples are RNA samples based on analysis type """
        return all([analysis == "wts" for analysis in sampleinfo_raw["analysis_type"].values()])

    @staticmethod
    def _get_files(config_data: dict, sampleinfo_data: dict) -> dict:
        """Get all the files from the MIP files."""

        data = [
            {"path": config_data["config_path"], "tags": ["mip-config"], "archive": True,},
            {"path": config_data["sampleinfo_path"], "tags": ["sampleinfo"], "archive": True,},
            {"path": sampleinfo_data["multiqc_html"], "tags": ["multiqc-html"], "archive": False,},
            {"path": sampleinfo_data["multiqc_json"], "tags": ["multiqc-json"], "archive": False,},
            {"path": sampleinfo_data["pedigree"], "tags": ["pedigree-yaml"], "archive": False,},
            {"path": sampleinfo_data["pedigree_path"], "tags": ["pedigree"], "archive": False,},
            {"path": config_data["log_path"], "tags": ["mip-log"], "archive": True},
            {"path": sampleinfo_data["qcmetrics_path"], "tags": ["qcmetrics"], "archive": True,},
            {
                "path": sampleinfo_data["snv"]["bcf"],
                "tags": ["snv-bcf", "snv-gbcf"],
                "archive": True,
            },
            {
                "path": f"{sampleinfo_data['snv']['bcf']}.csi",
                "tags": ["snv-bcf-index", "snv-gbcf-index"],
                "archive": True,
            },
            {"path": sampleinfo_data["sv"]["bcf"], "tags": ["sv-bcf"], "archive": True},
            {
                "path": f"{sampleinfo_data['sv']['bcf']}.csi",
                "tags": ["sv-bcf-index"],
                "archive": True,
            },
            {
                "path": sampleinfo_data["peddy"]["ped_check"],
                "tags": ["peddy", "ped-check"],
                "archive": False,
            },
            {"path": sampleinfo_data["peddy"]["ped"], "tags": ["peddy", "ped"], "archive": False,},
            {
                "path": sampleinfo_data["peddy"]["sex_check"],
                "tags": ["peddy", "sex-check"],
                "archive": False,
            },
            {"path": sampleinfo_data["version_collect"], "tags": ["exe-ver"], "archive": False,},
        ]

        # this key exists only for wgs
        if sampleinfo_data["str_vcf"]:
            data.append(
                {"path": sampleinfo_data["str_vcf"], "tags": ["vcf-str"], "archive": True,}
            )

        for variant_type in ["snv", "sv"]:
            for output_type in ["clinical", "research"]:
                vcf_path = sampleinfo_data[variant_type][f"{output_type}_vcf"]
                if vcf_path is None:
                    LOG.warning(f"missing file: {output_type} {variant_type} VCF")
                    continue
                vcf_tag = f"vcf-{variant_type}-{output_type}"
                data.append({"path": vcf_path, "tags": [vcf_tag], "archive": True})
                data.append(
                    {
                        "path": f"{vcf_path}.tbi" if variant_type == "snv" else f"{vcf_path}.csi",
                        "tags": [f"{vcf_tag}-index"],
                        "archive": True,
                    }
                )

        for sample_data in sampleinfo_data["samples"]:
            data.append(
                {
                    "path": sample_data["sambamba"],
                    "tags": ["coverage", sample_data["id"]],
                    "archive": False,
                }
            )

            # Cram pre-processing
            cram_path = sample_data["cram"]
            crai_path = f"{cram_path}.crai"
            if not Path(crai_path).exists():
                crai_path = cram_path.replace(".cram", ".crai")

            data.append(
                {"path": cram_path, "tags": ["cram", sample_data["id"]], "archive": False,}
            )
            data.append(
                {"path": crai_path, "tags": ["cram-index", sample_data["id"]], "archive": False,}
            )

            # Only for wgs data
            # Downsamples MT bam pre-processing
            if sample_data["subsample_mt"]:
                mt_bam_path = sample_data["subsample_mt"]
                mt_bai_path = f"{mt_bam_path}.bai"
                if not Path(mt_bai_path).exists():
                    mt_bai_path = mt_bam_path.replace(".bam", ".bai")
                data.append(
                    {"path": mt_bam_path, "tags": ["bam-mt", sample_data["id"]], "archive": False,}
                )
                data.append(
                    {
                        "path": mt_bai_path,
                        "tags": ["bam-mt-index", sample_data["id"]],
                        "archive": False,
                    }
                )
            # Only for wgs and trio data
            if sample_data["chromograph"]:
                chromograph_path = sample_data["chromograph"]
                data.append(
                    {
                        "path": chromograph_path,
                        "tags": ["chromograph", sample_data["id"]],
                        "archive": False,
                    }
                )

            cytosure_path = sample_data["vcf2cytosure"]
            data.append(
                {
                    "path": cytosure_path,
                    "tags": ["vcf2cytosure", sample_data["id"]],
                    "archive": False,
                }
            )

        return data
