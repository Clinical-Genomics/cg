import logging

from housekeeper.store.models import Version

from cg.apps.lims import LimsAPI
from cg.apps.madeline.api import MadelineAPI
from cg.constants.constants import GenomeBuild
from cg.constants.housekeeper_tags import HK_DELIVERY_REPORT_TAG
from cg.constants.scout import (
    RANK_MODEL_THRESHOLD,
    RAREDISEASE_CASE_TAGS,
    RAREDISEASE_SAMPLE_TAGS,
    UploadTrack,
)
from cg.constants.sequencing import Variants
from cg.meta.upload.scout.hk_tags import CaseTags, SampleTags
from cg.meta.upload.scout.rank_model import RankModel, parse_rank_model_file
from cg.meta.upload.scout.scout_config_builder import ScoutConfigBuilder
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.models.scout.scout_load_config import (
    CaseImages,
    CustomImage,
    CustomImages,
    RarediseaseLoadConfig,
    ScoutRarediseaseIndividual,
)
from cg.store.models import Analysis

LOG = logging.getLogger(__name__)


class RarediseaseConfigBuilder(ScoutConfigBuilder):
    def __init__(
        self,
        raredisease_analysis_api: RarediseaseAnalysisAPI,
        lims_api: LimsAPI,
        madeline_api: MadelineAPI,
    ):
        super().__init__(
            lims_api=lims_api,
        )
        self.case_tags: CaseTags = CaseTags(**RAREDISEASE_CASE_TAGS)
        self.sample_tags: SampleTags = SampleTags(**RAREDISEASE_SAMPLE_TAGS)
        self.raredisease_analysis_api: RarediseaseAnalysisAPI = raredisease_analysis_api
        self.lims_api: LimsAPI = lims_api
        self.madeline_api: MadelineAPI = madeline_api

    def build_load_config(self, hk_version: Version, analysis: Analysis) -> RarediseaseLoadConfig:
        """Create a RAREDISEASE specific load config for uploading analysis to Scout."""
        LOG.info("Build load config for RAREDISEASE case")
        load_config: RarediseaseLoadConfig = RarediseaseLoadConfig(
            track=UploadTrack.RARE_DISEASE.value,
            delivery_report=self.get_file_from_hk(
                hk_tags={HK_DELIVERY_REPORT_TAG}, hk_version=hk_version
            ),
        )
        self.add_common_info_to_load_config(load_config=load_config, analysis=analysis)
        load_config.gene_panels = self.raredisease_analysis_api.get_aggregated_panels(
            customer_id=analysis.case.customer.internal_id,
            default_panels=set(analysis.case.panels),
        )
        self.include_case_files(load_config=load_config, hk_version=hk_version)
        self.get_sample_information(
            load_config=load_config, analysis=analysis, hk_version=hk_version
        )
        self.include_pedigree_picture(load_config=load_config, analysis=analysis)
        self.load_custom_image_sample(
            load_config=load_config, analysis=analysis, hk_version=hk_version
        )
        load_config.human_genome_build = GenomeBuild.hg38
        load_config.rank_score_threshold = RANK_MODEL_THRESHOLD
        snv_rank_model: RankModel = self._get_rank_model(
            hk_version=hk_version, variant_type=Variants.SNV
        )
        load_config.rank_model_url = snv_rank_model.path
        load_config.rank_model_version = snv_rank_model.version
        sv_rank_model: RankModel = self._get_rank_model(
            hk_version=hk_version, variant_type=Variants.SV
        )
        load_config.sv_rank_model_url = sv_rank_model.path
        load_config.sv_rank_model_version = sv_rank_model.version
        return load_config

    def _get_rank_model(self, hk_version: Version, variant_type: Variants) -> RankModel:
        if variant_type == Variants.SNV:
            tags = {"rank-model-snv"}
        else:
            tags = {"rank-model-sv"}
        file_path: str | None = self.get_file_from_hk(hk_tags=tags, hk_version=hk_version)
        if not file_path:
            raise FileNotFoundError(f"No {variant_type} rank model file found in Housekeeper.")
        return parse_rank_model_file(file_path)

    def load_custom_image_sample(
        self, load_config: RarediseaseLoadConfig, analysis: Analysis, hk_version: Version
    ) -> None:
        """Build custom images config."""
        LOG.info("Adding custom images")

        saltshaker_images: list = []
        for sample in analysis.case.samples:
            sample_id: str = sample.internal_id
            saltshaker_image_path = self.get_file_from_hk(
                hk_tags=set(self.sample_tags.saltshaker_path).union({sample_id}),
                hk_version=hk_version,
            )
            if saltshaker_image_path:
                saltshaker_image = CustomImage(
                    title=sample_id,
                    path=saltshaker_image_path,
                    description="SAltShaker MT images",
                    width="1000",
                    height="800",
                )
                saltshaker_images.append(saltshaker_image)
        if saltshaker_images:
            case_images = CaseImages(saltshaker=saltshaker_images)
            config_custom_images = CustomImages(case_images=case_images)
            load_config.custom_images = config_custom_images

    def include_case_files(self, load_config: RarediseaseLoadConfig, hk_version: Version) -> None:
        """Include case level files for RAREDISEASE case."""
        LOG.info("Including RAREDISEASE specific case level files")
        for scout_key in RAREDISEASE_CASE_TAGS.keys():
            self._include_case_file(
                load_config=load_config, scout_key=scout_key, hk_version=hk_version
            )

    def _include_case_file(
        self, load_config: RarediseaseLoadConfig, scout_key: str, hk_version: Version
    ) -> None:
        """Include the file path associated to a scout configuration parameter if the corresponding housekeeper tags
        are found. Returns None."""
        file_path = self.get_file_from_hk(getattr(self.case_tags, scout_key), hk_version=hk_version)
        setattr(load_config, scout_key, file_path)

    def include_sample_files(
        self, config_sample: ScoutRarediseaseIndividual, hk_version: Version
    ) -> None:
        """Include sample level files that are optional for mip samples."""
        LOG.info("Including RAREDISEASE specific sample level files")
        sample_id: str = config_sample.sample_id
        config_sample.vcf2cytosure = self.get_sample_file(
            hk_tags=self.sample_tags.vcf2cytosure,
            sample_id=sample_id,
            hk_version=hk_version,
        )
        config_sample.mt_bam = self.get_sample_file(
            hk_tags=self.sample_tags.mt_bam, sample_id=sample_id, hk_version=hk_version
        )
        config_sample.chromograph_images.autozygous = self.remove_chromosome_substring(
            file_path=self.get_sample_file(
                hk_tags=self.sample_tags.chromograph_autozyg,
                sample_id=sample_id,
                hk_version=hk_version,
            )
        )
        config_sample.chromograph_images.coverage = self.remove_chromosome_substring(
            file_path=self.get_sample_file(
                hk_tags=self.sample_tags.chromograph_coverage,
                sample_id=sample_id,
                hk_version=hk_version,
            )
        )
        config_sample.chromograph_images.upd_regions = self.remove_chromosome_substring(
            file_path=self.get_sample_file(
                hk_tags=self.sample_tags.chromograph_regions,
                sample_id=sample_id,
                hk_version=hk_version,
            )
        )
        config_sample.chromograph_images.upd_sites = self.remove_chromosome_substring(
            file_path=self.get_sample_file(
                hk_tags=self.sample_tags.chromograph_sites,
                sample_id=sample_id,
                hk_version=hk_version,
            )
        )
        config_sample.mitodel_file = self.get_sample_file(
            hk_tags=self.sample_tags.mitodel_file,
            sample_id=sample_id,
            hk_version=hk_version,
        )
        config_sample.tiddit_coverage_wig = self.get_sample_file(
            hk_tags=self.sample_tags.tiddit_coverage_wig, hk_version=hk_version, sample_id=sample_id
        )
        self.include_reviewer_files(config_sample=config_sample, hk_version=hk_version)

    def _get_reviewer_reference_file(self) -> str:
        return self.raredisease_analysis_api.reference
