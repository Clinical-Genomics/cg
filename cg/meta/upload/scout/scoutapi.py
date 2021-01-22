"""File includes api to uploading data into Scout"""

import logging
from pathlib import Path
from typing import Optional

import requests
from housekeeper.store import models as hk_models
from ruamel import yaml

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.madeline.api import MadelineAPI
from cg.apps.scout.scout_load_config import (
    BalsamicLoadConfig,
    MipLoadConfig,
    ScoutBalsamicIndividual,
    ScoutIndividual,
    ScoutLoadConfig,
    ScoutMipIndividual,
)
from cg.apps.scout.scoutapi import ScoutAPI
from cg.constants import Pipeline
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.meta.workflow.mip import MipAnalysisAPI
from cg.store import models

from .files import BalsamicConfigBuilder, MipConfigBuilder, ScoutConfigBuilder

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

    def generate_config(
        self, analysis_obj: models.Analysis, rank_score_threshold: int = 5
    ) -> ScoutLoadConfig:
        """Fetch data about an analysis to load Scout."""
        LOG.info("Generate scout load config")

        # Fetch last version from housekeeper
        # This should be safe since analyses are only added if data is analysed
        hk_version_obj: hk_models.Version = self.housekeeper.last_version(
            analysis_obj.family.internal_id
        )
        LOG.debug("Found housekeeper version %s", hk_version_obj.id)

        load_config: ScoutLoadConfig
        track = "rare"
        LOG.info("Found pipeline %s", analysis_obj.pipeline)
        if analysis_obj.pipeline == Pipeline.BALSAMIC:
            config_builder = BalsamicConfigBuilder(hk_version_obj=hk_version_obj, analysis_obj=analysis_obj, lims_api=self.lims)
        

            load_config = self.generate_balsamic_config(
                analysis_obj=analysis_obj, hk_version_obj=hk_version_obj
            )
        else:
            load_config = self.generate_mip_config(
                analysis_obj=analysis_obj, hk_version_obj=hk_version_obj, rank_score_threshold=5
            )
        load_config.track = track

        return load_config

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
        tag_name: str = self.get_load_config_tag()
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
    def _is_family_case(load_config: MipLoadConfig) -> bool:
        """Check if there are any linked individuals in a case"""
        sample: ScoutMipIndividual
        for sample in load_config.samples:
            if sample.mother and sample.mother != "0":
                return True
            if sample.father and sample.father != "0":
                return True
        return False
