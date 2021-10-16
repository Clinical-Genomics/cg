"""File includes api to uploading data into Scout"""

import logging
from pathlib import Path
from typing import Optional

import yaml
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.madeline.api import MadelineAPI
from cg.apps.scout.scoutapi import ScoutAPI
from cg.constants import Pipeline
from cg.meta.workflow.analysis import AnalysisAPI
from cg.models.scout.scout_load_config import ScoutLoadConfig
from cg.store import models, Store
from housekeeper.store import models as hk_models

from .balsamic_config_builder import BalsamicConfigBuilder
from .mip_config_builder import MipConfigBuilder

LOG = logging.getLogger(__name__)


class UploadScoutAPI:
    """Class that handles everything that has to do with uploading to Scout"""

    def __init__(
        self,
        hk_api: HousekeeperAPI,
        scout_api: ScoutAPI,
        lims_api: LimsAPI,
        analysis_api: AnalysisAPI,
        madeline_api: MadelineAPI,
    ):
        self.housekeeper = hk_api
        self.scout = scout_api
        self.madeline_api = madeline_api
        self.mip_analysis_api = analysis_api
        self.lims = lims_api

    def generate_config(self, analysis_obj: models.Analysis) -> ScoutLoadConfig:
        """Fetch data about an analysis to load Scout."""
        LOG.info("Generate scout load config")

        # Fetch last version from housekeeper
        # This should be safe since analyses are only added if data is analysed
        hk_version_obj: hk_models.Version = self.housekeeper.last_version(
            analysis_obj.family.internal_id
        )
        LOG.debug("Found housekeeper version %s", hk_version_obj.id)

        load_config: ScoutLoadConfig
        LOG.info("Found pipeline %s", analysis_obj.pipeline)
        if analysis_obj.pipeline == Pipeline.BALSAMIC:
            config_builder = BalsamicConfigBuilder(
                hk_version_obj=hk_version_obj, analysis_obj=analysis_obj, lims_api=self.lims
            )
        else:
            config_builder = MipConfigBuilder(
                hk_version_obj=hk_version_obj,
                analysis_obj=analysis_obj,
                mip_analysis_api=self.mip_analysis_api,
                lims_api=self.lims,
                madeline_api=self.madeline_api,
            )
        config_builder.build_load_config()

        return config_builder.load_config

    @staticmethod
    def get_load_config_tag() -> str:
        """Get the hk tag for a scout load config"""
        return "scout-load-config"

    @staticmethod
    def save_config_file(upload_config: ScoutLoadConfig, file_path: Path) -> None:
        """Save a scout load config file to <file_path>"""

        LOG.info("Save Scout load config to %s", file_path)
        yaml.dump(upload_config.dict(exclude_none=True), file_path.open("w"))

    def add_scout_config_to_hk(
        self, config_file_path: Path, case_id: str, delete: bool = False
    ) -> hk_models.File:
        """Add scout load config to hk bundle"""
        LOG.info("Adding load config %s to housekeeper", config_file_path)
        tag_name: str = self.get_load_config_tag()
        version_obj: hk_models.Version = self.housekeeper.last_version(bundle=case_id)
        uploaded_config_file: Optional[hk_models.File] = self.housekeeper.fetch_file_from_version(
            version_obj=version_obj, tags={tag_name}
        )
        if uploaded_config_file:
            LOG.info("Found config file: %s", uploaded_config_file)
            if not delete:
                raise FileExistsError("Upload config already exists")
            self.housekeeper.delete_file(uploaded_config_file.id)

        file_obj: hk_models.File = self.housekeeper.add_file(
            path=str(config_file_path), version_obj=version_obj, tags=tag_name
        )
        self.housekeeper.include_file(file_obj=file_obj, version_obj=version_obj)
        self.housekeeper.add_commit(file_obj)

        LOG.info("Added scout load config to housekeeper: %s", config_file_path)
        return file_obj

    def get_fusion_report(self, case_id: str, research: bool) -> Optional[hk_models.File]:
        """Get a fusion report for case in housekeeper

        Args:
            case_id     (string):       Case identifier
            research    (bool):         Research report
        Returns:
            File in housekeeper (Optional[hk_models.File])
        """

        # This command can be executed as:
        # ´housekeeper get file -V --tag fusion --tag pdf --tag clinical/research <case_id>´
        tags = ["fusion"]
        if research:
            tags.append("research")
        else:
            tags.append("clinical")

        version_obj = self.housekeeper.last_version(case_id)
        fusion_report: Optional[hk_models.File] = self.housekeeper.fetch_file_from_version(
            version_obj=version_obj, tags=tags
        )

        return fusion_report

    def get_splice_junctions_bed(self, sample_id) -> Optional[hk_models.File]:
        """Get a splice junctions bed file for case in housekeeper

        Args:
            sample_id   (string):       Sample identifier
            research    (bool):         Research report
        Returns:
            File in housekeeper (Optional[hk_models.File])
        """

        # This command can be executed as:
        # ´housekeeper get file -V --tag junction --tag bed <sample_id>´
        tags = ["junction", "bed"]

        version_obj = self.housekeeper.last_version(sample_id)
        splice_junctions_bed: Optional[hk_models.File] = self.housekeeper.fetch_file_from_version(
            version_obj=version_obj, tags=tags
        )

        return splice_junctions_bed

    def get_rna_coverage_bigwig(self, sample_id) -> Optional[hk_models.File]:
        """Get a rna coverage bigwig file for case in housekeeper

        Args:
            sample_id   (string):       Sample identifier
            research    (bool):         Research report
        Returns:
            File in housekeeper (Optional[hk_models.File])
        """

        # This command can be executed as:
        # ´housekeeper get file -V --tag coverage --tag bigwig <sample_id>´
        tags = ["coverage", "bigwig"]

        version_obj = self.housekeeper.last_version(sample_id)
        rna_coverage_bigwig: Optional[hk_models.File] = self.housekeeper.fetch_file_from_version(
            version_obj=version_obj, tags=tags
        )

        return rna_coverage_bigwig

    def upload_rna_coverage_bigwig_to_scout(self, case_id: str, dry_run: bool) -> None:
        """Upload rna_coverage_bigwig file for a case to Scout.
            This command can be executed as:
            `housekeeper get file -V --tag coverage --tag bigwig <sample_id>;`
            `scout update individual -c <case_id> -n <customer_sample_id> rna_coverage_bigwig
            <path/to/coverage_file.bigWig>;`

        Args:
            dry_run     (bool):         Skip uploading
            case_id     (string):       Case identifier
        Returns:
            Nothing
        """
        scout_api: ScoutAPI = self.scout_api
        status_db: Store = self.status_db
        case_obj = status_db.family(case_id)

        for link in case_obj.links:
            sample_obj = link.sample
            sample_id = sample_obj.internal_id
            sample_name = sample_obj.name
            rna_coverage_bigwig: Optional[hk_models.File] = self.get_rna_coverage_bigwig(sample_id)

            if rna_coverage_bigwig is None:
                raise FileNotFoundError(
                    f"No rna coverage bigwig file was found in housekeeper for {sample_id}"
                )

            LOG.info("Uploading rna coverage bigwig file %s to scout", sample_id)

            if not dry_run:
                scout_api.upload_rna_coverage_bigwig(
                    file_path=rna_coverage_bigwig.full_path,
                    case_id=case_id,
                    customer_sample_id=sample_name,
                )

        LOG.info("Uploaded rna coverage bigwig %s", rna_coverage_bigwig.full_path)
        LOG.info("Rna coverage bigwig uploaded successfully to Scout")

    def upload_fusion_report_to_scout(self, dry_run: bool, research: bool, case_id: str) -> None:
        """Upload fusion report file for a case to Scout.
        This can also be run as
        `housekeeper get file -V --tag fusion --tag pdf --tag clinical/research <case_id>`
        `scout load gene-fusion-report [-r] <case_id> <path/to/research_gene_fusion_report.pdf>`

        Args:
            dry_run     (bool):         Skip uploading
            case_id     (string):       Case identifier
            research    (bool):         Upload research report instead of clinical
        Returns:
            Nothing
        """

        scout_api: ScoutAPI = self.scout_api
        fusion_report: Optional[hk_models.File] = self.get_fusion_report(case_id, research)

        if fusion_report is None:
            raise FileNotFoundError(f"No fusion report was found in housekeeper for {case_id}")

        LOG.info("uploading fusion report %s to scout", case_id)

        if not dry_run:
            scout_api.upload_fusion_report(
                report_path=fusion_report.full_path, research=research, case_id=case_id
            )

        LOG.info("Uploaded fusion report %s", fusion_report.full_path)
        LOG.info("Fusion report uploaded successfully to Scout")

    def upload_splice_junctions_bed_to_scout(self, dry_run: bool, case_id: str) -> None:
        """Upload splice_junctions_bed file for a case to Scout.
            This command can be executed as:
            `housekeeper get file -V --tag junction --tag bed <sample_id>;`
            `scout update individual -c <case_id> -n <customer_sample_id> splice_junctions_bed <path/to/junction_file.bed>;`


        Args:
            dry_run     (bool):         Skip uploading
            case_id     (string):       Case identifier
        Returns:
            Nothing
        """

        scout_api: ScoutAPI = self.scout_api
        status_db: Store = self.status_db
        case_obj = status_db.family(case_id)

        for link in case_obj.links:
            sample_obj = link.sample
            sample_id = sample_obj.internal_id
            sample_name = sample_obj.name
            splice_junctions_bed: Optional[hk_models.File] = self.get_splice_junctions_bed(
                sample_id
            )

            if splice_junctions_bed is None:
                raise FileNotFoundError(
                    f"No splice junctions bed file was found in housekeeper for {sample_id}"
                )

            LOG.info("Uploading splice junctions bed file %s to scout", sample_id)

            if not dry_run:
                scout_api.upload_splice_junctions_bed(
                    file_path=splice_junctions_bed.full_path,
                    case_id=case_id,
                    customer_sample_id=sample_name,
                )

        LOG.info("Uploaded splice junctions bed file %s", splice_junctions_bed.full_path)
        LOG.info("Splice junctions bed uploaded successfully to Scout")
