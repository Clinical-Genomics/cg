import logging

from housekeeper.store.models import Version

from cg.apps.lims import LimsAPI
from cg.apps.madeline.api import MadelineAPI
from cg.constants.housekeeper_tags import HK_DELIVERY_REPORT_TAG
from cg.constants.scout import (
    MIP_CASE_TAGS,
    MIP_SAMPLE_TAGS,
    RANK_MODEL_THRESHOLD,
    GenomeBuild,
    UploadTrack,
)
from cg.meta.upload.scout.hk_tags import CaseTags, SampleTags
from cg.meta.upload.scout.scout_config_builder import ScoutConfigBuilder
from cg.meta.workflow.mip import MipAnalysisAPI
from cg.models.mip.mip_analysis import MipAnalysis
from cg.models.scout.scout_load_config import MipLoadConfig, ScoutMipIndividual
from cg.store.models import Analysis, CaseSample

LOG = logging.getLogger(__name__)


class MipConfigBuilder(ScoutConfigBuilder):
    def __init__(
        self,
        mip_analysis_api: MipAnalysisAPI,
        lims_api: LimsAPI,
        madeline_api: MadelineAPI,
    ):
        super().__init__(
            lims_api=lims_api,
        )
        self.case_tags: CaseTags = CaseTags(**MIP_CASE_TAGS)
        self.sample_tags: SampleTags = SampleTags(**MIP_SAMPLE_TAGS)
        self.mip_analysis_api: MipAnalysisAPI = mip_analysis_api
        self.lims_api: LimsAPI = lims_api
        self.madeline_api: MadelineAPI = madeline_api

    def build_load_config(
        self,
        hk_version: Version,
        analysis: Analysis,
        rank_score_threshold: int = RANK_MODEL_THRESHOLD,
    ) -> MipLoadConfig:
        """Create a MIP specific load config for uploading analysis to Scout."""
        LOG.info("Generate load config for mip case")
        load_config: MipLoadConfig = MipLoadConfig(
            track=UploadTrack.RARE_DISEASE.value,
            delivery_report=self.get_file_from_hk(
                hk_tags={HK_DELIVERY_REPORT_TAG}, hk_version=hk_version
            ),
        )
        self.add_common_info_to_load_config(load_config=load_config, analysis=analysis)
        mip_analysis_data: MipAnalysis = self.mip_analysis_api.get_latest_metadata(
            analysis.case.internal_id
        )
        load_config.human_genome_build = (
            GenomeBuild.hg38
            if GenomeBuild.hg38 in mip_analysis_data.genome_build
            else GenomeBuild.hg19
        )
        load_config.rank_score_threshold = rank_score_threshold
        load_config.rank_model_version = mip_analysis_data.rank_model_version
        load_config.sv_rank_model_version = mip_analysis_data.sv_rank_model_version

        load_config.gene_panels = (
            self.mip_analysis_api.get_aggregated_panels(
                customer_id=analysis.case.customer.internal_id,
                default_panels=set(analysis.case.panels),
            )
            or None
        )

        self.include_case_files(load_config=load_config, hk_version=hk_version)

        LOG.info("Building samples")
        db_sample: CaseSample
        for db_sample in analysis.case.links:
            load_config.samples.append(
                self.build_config_sample(case_sample=db_sample, hk_version=hk_version)
            )
        self.include_pedigree_picture(load_config=load_config, analysis=analysis)
        return load_config

    def include_case_files(self, load_config: MipLoadConfig, hk_version: Version) -> None:
        """Include case level files for mip case"""
        LOG.info("Including MIP specific case level files")
        load_config.peddy_check = self.get_file_from_hk(
            self.case_tags.peddy_check, hk_version=hk_version
        )
        load_config.peddy_ped = self.get_file_from_hk(
            self.case_tags.peddy_ped, hk_version=hk_version
        )
        load_config.peddy_sex = self.get_file_from_hk(
            self.case_tags.peddy_sex, hk_version=hk_version
        )
        load_config.smn_tsv = self.get_file_from_hk(self.case_tags.smn_tsv, hk_version=hk_version)
        load_config.vcf_mei = self.get_file_from_hk(self.case_tags.vcf_mei, hk_version=hk_version)
        load_config.vcf_mei_research = self.get_file_from_hk(
            self.case_tags.vcf_mei_research, hk_version=hk_version
        )
        load_config.vcf_snv = self.get_file_from_hk(self.case_tags.snv_vcf, hk_version=hk_version)
        load_config.vcf_snv_research = self.get_file_from_hk(
            self.case_tags.snv_research_vcf, hk_version=hk_version
        )
        load_config.vcf_str = self.get_file_from_hk(self.case_tags.vcf_str, hk_version=hk_version)
        load_config.vcf_sv = self.get_file_from_hk(self.case_tags.sv_vcf, hk_version=hk_version)
        load_config.vcf_sv_research = self.get_file_from_hk(
            self.case_tags.sv_research_vcf, hk_version=hk_version
        )
        self.include_multiqc_report(load_config=load_config, hk_version=hk_version)

    def include_sample_files(self, config_sample: ScoutMipIndividual, hk_version: Version) -> None:
        """Include sample level files that are optional for mip samples"""
        LOG.info("Including MIP specific sample level files")
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
        config_sample.upd_regions_bed = self.get_sample_file(
            hk_tags=self.sample_tags.upd_regions_bed, hk_version=hk_version, sample_id=sample_id
        )
        config_sample.upd_sites_bed = self.get_sample_file(
            hk_tags=self.sample_tags.upd_sites_bed, hk_version=hk_version, sample_id=sample_id
        )
        self.include_reviewer_files(config_sample=config_sample, hk_version=hk_version)
