import logging

from housekeeper.store.models import Version

from cg.apps.lims import LimsAPI
from cg.constants.constants import PrepCategory
from cg.constants.housekeeper_tags import HK_DELIVERY_REPORT_TAG
from cg.constants.scout import TOMTE_CASE_TAGS, TOMTE_SAMPLE_TAGS, GenomeBuild, UploadTrack
from cg.constants.subject import RelationshipStatus
from cg.meta.upload.scout.hk_tags import CaseTags, SampleTags
from cg.meta.upload.scout.scout_config_builder import ScoutConfigBuilder
from cg.meta.workflow.tomte import TomteAnalysisAPI
from cg.models.scout.scout_load_config import OmicsFiles, ScoutRnaIndividual, TomteLoadConfig
from cg.store.models import Analysis, CaseSample, Sample

LOG = logging.getLogger(__name__)


class TomteConfigBuilder(ScoutConfigBuilder):
    """Class for handling Tomte information and files to be included in Scout upload."""

    def __init__(
        self,
        hk_version_obj: Version,
        analysis_obj: Analysis,
        analysis_api: TomteAnalysisAPI,
        lims_api: LimsAPI,
    ):
        super().__init__(
            hk_version_obj=hk_version_obj, analysis_obj=analysis_obj, lims_api=lims_api
        )
        self.case_tags: CaseTags = CaseTags(**TOMTE_CASE_TAGS)
        self.sample_tags: SampleTags = SampleTags(**TOMTE_SAMPLE_TAGS)
        self.load_config: TomteLoadConfig = TomteLoadConfig(
            track=UploadTrack.RARE_DISEASE.value,
            delivery_report=self.get_file_from_hk({HK_DELIVERY_REPORT_TAG}),
        )
        self.analysis_api: TomteAnalysisAPI = analysis_api

    def build_load_config(self) -> None:
        """Build a Tomte-specific load config for uploading a case to Scout."""
        LOG.info("Build load config for Tomte case")
        self.add_common_info_to_load_config()
        self.load_config.rna_genome_build = getattr(
            GenomeBuild,
            self.analysis_api.get_genome_build(case_id=self.analysis_obj.case.internal_id),
        )

        self.load_config.gene_panels: list[str] = self.analysis_api.get_aggregated_panels(
            customer_id=self.analysis_obj.case.customer.internal_id,
            default_panels=set(self.analysis_obj.case.panels),
        )

        self.include_case_files()

        LOG.info("Building samples")
        db_sample: CaseSample

        for db_sample in self.analysis_obj.case.links:
            self.load_config.samples.append(self.build_config_sample(case_sample=db_sample))

    def include_case_files(self) -> None:
        """Include case level files for Tomte case."""
        LOG.info("Including Tomte specific case level files")
        self.load_config.vcf_snv = self.get_file_from_hk(self.case_tags.snv_vcf)
        self.load_config.vcf_snv_research = self.get_file_from_hk(self.case_tags.snv_research_vcf)
        self.load_config.multiqc_rna = self.get_file_from_hk(self.case_tags.multiqc_rna)
        self.include_omics_files()

    def include_omics_files(self) -> None:
        """Build a sample with Tomte specific information."""
        omics_files = OmicsFiles()
        omics_files.fraser = self.get_file_from_hk(self.case_tags.fraser_tsv)
        omics_files.outrider = self.get_file_from_hk(self.case_tags.outrider_tsv)
        self.load_config.omics_files = omics_files.dict()

    def include_sample_files(self, config_sample: ScoutRnaIndividual) -> None:
        """Include sample level files that are optional."""
        LOG.info("Including Tomte specific sample level files")
        self.include_sample_rna_alignment_file(config_sample=config_sample)
        self.include_sample_splice_junctions_bed(config_sample=config_sample)
        self.include_sample_rna_coverage_bigwig(config_sample=config_sample)

    def build_config_sample(self, case_sample: CaseSample) -> ScoutRnaIndividual:
        """Build a sample with Tomte specific information."""
        config_sample = ScoutRnaIndividual()
        self.add_common_sample_info(config_sample=config_sample, case_sample=case_sample)
        self.include_sample_files(config_sample)
        config_sample.analysis_type: str = PrepCategory.WHOLE_TRANSCRIPTOME_SEQUENCING.value
        config_sample.father: Sample | str = (
            case_sample.father.internal_id
            if case_sample.father
            else RelationshipStatus.HAS_NO_PARENT
        )
        config_sample.mother: Sample | str = (
            case_sample.mother.internal_id
            if case_sample.mother
            else RelationshipStatus.HAS_NO_PARENT
        )
        return config_sample
