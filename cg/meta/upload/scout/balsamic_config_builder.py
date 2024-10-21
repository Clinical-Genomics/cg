import logging

from housekeeper.store.models import Version

from cg.apps.lims import LimsAPI
from cg.constants.constants import SampleType
from cg.constants.housekeeper_tags import HK_DELIVERY_REPORT_TAG
from cg.constants.scout import (
    BALSAMIC_CASE_TAGS,
    BALSAMIC_SAMPLE_TAGS,
    GenomeBuild,
    UploadTrack,
)
from cg.constants.subject import PhenotypeStatus
from cg.meta.upload.scout.hk_tags import CaseTags, SampleTags
from cg.meta.upload.scout.scout_config_builder import ScoutConfigBuilder
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.models.scout.scout_load_config import BalsamicLoadConfig, ScoutCancerIndividual
from cg.store.models import Analysis, CaseSample, Sample

LOG = logging.getLogger(__name__)


class BalsamicConfigBuilder(ScoutConfigBuilder):
    def __init__(self, hk_version_obj: Version, analysis_obj: Analysis, lims_api: LimsAPI):
        super().__init__(
            hk_version_obj=hk_version_obj,
            analysis_obj=analysis_obj,
            lims_api=lims_api,
        )
        self.case_tags: CaseTags = CaseTags(**BALSAMIC_CASE_TAGS)
        self.sample_tags: SampleTags = SampleTags(**BALSAMIC_SAMPLE_TAGS)

    def include_case_files(self, load_config: BalsamicLoadConfig) -> None:
        LOG.info("Including BALSAMIC specific case level files")
        load_config.vcf_cancer = self.get_file_from_hk(hk_tags=self.case_tags.snv_vcf, latest=True)
        load_config.vcf_cancer_sv = self.get_file_from_hk(
            hk_tags=self.case_tags.sv_vcf, latest=True
        )
        self.include_cnv_report(load_config)
        self.include_multiqc_report(load_config)

    def include_sample_files(self, config_sample: ScoutCancerIndividual) -> None:
        LOG.info("Including BALSAMIC specific sample level files.")

        sample_id: str = config_sample.sample_id
        if config_sample.alignment_path:
            if SampleType.TUMOR in config_sample.alignment_path:
                sample_id = SampleType.TUMOR.value
            elif SampleType.NORMAL in config_sample.alignment_path:
                sample_id = SampleType.NORMAL.value

        config_sample.vcf2cytosure = self.get_sample_file(
            hk_tags=self.sample_tags.vcf2cytosure, sample_id=sample_id
        )

    def build_config_sample(self, case_sample: CaseSample) -> ScoutCancerIndividual:
        """Build a sample with balsamic specific information."""
        config_sample = ScoutCancerIndividual()
        self.add_common_sample_info(config_sample=config_sample, case_sample=case_sample)
        self.add_common_sample_files(config_sample=config_sample, case_sample=case_sample)
        if BalsamicAnalysisAPI.get_sample_type(sample_obj=case_sample.sample) == SampleType.TUMOR:
            config_sample.phenotype = PhenotypeStatus.AFFECTED.value
        else:
            config_sample.phenotype = PhenotypeStatus.UNAFFECTED.value

        config_sample.analysis_type = self.get_balsamic_analysis_type(sample=case_sample.sample)

        return config_sample

    def get_balsamic_analysis_type(self, sample: Sample) -> str:
        """Returns a formatted balsamic analysis type"""

        analysis_type: str = BalsamicAnalysisAPI.get_application_type(sample_obj=sample)
        if analysis_type == "tgs":
            analysis_type = "panel"
        if analysis_type == "wgs":
            analysis_type = "wgs"

        return analysis_type

    def build_load_config(self) -> BalsamicLoadConfig:
        LOG.info("Build load config for balsamic case")
        load_config: BalsamicLoadConfig = BalsamicLoadConfig(
            track=UploadTrack.CANCER.value,
            delivery_report=self.get_file_from_hk({HK_DELIVERY_REPORT_TAG}),
        )
        self.add_common_info_to_load_config(load_config)
        load_config.human_genome_build = GenomeBuild.hg19
        load_config.rank_score_threshold = -100
        self.include_case_files(load_config)

        LOG.info("Building samples")
        db_sample: CaseSample

        for db_sample in self.analysis_obj.case.links:
            load_config.samples.append(self.build_config_sample(case_sample=db_sample))

        return load_config
