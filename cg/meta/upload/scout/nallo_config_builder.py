import logging

from housekeeper.store.models import Version

from cg.apps.lims import LimsAPI
from cg.apps.madeline.api import MadelineAPI
from cg.constants.housekeeper_tags import HK_DELIVERY_REPORT_TAG
from cg.constants.scout import (
    NALLO_CASE_TAGS,
    NALLO_RANK_MODEL_THRESHOLD,
    NALLO_RANK_MODEL_VERSION_SNV,
    NALLO_RANK_MODEL_VERSION_SV,
    NALLO_SAMPLE_TAGS,
    GenomeBuild,
    UploadTrack,
)
from cg.meta.upload.scout.hk_tags import CaseTags, SampleTags
from cg.meta.upload.scout.scout_config_builder import ScoutConfigBuilder
from cg.meta.workflow.nallo import NalloAnalysisAPI
from cg.models.scout.scout_load_config import NalloLoadConfig, ScoutNalloIndividual
from cg.store.models import Analysis

LOG = logging.getLogger(__name__)


class NalloConfigBuilder(ScoutConfigBuilder):
    def __init__(
        self,
        nallo_analysis_api: NalloAnalysisAPI,
        lims_api: LimsAPI,
        madeline_api: MadelineAPI,
    ):
        super().__init__(
            lims_api=lims_api,
        )
        self.case_tags = CaseTags(**NALLO_CASE_TAGS)
        self.sample_tags = SampleTags(**NALLO_SAMPLE_TAGS)
        self.nallo_analysis_api: NalloAnalysisAPI = nallo_analysis_api
        self.lims_api: LimsAPI = lims_api
        self.madeline_api: MadelineAPI = madeline_api

    def build_load_config(self, hk_version: Version, analysis: Analysis) -> NalloLoadConfig:
        """Create a NALLO specific load config for uploading analysis to Scout."""
        LOG.info("Build load config for NALLO case")
        load_config = NalloLoadConfig(
            track=UploadTrack.RARE_DISEASE.value,
            delivery_report=self.get_file_from_hk(
                hk_tags={HK_DELIVERY_REPORT_TAG}, hk_version=hk_version
            ),
        )
        self.add_common_info_to_load_config(load_config=load_config, analysis=analysis)
        load_config.gene_panels = self.nallo_analysis_api.get_aggregated_panels(
            customer_id=analysis.case.customer.internal_id,
            default_panels=set(analysis.case.panels),
        )
        self.include_case_files(load_config=load_config, hk_version=hk_version)
        LOG.info("Building samples")
        self.get_sample_information(
            load_config=load_config, analysis=analysis, hk_version=hk_version
        )
        self.include_pedigree_picture(load_config=load_config, analysis=analysis)
        load_config.human_genome_build = GenomeBuild.hg38
        load_config.rank_score_threshold = NALLO_RANK_MODEL_THRESHOLD
        load_config.rank_model_version = NALLO_RANK_MODEL_VERSION_SNV
        load_config.sv_rank_model_version = NALLO_RANK_MODEL_VERSION_SV
        return load_config

    def include_case_files(self, load_config: NalloLoadConfig, hk_version: Version = None) -> None:
        """Include case level files for NALLO case."""
        LOG.info("Including NALLO specific case level files")
        for scout_key in NALLO_CASE_TAGS.keys():
            self._include_case_file(
                load_config=load_config, scout_key=scout_key, hk_version=hk_version
            )

    def _include_case_file(
        self, load_config: NalloLoadConfig, scout_key: str, hk_version: Version
    ) -> None:
        """Include the file path associated to a scout configuration parameter if the corresponding housekeeper tags
        are found. Otherwise return None."""
        file_path = self.get_file_from_hk(
            hk_tags=getattr(self.case_tags, scout_key), hk_version=hk_version
        )
        setattr(load_config, scout_key, file_path)

    def include_sample_files(
        self, config_sample: ScoutNalloIndividual, hk_version: Version
    ) -> None:
        """Include sample level files that are optional."""
        LOG.info("Including NALLO specific sample level files")
        sample_id: str = config_sample.sample_id
        config_sample.d4_file = self.get_sample_file(
            hk_tags=self.sample_tags.d4_file, sample_id=sample_id, hk_version=hk_version
        )
        config_sample.paraphase_alignment_path = self.get_sample_file(
            hk_tags=self.sample_tags.paraphase_alignment_path,
            sample_id=sample_id,
            hk_version=hk_version,
        )
        config_sample.tiddit_coverage_wig = self.get_sample_file(
            hk_tags=self.sample_tags.hificnv_coverage,
            sample_id=sample_id,
            hk_version=hk_version,
        )
        config_sample.minor_allele_frequency_wig = self.get_sample_file(
            hk_tags=self.sample_tags.minor_allele_frequency_wig,
            sample_id=sample_id,
            hk_version=hk_version,
        )
        config_sample.alignment_path = self.get_sample_file(
            hk_tags=self.sample_tags.alignment_path,
            sample_id=sample_id,
            hk_version=hk_version,
        )
        self.include_reviewer_files(config_sample=config_sample, hk_version=hk_version)
        config_sample.reviewer.trgt = (
            True
            if any(
                [
                    config_sample.reviewer.alignment,
                    config_sample.reviewer.alignment_index,
                    config_sample.reviewer.vcf,
                    config_sample.reviewer.catalog,
                ]
            )
            else None
        )
