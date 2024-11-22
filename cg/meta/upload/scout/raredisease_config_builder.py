import logging
import re

from housekeeper.store.models import File, Version

from cg.apps.lims import LimsAPI
from cg.apps.madeline.api import MadelineAPI
from cg.constants.constants import FileFormat
from cg.constants.housekeeper_tags import (
    HK_DELIVERY_REPORT_TAG,
    AnalysisTag,
    NFAnalysisTags,
)
from cg.constants.scout import (
    RANK_MODEL_THRESHOLD,
    RAREDISEASE_CASE_TAGS,
    RAREDISEASE_SAMPLE_TAGS,
    GenomeBuild,
    UploadTrack,
)
from cg.constants.sequencing import Variants
from cg.io.controller import ReadFile
from cg.meta.upload.scout.hk_tags import CaseTags, SampleTags
from cg.meta.upload.scout.scout_config_builder import ScoutConfigBuilder
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.models.scout.scout_load_config import (
    CaseImages,
    CustomImages,
    Eklipse,
    RarediseaseLoadConfig,
    ScoutRarediseaseIndividual,
)
from cg.store.models import Analysis

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
        self.raredisease_analysis_api: RarediseaseAnalysisAPI = raredisease_analysis_api
        self.lims_api: LimsAPI = lims_api
        self.madeline_api: MadelineAPI = madeline_api

    def build_load_config(self) -> RarediseaseLoadConfig:
        """Create a RAREDISEASE specific load config for uploading analysis to Scout."""
        LOG.info("Build load config for RAREDISEASE case")
        load_config: RarediseaseLoadConfig = RarediseaseLoadConfig(
            track=UploadTrack.RARE_DISEASE.value,
            delivery_report=self.get_file_from_hk({HK_DELIVERY_REPORT_TAG}),
        )
        self.add_common_info_to_load_config(load_config)
        load_config.gene_panels = self.raredisease_analysis_api.get_aggregated_panels(
            customer_id=self.analysis_obj.case.customer.internal_id,
            default_panels=set(self.analysis_obj.case.panels),
        )
        self.include_case_files(load_config)
        self.get_sample_information(load_config)
        self.include_pedigree_picture(load_config)
        self.load_custom_image_sample(load_config)
        load_config.human_genome_build = GenomeBuild.hg19
        load_config.rank_score_threshold = RANK_MODEL_THRESHOLD
        load_config.rank_model_version = self.get_rank_model_version(variant_type=Variants.SNV)
        load_config.sv_rank_model_version = self.get_rank_model_version(variant_type=Variants.SV)
        return load_config

    def get_rank_model_version(self, variant_type: Variants) -> str:
        """
        Returns the rank model version for a variant type from the manifest file.
        Raises:
            FileNotFoundError if no manifest file is found in housekeeper.
        """
        hk_manifest_file: File = self.get_file_from_hk({NFAnalysisTags.MANIFEST})
        if not hk_manifest_file:
            raise FileNotFoundError("No manifest file found in Housekeeper.")
        return self.extract_rank_model_from_manifest(
            hk_manifest_file=hk_manifest_file, variant_type=variant_type
        )

    def extract_rank_model_from_manifest(
        self, hk_manifest_file: File, variant_type: Variants
    ) -> str:
        content: dict[str, dict[str, str]] = ReadFile.get_content_from_file(
            file_format=FileFormat.JSON, file_path=hk_manifest_file
        )
        return self.get_rank_model_version_from_manifest_content(
            content=content, variant_type=variant_type
        )

    def get_rank_model_version_from_manifest_content(
        self, content: dict[str, dict[str, str]], variant_type: Variants
    ) -> str:
        """
        Return the rank model version from the manifest file content.
        Raises:
            ValueError if pattern not found ing process or clinical not found in script.
        """
        pattern: str = variant_type.upper() + ":GENMOD_SCORE"
        for key, value in content["tasks"].items():
            process: str = value.get("process")
            script: str = value.get("script")
            if pattern in process and AnalysisTag.CLINICAL in script:
                return self._get_version_from_manifest_script(script)
        raise ValueError(
            f"Either {pattern} not found in any process or {AnalysisTag.CLINICAL} not found in any script of the manifest file"
        )

    def _get_version_from_manifest_script(self, script: str) -> str:
        """
        Returns the rank model version in the format 'vX.X from the given script string.
        Raises a ValueError if no rank model version is found in the script string.
        """
        if match := re.search(r"v(\d+\.\d+)", script):
            return match.group(1)
        raise ValueError("No rank model version found")

    def load_custom_image_sample(self, load_config: RarediseaseLoadConfig) -> None:
        """Build custom images config."""
        LOG.info("Adding custom images")

        eklipse_images: list = []
        for sample in self.analysis_obj.case.samples:
            sample_id: str = sample.internal_id
            eklipse_image_path = self.get_file_from_hk(
                hk_tags=set(self.sample_tags.eklipse_path).union({sample_id})
            )
            if eklipse_image_path:
                eklipse_image = Eklipse(
                    title=sample_id,
                    path=eklipse_image_path,
                    description="eKLIPse MT images",
                    width="800",
                    height="800",
                )
                eklipse_images.append(eklipse_image)
        if eklipse_images:
            case_images = CaseImages(eKLIPse=eklipse_images)
            config_custom_images = CustomImages(case_images=case_images)
            load_config.custom_images = config_custom_images

    def include_case_files(self, load_config: RarediseaseLoadConfig) -> None:
        """Include case level files for mip case."""
        LOG.info("Including RAREDISEASE specific case level files")
        for scout_key in RAREDISEASE_CASE_TAGS.keys():
            self._include_case_file(load_config, scout_key)

    def _include_case_file(self, load_config: RarediseaseLoadConfig, scout_key: str) -> None:
        """Include the file path associated to a scout configuration parameter if the corresponding housekeeper tags
        are found. Otherwise return None."""
        file_path = self.get_file_from_hk(getattr(self.case_tags, scout_key))
        setattr(load_config, scout_key, file_path)

    def include_sample_files(self, config_sample: ScoutRarediseaseIndividual) -> None:
        """Include sample level files that are optional for mip samples."""
        LOG.info("Including RAREDISEASE specific sample level files")
        sample_id: str = config_sample.sample_id
        config_sample.vcf2cytosure = self.get_sample_file(
            hk_tags=self.sample_tags.vcf2cytosure, sample_id=sample_id
        )
        config_sample.mt_bam = self.get_sample_file(
            hk_tags=self.sample_tags.mt_bam, sample_id=sample_id
        )
        config_sample.chromograph_images.autozygous = self.remove_chromosome_substring(
            file_path=self.get_sample_file(
                hk_tags=self.sample_tags.chromograph_autozyg, sample_id=sample_id
            )
        )
        config_sample.chromograph_images.coverage = self.remove_chromosome_substring(
            file_path=self.get_sample_file(
                hk_tags=self.sample_tags.chromograph_coverage, sample_id=sample_id
            )
        )
        config_sample.chromograph_images.upd_regions = self.remove_chromosome_substring(
            file_path=self.get_sample_file(
                hk_tags=self.sample_tags.chromograph_regions, sample_id=sample_id
            )
        )
        config_sample.chromograph_images.upd_sites = self.remove_chromosome_substring(
            file_path=self.get_sample_file(
                hk_tags=self.sample_tags.chromograph_sites, sample_id=sample_id
            )
        )
        config_sample.reviewer.alignment = self.get_sample_file(
            hk_tags=self.sample_tags.reviewer_alignment, sample_id=sample_id
        )
        config_sample.reviewer.alignment_index = self.get_sample_file(
            hk_tags=self.sample_tags.reviewer_alignment_index, sample_id=sample_id
        )
        config_sample.reviewer.vcf = self.get_sample_file(
            hk_tags=self.sample_tags.reviewer_vcf, sample_id=sample_id
        )
        config_sample.reviewer.catalog = self.get_file_from_hk(hk_tags=self.case_tags.str_catalog)
        config_sample.mitodel_file = self.get_sample_file(
            hk_tags=self.sample_tags.mitodel_file, sample_id=sample_id
        )
