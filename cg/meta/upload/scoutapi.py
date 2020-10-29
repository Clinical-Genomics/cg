"""File includes api to uploading data into Scout"""

import logging
from pathlib import Path

import requests
from ruamel import yaml

from cg.apps.hk import HousekeeperAPI
from cg.apps.scoutapi import ScoutAPI
from cg.apps.lims import LimsAPI
from cg.apps.madeline.api import MadelineAPI
from cg.meta.workflow.mip import MipAnalysisAPI
from cg.store import models

LOG = logging.getLogger(__name__)


class UploadScoutAPI:
    """Class that handles everything that has to do with uploading to Scout"""

    def __init__(
        self,
        hk_api: HousekeeperAPI,
        scout_api: ScoutAPI,
        lims_api: LimsAPI,
        analysis_api: MipAnalysisAPI,
        madeline_api: MadelineAPI,
    ):
        self.housekeeper = hk_api
        self.scout = scout_api
        self.madeline_api = madeline_api
        self.analysis = analysis_api
        self.lims = lims_api

    def fetch_file_path(self, tag: str, sample_id: str, hk_version_id: int = None):
        """"Fetch files from housekeeper"""
        tags = [tag, sample_id]
        hk_file = self.housekeeper.files(version=hk_version_id, tags=tags).first()
        file_path = None
        if hk_file:
            file_path = hk_file.full_path
        return file_path

    def build_samples(self, analysis_obj: models.Analysis, hk_version_id: int = None):
        """Loop over the samples in an analysis and build dicts from them"""

        for link_obj in analysis_obj.family.links:
            sample_id = link_obj.sample.internal_id
            bam_path = self.fetch_file_path("bam", sample_id, hk_version_id)
            alignment_file_path = self.fetch_file_path("cram", sample_id, hk_version_id)
            chromograph_path = self.fetch_file_path("chromograph", sample_id, hk_version_id)
            mt_bam_path = self.fetch_file_path("bam-mt", sample_id, hk_version_id)
            vcf2cytosure_path = self.fetch_file_path("vcf2cytosure", sample_id, hk_version_id)

            lims_sample = dict()
            try:
                lims_sample = self.lims.sample(sample_id) or {}
            except requests.exceptions.HTTPError as ex:
                LOG.info("Could not fetch sample %s from LIMS: %s", sample_id, ex)
            sample = {
                "analysis_type": link_obj.sample.application_version.application.analysis_type,
                "bam_path": bam_path,
                "capture_kit": None,
                "alignment_path": alignment_file_path,
                "chromograph": chromograph_path,
                "father": link_obj.father.internal_id if link_obj.father else "0",
                "mother": link_obj.mother.internal_id if link_obj.mother else "0",
                "mt_bam": mt_bam_path,
                "phenotype": link_obj.status,
                "sample_id": sample_id,
                "sample_name": link_obj.sample.name,
                "sex": link_obj.sample.sex,
                "tissue_type": lims_sample.get("source", "unknown"),
                "vcf2cytosure": vcf2cytosure_path,
            }
            yield sample

    def generate_config(self, analysis_obj: models.Analysis) -> dict:
        """Fetch data about an analysis to load Scout."""
        analysis_date = analysis_obj.started_at or analysis_obj.completed_at
        hk_version = self.housekeeper.version(analysis_obj.family.internal_id, analysis_date)
        analysis_data = self.analysis.get_latest_metadata(analysis_obj.family.internal_id)
        data = {
            "analysis_date": analysis_obj.completed_at,
            "default_gene_panels": analysis_obj.family.panels,
            "family": analysis_obj.family.internal_id,
            "family_name": analysis_obj.family.name,
            "gene_panels": self.analysis.convert_panels(
                analysis_obj.family.customer.internal_id, analysis_obj.family.panels
            ),
            "human_genome_build": analysis_data.get("genome_build"),
            "owner": analysis_obj.family.customer.internal_id,
            "rank_model_version": analysis_data.get("rank_model_version"),
            "samples": list(),
            "sv_rank_model_version": analysis_data.get("sv_rank_model_version"),
        }
        for sample in self.build_samples(analysis_obj, hk_version.id):
            data["samples"].append(sample)

        self._include_mandatory_files(data, hk_version)
        self._include_peddy_files(data, hk_version)
        self._include_optional_files(data, hk_version)

        if self._is_multi_sample_case(data):
            if self._is_family_case(data):
                svg_path = self._run_madeline(analysis_obj.family)
                data["madeline"] = svg_path
            else:
                LOG.info("family of unconnected samples - skip pedigree graph")
        else:
            LOG.info("family of 1 sample - skip pedigree graph")

        return data

    @staticmethod
    def get_load_config_tag() -> str:
        """Get the hk tag for a scout load config"""
        return "scout-load-config"

    @staticmethod
    def save_config_file(upload_config: dict, file_path: Path):
        """Save a scout load config file to <file_path>"""

        LOG.info("Save Scout load config to %s", file_path)
        yml = yaml.YAML()
        yml.dump(upload_config, file_path)

    @staticmethod
    def add_scout_config_to_hk(config_file_path: Path, hk_api: HousekeeperAPI, case_id: str):
        """Add scout load config to hk bundle"""
        tag_name = UploadScoutAPI.get_load_config_tag()
        version_obj = hk_api.last_version(bundle=case_id)
        uploaded_config_files = hk_api.get_files(
            bundle=case_id, tags=[tag_name], version=version_obj.id
        )

        number_of_configs = sum(1 for i in uploaded_config_files)
        bundle_config_exists = number_of_configs > 0

        if bundle_config_exists:
            raise FileExistsError("Upload config already exists")

        file_obj = hk_api.add_file(str(config_file_path), version_obj, tag_name)
        hk_api.include_file(file_obj, version_obj)
        hk_api.add_commit(file_obj)

        LOG.info("Added scout load config to housekeeper: %s", config_file_path)
        return file_obj

    def _include_optional_files(self, data: dict, hk_version) -> None:
        """"Optional files on case level"""
        scout_hk_map = [
            ("delivery_report", "delivery-report"),
            ("multiqc", "multiqc-html"),
            ("vcf_str", "vcf-str"),
            ("smn_tsv", "smn-calling"),
        ]
        self._include_files(data, hk_version, scout_hk_map)

    def _include_peddy_files(self, data, hk_version):
        scout_hk_map = [
            ("peddy_ped", "ped"),
            ("peddy_sex", "sex-check"),
            ("peddy_check", "ped-check"),
        ]
        self._include_files(data, hk_version, scout_hk_map, extra_tag="peddy")

    def _include_mandatory_files(self, data, hk_version):
        scout_hk_map = {
            ("vcf_snv", "vcf-snv-clinical"),
            ("vcf_snv_research", "vcf-snv-research"),
            ("vcf_sv", "vcf-sv-clinical"),
            ("vcf_sv_research", "vcf-sv-research"),
        }
        self._include_files(data, hk_version, scout_hk_map, skip_missing=False)

    def _include_files(self, data, hk_version, scout_hk_map, **kwargs):
        extra_tag = kwargs.get("extra_tag")
        skip_missing = kwargs.get("skip_missing", True)
        for scout_key, hk_tag in scout_hk_map:

            if extra_tag:
                tags = [extra_tag, hk_tag]
            else:
                tags = [hk_tag]

            hk_file = self.housekeeper.files(version=hk_version.id, tags=tags).first()
            if hk_file:
                data[scout_key] = str(hk_file.full_path)
            else:
                if skip_missing:
                    LOG.debug("skipping missing file: %s", scout_key)
                else:
                    raise FileNotFoundError(f"missing file: {scout_key}")

    @staticmethod
    def _is_family_case(data: dict):
        """Check if there are any linked individuals in a case"""
        for sample in data["samples"]:
            if sample["mother"] and sample["mother"] != "0":
                return True
            if sample["father"] and sample["father"] != "0":
                return True
        return False

    @staticmethod
    def _is_multi_sample_case(data):
        return len(data["samples"]) > 1

    def _run_madeline(self, family_obj: models.Family):
        """Generate a madeline file for an analysis."""
        samples = [
            {
                "sample": link_obj.sample.name,
                "sex": link_obj.sample.sex,
                "father": link_obj.father.name if link_obj.father else None,
                "mother": link_obj.mother.name if link_obj.mother else None,
                "status": link_obj.status,
            }
            for link_obj in family_obj.links
        ]
        svg_path = self.madeline_api.run(family_id=family_obj.name, samples=samples)
        return svg_path
