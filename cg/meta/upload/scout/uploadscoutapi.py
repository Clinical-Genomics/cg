"""File includes api to uploading data into Scout."""

import logging
from pathlib import Path

from housekeeper.store.models import File, Version

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.madeline.api import MadelineAPI
from cg.apps.scout.scoutapi import ScoutAPI
from cg.constants import HK_MULTIQC_HTML_TAG, Workflow
from cg.constants.constants import FileFormat
from cg.constants.housekeeper_tags import HK_DELIVERY_REPORT_TAG, AlignmentFileTag, AnalysisTag
from cg.constants.scout import GenomeBuild, ScoutCustomCaseReportTags
from cg.exc import CgDataError, HousekeeperBundleVersionMissingError
from cg.io.controller import WriteFile
from cg.meta.upload.scout.balsamic_config_builder import BalsamicConfigBuilder
from cg.meta.upload.scout.balsamic_umi_config_builder import BalsamicUmiConfigBuilder
from cg.meta.upload.scout.mip_config_builder import MipConfigBuilder
from cg.meta.upload.scout.nallo_config_builder import NalloConfigBuilder
from cg.meta.upload.scout.raredisease_config_builder import RarediseaseConfigBuilder
from cg.meta.upload.scout.rnafusion_config_builder import RnafusionConfigBuilder
from cg.meta.upload.scout.scout_config_builder import ScoutConfigBuilder
from cg.meta.workflow.analysis import AnalysisAPI
from cg.models.scout.scout_load_config import ScoutLoadConfig
from cg.store.api.data_classes import RNADNACollection
from cg.store.models import Analysis, Case
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class UploadScoutAPI:
    """Class that handles everything that has to do with uploading to Scout."""

    def __init__(
        self,
        hk_api: HousekeeperAPI,
        scout_api: ScoutAPI,
        lims_api: LimsAPI,
        analysis_api: AnalysisAPI,
        madeline_api: MadelineAPI,
        status_db: Store,
    ):
        self.housekeeper = hk_api
        self.scout_api = scout_api
        self.madeline_api = madeline_api
        self.analysis_api = analysis_api
        self.raredisease_analysis_api = analysis_api
        self.lims = lims_api
        self.status_db = status_db

    def generate_config(self, analysis: Analysis) -> ScoutLoadConfig:
        """Fetch data about an analysis to load Scout."""
        LOG.info("Generate scout load config")
        # Fetch last version from housekeeper
        # This should be safe since analyses are only added if data is analysed
        hk_version: Version = self.housekeeper.last_version(analysis.case.internal_id)
        LOG.debug(f"Found housekeeper version {hk_version.id}")

        LOG.info(f"Found workflow {analysis.workflow}")
        config_builder = self.get_config_builder(analysis=analysis)
        return config_builder.build_load_config(hk_version=hk_version, analysis=analysis)

    @staticmethod
    def get_load_config_tag() -> str:
        """Get the Housekeeper tag for a Scout load config."""
        return "scout-load-config"

    @staticmethod
    def save_config_file(upload_config: ScoutLoadConfig, file_path: Path) -> None:
        """Save a Scout load config file to the supplied file path."""

        LOG.info(f"Save Scout load config to {file_path.as_posix()}.")
        WriteFile.write_file_from_content(
            content=upload_config.model_dump(exclude_none=True),
            file_format=FileFormat.YAML,
            file_path=file_path,
        )

    def add_scout_config_to_hk(
        self, config_file_path: Path, case_id: str, delete: bool = False
    ) -> File:
        """Add Scout load config to Housekeeper bundle."""
        LOG.info(f"Adding load config {config_file_path} to Housekeeper.")
        tag_name: str = self.get_load_config_tag()
        version: Version = self.housekeeper.last_version(case_id)
        uploaded_config_file: File | None = self.housekeeper.get_latest_file_from_version(
            version=version, tags={tag_name}
        )
        if uploaded_config_file:
            LOG.info(f"Found config file: {uploaded_config_file}.")
            if not delete:
                raise FileExistsError("Upload config already exists.")
            self.housekeeper.delete_file(uploaded_config_file.id)

        file_obj: File = self.housekeeper.add_file(
            path=str(config_file_path), version_obj=version, tags=[tag_name]
        )
        self.housekeeper.include_file(file_obj=file_obj, version_obj=version)
        self.housekeeper.add_commit(file_obj)

        LOG.info(f"Added Scout load config to Housekeeper: {config_file_path}.")
        return file_obj

    def get_multiqc_html_report(
        self, case_id: str, workflow: Workflow
    ) -> tuple[ScoutCustomCaseReportTags, File | None]:
        """Return a multiqc report for a case in Housekeeper."""
        if workflow == Workflow.MIP_RNA:
            tags: set[str] = {HK_MULTIQC_HTML_TAG, case_id}
            return (
                ScoutCustomCaseReportTags.MULTIQC_RNA,
                self.housekeeper.get_file_from_latest_version(bundle_name=case_id, tags=tags),
            )
        tags: set[str] = {HK_MULTIQC_HTML_TAG, case_id}
        if workflow == Workflow.TOMTE:
            return (
                ScoutCustomCaseReportTags.MULTIQC_RNA,
                self.housekeeper.get_file_from_latest_version(bundle_name=case_id, tags=tags),
            )
        return ScoutCustomCaseReportTags.MULTIQC, self.housekeeper.get_file_from_latest_version(
            bundle_name=case_id, tags=tags
        )

    def get_fusion_report(self, case_id: str, research: bool) -> File | None:
        """Return a fusion report for a case in housekeeper."""

        tags = {AnalysisTag.FUSION}
        if research:
            tags.add(AnalysisTag.RESEARCH)
        else:
            tags.add(AnalysisTag.CLINICAL)

        return self.housekeeper.get_file_from_latest_version(bundle_name=case_id, tags=tags)

    def get_rna_delivery_report(self, case_id: str) -> File | None:
        """Return a RNA report for a case in housekeeper."""

        tags = {HK_DELIVERY_REPORT_TAG}

        return self.housekeeper.get_file_from_latest_version(bundle_name=case_id, tags=tags)

    def get_splice_junctions_bed(self, case_id: str, sample_id: str) -> File | None:
        """Return a splice junctions bed file for a case in Housekeeper."""

        tags: set[str] = {AnalysisTag.JUNCTION, AnalysisTag.BED, sample_id}
        splice_junctions_bed: File | None = None
        try:
            splice_junctions_bed = self.housekeeper.get_file_from_latest_version(
                bundle_name=case_id, tags=tags
            )
        except HousekeeperBundleVersionMissingError:
            LOG.debug("Could not find bundle for case %s", case_id)

        return splice_junctions_bed

    def get_rna_coverage_bigwig(self, case_id: str, sample_id: str) -> File | None:
        """Return an RNA coverage bigwig file for a case in Housekeeper."""
        tags: set[str] = {AnalysisTag.COVERAGE, AnalysisTag.BIGWIG, sample_id}
        return self.housekeeper.get_file_from_latest_version(bundle_name=case_id, tags=tags)

    def get_rna_omics_fraser(self, case_id: str) -> File | None:
        """Return an fraser file for a case in Housekeeper."""
        tags: set[str] = {AnalysisTag.FRASER, case_id, AnalysisTag.CLINICAL}
        return self.housekeeper.get_file_from_latest_version(bundle_name=case_id, tags=tags)

    def get_rna_omics_outrider(self, case_id: str) -> File | None:
        """Return an outrider file for a case in Housekeeper."""
        tags: set[str] = {AnalysisTag.OUTRIDER, case_id, AnalysisTag.CLINICAL}
        return self.housekeeper.get_file_from_latest_version(bundle_name=case_id, tags=tags)

    def get_rna_alignment_cram(self, case_id: str, sample_id: str) -> File | None:
        """Return an RNA alignment CRAM file for a case in Housekeeper."""
        tags: set[str] = {AlignmentFileTag.CRAM, sample_id}
        rna_alignment_cram: File | None = None
        try:
            rna_alignment_cram = self.housekeeper.get_file_from_latest_version(
                bundle_name=case_id, tags=tags
            )
        except HousekeeperBundleVersionMissingError:
            LOG.warning(f"Could not find bundle for {case_id}")
        return rna_alignment_cram

    def upload_rna_alignment_file(self, case_id: str, dry_run: bool) -> None:
        """Upload RNA alignment file to Scout."""
        rna_case: Case = self.status_db.get_case_by_internal_id(case_id)
        rna_dna_collections: list[RNADNACollection] = (
            self.status_db.get_related_dna_cases_with_samples(rna_case)
        )
        for rna_dna_collection in rna_dna_collections:
            rna_sample_internal_id: str = rna_dna_collection.rna_sample_id
            dna_sample_name: str = rna_dna_collection.dna_sample_name
            rna_alignment_cram: File | None = self.get_rna_alignment_cram(
                case_id=case_id, sample_id=rna_sample_internal_id
            )
            if not rna_alignment_cram:
                raise FileNotFoundError(
                    f"No RNA alignment CRAM file was found in Housekeeper for {rna_sample_internal_id}"
                )
            LOG.debug(f"RNA alignment CRAM file {rna_alignment_cram.path} found")
            for dna_case_id in rna_dna_collection.dna_case_ids:
                LOG.info(
                    f"Uploading RNA alignment CRAM file for sample {dna_sample_name} to case {dna_case_id}"
                )
                if dry_run:
                    continue
                self.scout_api.upload_rna_alignment_file(
                    case_id=dna_case_id,
                    customer_sample_id=dna_sample_name,
                    file_path=rna_alignment_cram.full_path,
                )
        for upload_statement in self.get_rna_alignment_file_upload_summary(rna_dna_collections):
            LOG.info(upload_statement)
        LOG.info("Upload RNA alignment CRAM file finished!")

    def upload_fusion_report_to_scout(
        self, dry_run: bool, case_id: str, research: bool = False
    ) -> None:
        """Upload fusion report file for a case to Scout."""

        report_type: str = "Research" if research else "Clinical"

        fusion_report: File | None = self.get_fusion_report(case_id, research)
        if not fusion_report:
            raise FileNotFoundError(
                f"{report_type} fusion report was not found in Housekeeper for {case_id}."
            )

        LOG.info(f"{report_type} fusion report {fusion_report.path} found")

        related_dna_cases: set[str] = self.get_related_uploaded_dna_cases(case_id)
        if not related_dna_cases:
            raise CgDataError("No connected DNA case found.")

        for dna_case_id in related_dna_cases:
            LOG.info(f"Uploading {report_type} fusion report to Scout for case {dna_case_id}.")

            if dry_run:
                continue
            self.scout_api.upload_fusion_report(
                case_id=dna_case_id,
                report_path=fusion_report.full_path,
                research=research,
            )
            LOG.info(f"Uploaded {report_type} fusion report.")

        LOG.info(f"Upload {report_type} fusion report finished!")

    def upload_rna_delivery_report_to_scout(self, dry_run: bool, case_id: str) -> None:
        """Upload rna delivery report file for a case to Scout."""

        rna_delivery_report: File | None = self.get_rna_delivery_report(case_id)
        if not rna_delivery_report:
            raise FileNotFoundError(
                f"Rna delivery report was not found in Housekeeper for {case_id}."
            )

        LOG.info(f"Rna delivery report {rna_delivery_report.path} found")

        related_dna_cases: set[str] = self.get_related_uploaded_dna_cases(case_id)
        if not related_dna_cases:
            raise CgDataError("No connected DNA case has been uploaded.")

        for dna_case_id in related_dna_cases:
            LOG.debug(f"Uploading rna delivery report to Scout for case {dna_case_id}.")

            if dry_run:
                LOG.debug(
                    f"Dry run - Would have uploaded rna delivery report to Scout for case {dna_case_id}."
                )
                continue
            self.scout_api.upload_rna_delivery_report(
                case_id=dna_case_id,
                report_path=rna_delivery_report.full_path,
            )
            LOG.debug(f"Uploaded rna delivery report for {dna_case_id}.")

        LOG.info(f"Upload rna delivery report finished for case {case_id}!")

    def upload_rna_report_to_dna_case_in_scout(
        self,
        dry_run: bool,
        report_type: str,
        report_file: File,
        rna_case_id: str,
    ) -> None:
        """Upload report file to DNA cases related to an RNA case in Scout."""
        LOG.info(f"Finding DNA cases related to RNA case {rna_case_id}")

        related_dna_cases: set[str] = self.get_related_uploaded_dna_cases(rna_case_id)
        if not related_dna_cases:
            raise CgDataError("No connected DNA case has been uploaded.")
        for dna_case_id in related_dna_cases:
            LOG.info(f"Running upload of report to DNA case {dna_case_id}.")
            self.upload_report_to_scout(
                dry_run=dry_run,
                report_type=report_type,
                report_file=report_file,
                case_id=dna_case_id,
            )

    def upload_report_to_scout(
        self,
        dry_run: bool,
        case_id: str,
        report_type: str,
        report_file: File,
    ) -> None:
        """Upload report file for a case to Scout."""

        LOG.info(f"Uploading {report_type} report to Scout for case {case_id}.")

        if dry_run:
            LOG.info(f"Would have uploaded {report_type} report.")
            return
        self.scout_api.upload_report(
            case_id=case_id,
            report_path=report_file.full_path,
            report_type=report_type,
        )
        LOG.info(f"Uploaded {report_type} report.")
        LOG.info(f"Upload {report_type} report finished!")

    def upload_rna_coverage_bigwig_to_scout(self, case_id: str, dry_run: bool) -> None:
        """Upload rna_coverage_bigwig file for a case to Scout."""

        status_db: Store = self.status_db
        rna_case = status_db.get_case_by_internal_id(case_id)
        rna_dna_collections: list[RNADNACollection] = (
            self.status_db.get_related_dna_cases_with_samples(rna_case)
        )
        for rna_dna_collection in rna_dna_collections:
            rna_sample_internal_id: str = rna_dna_collection.rna_sample_id
            dna_sample_name: str = rna_dna_collection.dna_sample_name
            rna_coverage_bigwig: File | None = self.get_rna_coverage_bigwig(
                case_id=case_id, sample_id=rna_sample_internal_id
            )

            if not rna_coverage_bigwig:
                raise FileNotFoundError(
                    f"No RNA coverage bigwig file was found in housekeeper for {rna_sample_internal_id}."
                )

            LOG.debug(f"RNA coverage bigwig file {rna_coverage_bigwig.path} found.")
            for dna_case_id in rna_dna_collection.dna_case_ids:
                LOG.info(
                    f"Uploading RNA coverage bigwig file for sample {dna_sample_name} "
                    f"in case {dna_case_id} in Scout."
                )

                if dry_run:
                    continue

                self.scout_api.upload_rna_coverage_bigwig(
                    file_path=rna_coverage_bigwig.full_path,
                    case_id=dna_case_id,
                    customer_sample_id=dna_sample_name,
                )
        for upload_statement in self.get_rna_bigwig_coverage_upload_summary(rna_dna_collections):
            LOG.info(upload_statement)
        LOG.info("Upload RNA coverage bigwig file finished!")

    def upload_omics_sample_id_to_scout(
        self, dry_run: bool, rna_dna_collections: list[RNADNACollection]
    ) -> None:
        for rna_dna_collection in rna_dna_collections:
            rna_sample_internal_id: str = rna_dna_collection.rna_sample_id
            dna_sample_name: str = rna_dna_collection.dna_sample_name
            for dna_case_id in rna_dna_collection.dna_case_ids:
                LOG.info(
                    f"Uploading omics sample id for sample {dna_sample_name} "
                    f"in case {dna_case_id} in Scout."
                )
                if dry_run:
                    continue
                self.scout_api.upload_omics_sample_id(
                    dna_case_id=dna_case_id,
                    customer_sample_id=dna_sample_name,
                    rna_sample_internal_id=rna_sample_internal_id,
                )

    def upload_rna_fraser_outrider_to_scout(
        self,
        dry_run: bool,
        case_id: str,
        rna_dna_collections: list[RNADNACollection],
    ) -> None:
        """Upload omics fraser and outrider file for a case to Scout."""
        status_db: Store = self.status_db
        for rna_dna_collection in rna_dna_collections:
            dna_sample_name: str = rna_dna_collection.dna_sample_name
            rna_fraser: File | None = self.get_rna_omics_fraser(case_id)
            rna_outrider: File | None = self.get_rna_omics_outrider(case_id)
            for dna_case_id in rna_dna_collection.dna_case_ids:
                LOG.info(
                    f"Uploading RNA fraser and outrider files for sample {dna_sample_name} "
                    f"in case {dna_case_id} in Scout."
                )
                customer_case = status_db.get_case_by_internal_id(dna_case_id)
                if dry_run:
                    continue
                self.scout_api.upload_rna_fraser_outrider(
                    fraser_file_path=rna_fraser.full_path,
                    outrider_file_path=rna_outrider.full_path,
                    case_id=dna_case_id,
                    customer_case_name=customer_case.name,
                    cust_id=customer_case.customer.internal_id,
                )
        for upload_statement in self.get_rna_fraser_outrider_upload_summary(rna_dna_collections):
            LOG.info(upload_statement)
        LOG.info("Upload RNA fraser and outrider file finished!")

    def upload_rna_genome_build_to_scout(
        self,
        dry_run: bool,
        rna_dna_collections: list[RNADNACollection],
    ) -> None:
        """Upload RNA genome built for a RNA/DNA case to Scout."""
        status_db: Store = self.status_db
        for rna_dna_collection in rna_dna_collections:
            dna_sample_name: str = rna_dna_collection.dna_sample_name
            for dna_case_id in rna_dna_collection.dna_case_ids:
                LOG.info(
                    f"Uploading RNA genome built for sample {dna_sample_name} "
                    f"in case {dna_case_id} in Scout."
                )
                customer_case = status_db.get_case_by_internal_id(dna_case_id)

                if dry_run:
                    continue

                self.scout_api.upload_rna_genome_build(
                    case_id=dna_case_id,
                    customer_case_name=customer_case.name,
                    cust_id=customer_case.customer.internal_id,
                    rna_genome_build=GenomeBuild.hg38,
                )

        for upload_statement in self.get_rna_genome_build_upload_summary(rna_dna_collections):
            LOG.info(upload_statement)
        LOG.info("Upload RNA fraser and outrider file finished!")

    def load_rna_variant_outlier_to_scout(
        self, dry_run: bool, rna_dna_collections: list[RNADNACollection]
    ) -> None:
        """Upload RNA genome built for a RNA/DNA case to Scout."""
        for rna_dna_collection in rna_dna_collections:
            dna_sample_name: str = rna_dna_collection.dna_sample_name
            for dna_case_id in rna_dna_collection.dna_case_ids:
                LOG.info(
                    f"Loading RNA variants for sample {dna_sample_name} "
                    f"in case {dna_case_id} in Scout."
                )

                if dry_run:
                    continue

                self.scout_api.load_variant_outlier(
                    case_id=dna_case_id,
                )

        for upload_statement in self.get_variant_load_summary(rna_dna_collections):
            LOG.info(upload_statement)
        LOG.info("Load RNA variants finished!")

    def upload_splice_junctions_bed_to_scout(self, dry_run: bool, case_id: str) -> None:
        """Upload splice_junctions_bed file for a case to Scout."""

        status_db: Store = self.status_db
        rna_case: Case = status_db.get_case_by_internal_id(case_id)

        rna_dna_collections: list[RNADNACollection] = (
            self.status_db.get_related_dna_cases_with_samples(rna_case)
        )
        for rna_dna_collection in rna_dna_collections:
            rna_sample_internal_id: str = rna_dna_collection.rna_sample_id
            dna_sample_name: str = rna_dna_collection.dna_sample_name
            splice_junctions_bed: File | None = self.get_splice_junctions_bed(
                case_id=case_id, sample_id=rna_sample_internal_id
            )

            if not splice_junctions_bed:
                raise FileNotFoundError(
                    f"No splice junctions bed file was found in Housekeeper for {rna_sample_internal_id}."
                )

            LOG.debug(f"Splice junctions bed file {splice_junctions_bed.path} found")
            for dna_case_id in rna_dna_collection.dna_case_ids:
                LOG.info(
                    f"Uploading splice junctions bed file for sample {dna_sample_name} "
                    f"in case {dna_case_id} in Scout."
                )

                if dry_run:
                    continue

                self.scout_api.upload_splice_junctions_bed(
                    file_path=splice_junctions_bed.full_path,
                    case_id=dna_case_id,
                    customer_sample_id=dna_sample_name,
                )
        for upload_statement in self.get_rna_splice_junctions_upload_summary(rna_dna_collections):
            LOG.info(upload_statement)
        LOG.info("Upload splice junctions bed file finished!")

    @staticmethod
    def get_rna_alignment_file_upload_summary(
        rna_dna_collections: list[RNADNACollection],
    ) -> list[str]:
        upload_summary: list[str] = []
        for rna_dna_collection in rna_dna_collections:
            upload_summary.extend(
                f"Uploaded RNA alignment CRAM file for sample {rna_dna_collection.dna_sample_name} in case {dna_case}"
                for dna_case in rna_dna_collection.dna_case_ids
            )
        return upload_summary

    @staticmethod
    def get_rna_splice_junctions_upload_summary(
        rna_dna_collections: list[RNADNACollection],
    ) -> list[str]:
        upload_summary: list[str] = []
        for rna_dna_collection in rna_dna_collections:
            upload_summary.extend(
                f"Uploaded splice junctions bed file for sample {rna_dna_collection.dna_sample_name} in case {dna_case}."
                for dna_case in rna_dna_collection.dna_case_ids
            )
        return upload_summary

    @staticmethod
    def get_rna_bigwig_coverage_upload_summary(
        rna_dna_collections: list[RNADNACollection],
    ) -> list[str]:
        upload_summary: list[str] = []
        for rna_dna_collection in rna_dna_collections:
            upload_summary.extend(
                f"Uploaded bigwig coverage file for sample {rna_dna_collection.dna_sample_name} in case {dna_case}."
                for dna_case in rna_dna_collection.dna_case_ids
            )
        return upload_summary

    @staticmethod
    def get_rna_fraser_outrider_upload_summary(
        rna_dna_collections: list[RNADNACollection],
    ) -> list[str]:
        upload_summary: list[str] = []
        for rna_dna_collection in rna_dna_collections:
            upload_summary.extend(
                f"Uploaded fraser and outrider files for sample {rna_dna_collection.dna_sample_name} in case {dna_case}."
                for dna_case in rna_dna_collection.dna_case_ids
            )
        return upload_summary

    @staticmethod
    def get_rna_genome_build_upload_summary(
        rna_dna_collections: list[RNADNACollection],
    ) -> list[str]:
        upload_summary: list[str] = []
        for rna_dna_collection in rna_dna_collections:
            upload_summary.extend(
                f"Uploaded RNA genome build file for sample {rna_dna_collection.dna_sample_name} in case {dna_case}."
                for dna_case in rna_dna_collection.dna_case_ids
            )
        return upload_summary

    @staticmethod
    def get_variant_load_summary(
        rna_dna_collections: list[RNADNACollection],
    ) -> list[str]:
        upload_summary: list[str] = []
        for rna_dna_collection in rna_dna_collections:
            upload_summary.extend(
                f"Loaded variant outlier for sample {rna_dna_collection.dna_sample_name} in case {dna_case}."
                for dna_case in rna_dna_collection.dna_case_ids
            )
        return upload_summary

    def upload_rna_junctions_to_scout(self, dry_run: bool, case_id: str) -> None:
        """Upload RNA junctions splice files to Scout."""
        self.upload_splice_junctions_bed_to_scout(dry_run=dry_run, case_id=case_id)
        self.upload_rna_coverage_bigwig_to_scout(case_id=case_id, dry_run=dry_run)

    def upload_rna_omics_to_scout(self, dry_run: bool, case_id: str) -> None:
        """Upload RNA omics files to Scout."""
        status_db: Store = self.status_db
        rna_case = status_db.get_case_by_internal_id(case_id)
        rna_dna_collections: list[RNADNACollection] = (
            self.status_db.get_related_dna_cases_with_samples(rna_case)
        )
        self.upload_omics_sample_id_to_scout(
            dry_run=dry_run, rna_dna_collections=rna_dna_collections
        )
        self.upload_rna_genome_build_to_scout(
            dry_run=dry_run,
            rna_dna_collections=rna_dna_collections,
        )
        if self._has_rna_outlier_variants(case_id):
            self.upload_rna_fraser_outrider_to_scout(
                dry_run=dry_run,
                case_id=case_id,
                rna_dna_collections=rna_dna_collections,
            )

            self.load_rna_variant_outlier_to_scout(
                dry_run=dry_run, rna_dna_collections=rna_dna_collections
            )

    def _has_rna_outlier_variants(self, case_id: str) -> bool:
        rna_fraser: File | None = self.get_rna_omics_fraser(case_id)
        rna_outrider: File | None = self.get_rna_omics_outrider(case_id)
        return bool(rna_fraser or rna_outrider)

    def get_config_builder(self, analysis: Analysis) -> ScoutConfigBuilder:
        config_builders = {
            Workflow.BALSAMIC: BalsamicConfigBuilder(
                lims_api=self.lims,
            ),
            Workflow.BALSAMIC_UMI: BalsamicUmiConfigBuilder(
                lims_api=self.lims,
            ),
            Workflow.MIP_DNA: MipConfigBuilder(
                mip_analysis_api=self.analysis_api,
                lims_api=self.lims,
                madeline_api=self.madeline_api,
            ),
            Workflow.MIP_RNA: MipConfigBuilder(
                mip_analysis_api=self.analysis_api,
                lims_api=self.lims,
                madeline_api=self.madeline_api,
            ),
            Workflow.NALLO: NalloConfigBuilder(
                nallo_analysis_api=self.analysis_api,
                lims_api=self.lims,
                madeline_api=self.madeline_api,
            ),
            Workflow.RAREDISEASE: RarediseaseConfigBuilder(
                raredisease_analysis_api=self.raredisease_analysis_api,
                lims_api=self.lims,
                madeline_api=self.madeline_api,
            ),
            Workflow.RNAFUSION: RnafusionConfigBuilder(
                lims_api=self.lims,
            ),
        }

        return config_builders[analysis.workflow]

    def get_related_uploaded_dna_cases(self, rna_case_id: str) -> set[str]:
        """Returns all uploaded DNA cases related to the specified RNA case."""
        rna_case: Case = self.status_db.get_case_by_internal_id(rna_case_id)
        dna_cases: list[Case] = self.status_db.get_uploaded_related_dna_cases(rna_case)
        return {dna_case.internal_id for dna_case in dna_cases}
