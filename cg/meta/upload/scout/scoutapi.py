"""File includes api to uploading data into Scout"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

import requests
from housekeeper.store import models as hk_models
from ruamel import yaml

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.madeline.api import MadelineAPI
from cg.apps.scout.scout_load_config import ScoutIndividual, ScoutLoadConfig
from cg.apps.scout.scoutapi import ScoutAPI
from cg.constants import Pipeline
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.meta.workflow.mip import MipAnalysisAPI
from cg.store import models

from .files import BalsamicFileHandler, MipFileHandler, ScoutFileHandler

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
        self.mip_analysis_api = analysis_api
        self.lims = lims_api

    def build_sample(
        self,
        sample_obj: models.FamilySample,
        file_handler: ScoutFileHandler,
        sample_name: Optional[str] = None,
    ) -> ScoutIndividual:
        """Build the base of a sample that is common for different analysis types"""
        sample_id: str = sample_obj.sample.internal_id
        LOG.info("Building sample %s", sample_id)
        lims_sample = dict()
        try:
            lims_sample = self.lims.sample(sample_id) or {}
        except requests.exceptions.HTTPError as ex:
            LOG.info("Could not fetch sample %s from LIMS: %s", sample_id, ex)

        sample_data = ScoutIndividual(
            sample_id=sample_id,
            sex=sample_obj.sample.sex,
            phenotype=sample_obj.status,
            analysis_type=sample_obj.sample.application_version.application.analysis_type,
            sample_name=sample_name or sample_obj.sample.name,
            tissue_type=lims_sample.get("source", "unknown"),
        )
        file_handler.include_sample_alignment_file(sample=sample_data)
        file_handler.include_sample_files()

        return sample_data

    def build_mip_sample(
        self, sample_obj: models.FamilySample, file_handler: MipFileHandler
    ) -> ScoutIndividual:
        """Build a sample with mip specific information"""

        sample_data: ScoutIndividual = self.build_sample(
            sample_obj=sample_obj, file_handler=file_handler
        )
        sample_data.father = sample_obj.father.internal_id if sample_obj.father else "0"
        sample_data.mother = sample_obj.mother.internal_id if sample_obj.mother else "0"

        return sample_data

    def build_balsamic_sample(
        self, sample_obj: models.FamilySample, file_handler: BalsamicFileHandler
    ) -> ScoutIndividual:
        """Build a sample with mip specific information"""

        # This will be tumor or normal
        sample_name: str = BalsamicAnalysisAPI.get_sample_type(sample_obj)
        sample_data: ScoutIndividual = self.build_sample(
            sample_obj=sample_obj, file_handler=file_handler, sample_name=sample_name
        )
        return sample_data

    @staticmethod
    def get_config_case(analysis_obj: models.Analysis) -> ScoutLoadConfig:
        """Create a base for scout load config based on all information available in an analysis object"""
        case_data = ScoutLoadConfig(
            analysis_date=analysis_obj.completed_at,
            default_gene_panels=analysis_obj.family.panels,
            family=analysis_obj.family.internal_id,
            family_name=analysis_obj.family.name,
            owner=analysis_obj.family.customer.internal_id,
            samples=list(),
        )
        return case_data

    def generate_mip_config(
        self,
        hk_version_obj: hk_models.Version,
        analysis_obj: models.Analysis,
        rank_score_threshold: int,
    ) -> dict:
        LOG.info("Generate load config for mip case")
        file_handler: MipFileHandler(hk_version_obj=hk_version_obj)
        config_data: ScoutLoadConfig = self.get_config_case(analysis_obj)

        analysis_data: dict = self.mip_analysis_api.get_latest_metadata(
            analysis_obj.family.internal_id
        )
        config_data.human_genome_build = (
            "38" if "38" in analysis_data.get("genome_build", "") else "37"
        )
        config_data.rank_score_threshold = rank_score_threshold
        config_data.rank_model_version = analysis_data.get("rank_model_version")
        config_data.sv_rank_model_version = analysis_data.get("sv_rank_model_version")

        config_data.gene_panels = (
            self.mip_analysis_api.convert_panels(
                analysis_obj.family.customer.internal_id, analysis_obj.family.panels
            )
            or None
        )
        LOG.debug("Including the mip specific vcf files")

        LOG.debug("Including optional mip files")
        include_files(
            data=config_data,
            hk_version_obj=hk_version_obj,
            hk_tag_map=CASE_TAG_MAP["optional_mip_to_tag"],
            skip_missing=True,
        )

        if self._is_multi_sample_case(config_data):
            if self._is_family_case(config_data):
                svg_path: Path = self._run_madeline(analysis_obj.family)
                config_data["madeline"] = str(svg_path)
            else:
                LOG.info("family of unconnected samples - skip pedigree graph")
        else:
            LOG.info("family of 1 sample - skip pedigree graph")

        LOG.info("Building samples")
        sample: models.FamilySample
        config_data["samples"] = [
            self.build_mip_sample(sample_obj=sample, hk_version_obj=hk_version_obj)
            for sample in analysis_obj.family.links
        ]

        return config_data

    def generate_balsamic_config(
        self, analysis_obj: models.Analysis, hk_version_obj: hk_models.Version
    ) -> dict:
        LOG.info("Generate load config for balsamic case")
        config_data: dict = self.get_config_case(analysis_obj)
        config_data["human_genome_build"] = "37"
        config_data["rank_score_threshold"] = 0

        LOG.debug("Including the balsamic specific vcf files")
        include_files(
            data=config_data,
            hk_version_obj=hk_version_obj,
            hk_tag_map=CASE_TAG_MAP["cancer_vcf_to_tag"],
        )

        LOG.debug("Including optional balsamic files")
        include_files(
            data=config_data,
            hk_version_obj=hk_version_obj,
            hk_tag_map=CASE_TAG_MAP["optional_balsamic_to_tag"],
            skip_missing=True,
        )
        LOG.info("Building samples")
        sample: models.FamilySample
        config_data["samples"] = [
            self.build_balsamic_sample(sample_obj=sample, hk_version_obj=hk_version_obj)
            for sample in analysis_obj.family.links
        ]

        return config_data

    def generate_config(
        self, analysis_obj: models.Analysis, rank_score_threshold: int = 5
    ) -> ScoutLoadConfig:
        """Fetch data about an analysis to load Scout."""
        LOG.info("Generate scout load config")

        # Fetch last version from housekeeper
        # This should be safe since analyses are only added if data is analysed
        hk_version: hk_models.Version = self.housekeeper.last_version(
            analysis_obj.family.internal_id
        )
        LOG.debug("Found housekeeper version %s", hk_version.id)

        case_data: dict
        analysis_type = "rare"
        if analysis_obj.pipeline == Pipeline.BALSAMIC:
            analysis_type = "cancer"
            case_data = self.generate_balsamic_config(
                analysis_obj=analysis_obj, hk_version_obj=hk_version
            )
        else:
            case_data = self.generate_mip_config(
                analysis_obj=analysis_obj, hk_version_obj=hk_version, rank_score_threshold=5
            )

        samples: Iterable[dict] = self.build_samples(
            analysis_obj=analysis_obj, hk_version_object=hk_version, analysis_type=analysis_type
        )
        for sample in samples:
            case_data["samples"].append(sample)

        # Validate that the config is correct
        scout_case = ScoutLoadConfig(**case_data)

        return scout_case

    @staticmethod
    def get_load_config_tag() -> str:
        """Get the hk tag for a scout load config"""
        return "scout-load-config"

    @staticmethod
    def save_config_file(upload_config: ScoutLoadConfig, file_path: Path) -> None:
        """Save a scout load config file to <file_path>"""

        LOG.info("Save Scout load config to %s", file_path)
        yml = yaml.YAML()
        yml.dump(upload_config.dict(exclude_none=True), file_path)

    def add_scout_config_to_hk(
        self, config_file_path: Path, case_id: str, delete: bool = False
    ) -> hk_models.File:
        """Add scout load config to hk bundle"""
        LOG.info("Adding load config to housekeeper")
        tag_name: str = UploadScoutAPI.get_load_config_tag()
        version_obj: hk_models.Version = self.housekeeper.last_version(bundle=case_id)
        uploaded_config_file: Optional[hk_models.File] = self.housekeeper.fetch_file_from_version(
            version_obj=version_obj, tags={tag_name}
        )
        if uploaded_config_file:
            LOG.info("Found config file: %s", uploaded_config_file)
            if delete is False:
                raise FileExistsError("Upload config already exists")
            self.housekeeper.delete_file(uploaded_config_file.id)

        file_obj: hk_models.File = self.housekeeper.add_file(
            path=str(config_file_path), version_obj=version_obj, tags=tag_name
        )
        self.housekeeper.include_file(file_obj=file_obj, version_obj=version_obj)
        self.housekeeper.add_commit(file_obj)

        LOG.info("Added scout load config to housekeeper: %s", config_file_path)
        return file_obj

    @staticmethod
    def _is_family_case(data: dict) -> bool:
        """Check if there are any linked individuals in a case"""
        for sample in data["samples"]:
            if sample["mother"] and sample["mother"] != "0":
                return True
            if sample["father"] and sample["father"] != "0":
                return True
        return False

    @staticmethod
    def _is_multi_sample_case(data) -> bool:
        return len(data["samples"]) > 1

    def _run_madeline(self, family_obj: models.Family) -> Path:
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
        svg_path: Path = self.madeline_api.run(family_id=family_obj.name, samples=samples)
        return svg_path
