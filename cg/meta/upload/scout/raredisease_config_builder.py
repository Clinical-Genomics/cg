import logging
import re
from pathlib import Path

from housekeeper.store.models import Version

from cg.apps.lims import LimsAPI
from cg.apps.madeline.api import MadelineAPI
from cg.constants.housekeeper_tags import HK_DELIVERY_REPORT_TAG
from cg.constants.scout import (
    GenomeBuild,
    RAREDISEASE_CASE_TAGS,
    RAREDISEASE_SAMPLE_TAGS,
    UploadTrack,
)
from cg.constants.subject import RelationshipStatus
from cg.meta.upload.scout.hk_tags import CaseTags, SampleTags
from cg.meta.upload.scout.scout_config_builder import ScoutConfigBuilder
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.models.scout.scout_load_config import (
    RarediseaseLoadConfig,
    ScoutIndividual,
    ScoutLoadConfig,
    ScoutRarediseaseIndividual,
)
from cg.store.models import Analysis, Case, CaseSample

LOG = logging.getLogger(__name__)


class RarediseaseConfigBuilder(ScoutConfigBuilder):
    def __init__(
        self,
        hk_version_obj: Version,
        analysis_obj: Analysis,
        raredisease_analysis_api: RarediseaseAnalysisAPI,
        lims_api: LimsAPI,
        madeline_api: MadelineAPI,
    ):
        super().__init__(
            hk_version_obj=hk_version_obj,
            analysis_obj=analysis_obj,
            lims_api=lims_api,
        )
        self.case_tags: CaseTags = CaseTags(**RAREDISEASE_CASE_TAGS)
        self.sample_tags: SampleTags = SampleTags(**RAREDISEASE_SAMPLE_TAGS)
        self.load_config: RarediseaseLoadConfig = RarediseaseLoadConfig(
            track=UploadTrack.RARE_DISEASE.value,
            delivery_report=self.get_file_from_hk({HK_DELIVERY_REPORT_TAG}),
        )
        self.raredisease_analysis_api: RarediseaseAnalysisAPI = raredisease_analysis_api
        self.lims_api: LimsAPI = lims_api
        self.madeline_api: MadelineAPI = madeline_api

    def build_load_config(self, rank_score_threshold: int = 5) -> None:
        """Create a RAREDISEASE specific load config for uploading analysis to Scout"""
        LOG.info("Build load config for RAREDISEASE case")
        self.add_common_info_to_load_config()
        self.load_config.human_genome_build = getattr(
            GenomeBuild,
            self.raredisease_analysis_api.get_genome_build(case_id=self.analysis_obj.case.internal_id),
        )
        # self.load_config.rank_score_threshold = rank_score_threshold
        # self.load_config.rank_model_version = raredisease_analysis_data.rank_model_version
        # self.load_config.sv_rank_model_version = raredisease_analysis_data.sv_rank_model_version

        self.load_config.gene_panels = (
            self.raredisease_analysis_api.get_aggregated_panels(
                customer_id=self.analysis_obj.case.customer.internal_id,
                default_panels=set(self.analysis_obj.case.panels),
            )
            or None
        )

        self.include_case_files()
        LOG.info("Building samples")
        db_sample: CaseSample
        for db_sample in self.analysis_obj.case.links:
            self.load_config.samples.append(self.build_config_sample(case_sample=db_sample))
        self.include_pedigree_picture()

    def include_pedigree_picture(self) -> None:
        if self.is_multi_sample_case(self.load_config):
            if self.is_family_case(self.load_config):
                svg_path: Path = self.run_madeline(self.analysis_obj.case)
                self.load_config.madeline = str(svg_path)
            else:
                LOG.info("family of unconnected samples - skip pedigree graph")
        else:
            LOG.info("family of 1 sample - skip pedigree graph")

    def build_config_sample(self, case_sample: CaseSample) -> ScoutRarediseaseIndividual:
        """Build a sample with specific information"""
        config_sample = ScoutRarediseaseIndividual()
        self.add_common_sample_info(config_sample=config_sample, case_sample=case_sample)
        self.include_sample_files(case_sample=case_sample, config_sample=config_sample)
        config_sample.father = (
            case_sample.father.internal_id
            if case_sample.father
            else RelationshipStatus.HAS_NO_PARENT
        )
        config_sample.mother = (
            case_sample.mother.internal_id
            if case_sample.mother
            else RelationshipStatus.HAS_NO_PARENT
        )
        return config_sample

    def include_case_files(self) -> None:
        """Include case level files for mip case"""
        LOG.info("Including RAREDISEASE specific case level files")
        for scout_key in RAREDISEASE_CASE_TAGS.keys():
            LOG.info(f"Scout key: {scout_key}")
            self._include_case_file(scout_key)

    def include_sample_files(self, case_sample: CaseSample, config_sample: ScoutIndividual = None, ) -> None:
        for scout_key in RAREDISEASE_SAMPLE_TAGS.keys():
            self._include_sample_file(scout_key, case_sample, config_sample)

    def _include_case_file(self, scout_key) -> None:
        """Include the file path associated to a scout configuration parameter if the corresponding housekeeper tags
        are found. Otherwise return None."""
        setattr(
            self.load_config,
            scout_key,
            self.get_file_from_hk(getattr(self.case_tags, scout_key)),
        )

    def _include_sample_file(self, scout_key, case_sample: CaseSample, config_sample: ScoutRarediseaseIndividual) -> None:
        """Include the file path associated to a scout configuration parameter if the corresponding housekeeper tags
        are found. Otherwise return None."""
        tags = getattr(self.sample_tags, scout_key)
        sample_id: str = case_sample.sample.internal_id
        scout_sample_tag: ScoutRarediseaseIndividual = scout_key.to_dot_notation_config()
        LOG.info(f"Scout key: {scout_key}")
        setattr(
            config_sample,
            scout_sample_tag,
            self.get_sample_file(hk_tags=tags, sample_id=sample_id),
        )

    @staticmethod
    def is_family_case(load_config: ScoutLoadConfig) -> bool:
        """Check if there are any linked individuals in a case"""
        for sample in load_config.samples:
            if sample.mother and sample.mother != "0":
                return True
            if sample.father and sample.father != "0":
                return True
        return False

    @staticmethod
    def is_multi_sample_case(load_config: ScoutLoadConfig) -> bool:
        return len(load_config.samples) > 1

    def run_madeline(self, family_obj: Case) -> Path:
        """Generate a madeline file for an analysis. Use customer sample names"""
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
