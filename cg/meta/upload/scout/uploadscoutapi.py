"""File includes api to uploading data into Scout."""

import logging
from pathlib import Path
from typing import List, Optional, Set, Tuple

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.madeline.api import MadelineAPI
from cg.apps.scout.scoutapi import ScoutAPI
from cg.constants import HK_MULTIQC_HTML_TAG, Pipeline
from cg.constants.constants import FileFormat, PrepCategory
from cg.constants.scout_upload import ScoutCustomCaseReportTags
from cg.exc import CgDataError, HousekeeperBundleVersionMissingError
from cg.io.controller import WriteFile
from cg.meta.upload.scout.balsamic_config_builder import BalsamicConfigBuilder
from cg.meta.upload.scout.balsamic_umi_config_builder import BalsamicUmiConfigBuilder
from cg.meta.upload.scout.mip_config_builder import MipConfigBuilder
from cg.meta.upload.scout.rnafusion_config_builder import RnafusionConfigBuilder
from cg.meta.upload.scout.scout_config_builder import ScoutConfigBuilder
from cg.meta.workflow.analysis import AnalysisAPI
from cg.models.scout.scout_load_config import ScoutLoadConfig
from cg.store import Store
from cg.store.models import Analysis, Customer, Family, Sample
from housekeeper.store.models import File, Version
from pydantic.v1.dataclasses import dataclass

LOG = logging.getLogger(__name__)


@dataclass
class RNADNACollection:
    """Contains the id for an RNA sample, the name of its connected DNA sample,
    and a list of connected, uploaded DNA cases."""

    rna_sample_internal_id: str
    dna_sample_name: str
    dna_case_ids: List[str]


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
        self.mip_analysis_api = analysis_api
        self.lims = lims_api
        self.status_db = status_db

    def generate_config(self, analysis_obj: Analysis) -> ScoutLoadConfig:
        """Fetch data about an analysis to load Scout."""
        LOG.info("Generate scout load config")

        # Fetch last version from housekeeper
        # This should be safe since analyses are only added if data is analysed
        hk_version_obj: Version = self.housekeeper.last_version(analysis_obj.family.internal_id)
        LOG.debug("Found housekeeper version %s", hk_version_obj.id)

        load_config: ScoutLoadConfig
        LOG.info("Found pipeline %s", analysis_obj.pipeline)
        config_builder = self.get_config_builder(analysis=analysis_obj, hk_version=hk_version_obj)

        config_builder.build_load_config()

        return config_builder.load_config

    @staticmethod
    def get_load_config_tag() -> str:
        """Get the Housekeeper tag for a Scout load config."""
        return "scout-load-config"

    @staticmethod
    def save_config_file(upload_config: ScoutLoadConfig, file_path: Path) -> None:
        """Save a Scout load config file to the supplied file path."""

        LOG.info(f"Save Scout load config to {file_path.as_posix()}.")
        WriteFile.write_file_from_content(
            content=upload_config.dict(exclude_none=True),
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
        uploaded_config_file: Optional[File] = self.housekeeper.get_latest_file_from_version(
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
        self, case_id: str, pipeline: Pipeline
    ) -> Tuple[ScoutCustomCaseReportTags, Optional[File]]:
        """Return a multiqc report for a case in Housekeeper."""
        if pipeline == Pipeline.MIP_RNA:
            return (
                ScoutCustomCaseReportTags.MULTIQC_RNA,
                self.housekeeper.files(bundle=case_id, tags=HK_MULTIQC_HTML_TAG).first(),
            )
        return (
            ScoutCustomCaseReportTags.MULTIQC,
            self.housekeeper.files(bundle=case_id, tags=HK_MULTIQC_HTML_TAG).first(),
        )

    def get_fusion_report(self, case_id: str, research: bool) -> Optional[File]:
        """Return a fusion report for a case in housekeeper."""

        tags = {"fusion"}
        if research:
            tags.add("research")
        else:
            tags.add("clinical")

        return self.housekeeper.get_file_from_latest_version(bundle_name=case_id, tags=tags)

    def get_splice_junctions_bed(self, case_id: str, sample_id: str) -> Optional[File]:
        """Return a splice junctions bed file for a case in Housekeeper."""

        tags: Set[str] = {"junction", "bed", sample_id}
        splice_junctions_bed: Optional[File] = None
        try:
            splice_junctions_bed = self.housekeeper.get_file_from_latest_version(
                bundle_name=case_id, tags=tags
            )
        except HousekeeperBundleVersionMissingError:
            LOG.debug("Could not find bundle for case %s", case_id)

        return splice_junctions_bed

    def get_rna_coverage_bigwig(self, case_id: str, sample_id: str) -> Optional[File]:
        """Return an RNA coverage bigwig file for a case in Housekeeper."""

        tags: Set[str] = {"coverage", "bigwig", sample_id}

        return self.housekeeper.get_file_from_latest_version(bundle_name=case_id, tags=tags)

    def get_unique_dna_cases_related_to_rna_case(self, case_id: str) -> Set[str]:
        """Return a set of unique DNA cases related to an RNA case."""
        case: Family = self.status_db.get_case_by_internal_id(case_id)
        rna_dna_collections: List[RNADNACollection] = self.create_rna_dna_collections(case)
        unique_dna_cases_related_to_rna_case: Set[str] = set()
        for rna_dna_collection in rna_dna_collections:
            unique_dna_cases_related_to_rna_case.update(rna_dna_collection.dna_case_ids)
        return unique_dna_cases_related_to_rna_case

    def upload_fusion_report_to_scout(
        self, dry_run: bool, case_id: str, research: bool = False
    ) -> None:
        """Upload fusion report file for a case to Scout."""

        report_type: str = "Research" if research else "Clinical"

        fusion_report: Optional[File] = self.get_fusion_report(case_id, research)
        if fusion_report is None:
            raise FileNotFoundError(
                f"{report_type} fusion report was not found in Housekeeper for {case_id}."
            )

        LOG.info(f"{report_type} fusion report {fusion_report.path} found")

        related_dna_cases: Set[str] = self.get_related_uploaded_dna_cases(case_id)
        if not related_dna_cases:
            raise CgDataError("No connected DNA case has been uploaded.")

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

    def upload_rna_report_to_dna_case_in_scout(
        self,
        dry_run: bool,
        report_type: str,
        report_file: File,
        rna_case_id: str,
    ) -> None:
        """Upload report file to DNA cases related to an RNA case in Scout."""
        LOG.info(f"Finding DNA cases related to RNA case {rna_case_id}")

        related_dna_cases: Set[str] = self.get_related_uploaded_dna_cases(rna_case_id)
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
        rna_dna_collections: List[RNADNACollection] = self.create_rna_dna_collections(rna_case)
        for rna_dna_collection in rna_dna_collections:
            rna_sample_internal_id: str = rna_dna_collection.rna_sample_internal_id
            dna_sample_name: str = rna_dna_collection.dna_sample_name
            rna_coverage_bigwig: Optional[File] = self.get_rna_coverage_bigwig(
                case_id=case_id, sample_id=rna_sample_internal_id
            )

            if rna_coverage_bigwig is None:
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

    def upload_splice_junctions_bed_to_scout(self, dry_run: bool, case_id: str) -> None:
        """Upload splice_junctions_bed file for a case to Scout."""

        status_db: Store = self.status_db
        rna_case: Family = status_db.get_case_by_internal_id(case_id)

        rna_dna_collections: List[RNADNACollection] = self.create_rna_dna_collections(rna_case)
        for rna_dna_collection in rna_dna_collections:
            rna_sample_internal_id: str = rna_dna_collection.rna_sample_internal_id
            dna_sample_name: str = rna_dna_collection.dna_sample_name
            splice_junctions_bed: Optional[File] = self.get_splice_junctions_bed(
                case_id=case_id, sample_id=rna_sample_internal_id
            )

            if splice_junctions_bed is None:
                raise FileNotFoundError(
                    f"No splice junctions bed file was found in Housekeeper for {rna_sample_internal_id}."
                )

            LOG.debug(f"Splice junctions bed file {splice_junctions_bed.path} found")
            dna_sample_id: str
            dna_cases: List[str]
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
    def get_rna_splice_junctions_upload_summary(
        rna_dna_collections: List[RNADNACollection],
    ) -> List[str]:
        upload_summary: List[str] = []
        for rna_dna_collection in rna_dna_collections:
            upload_summary.extend(
                f"Uploaded splice junctions bed file for sample {rna_dna_collection.dna_sample_name} in case {dna_case}."
                for dna_case in rna_dna_collection.dna_case_ids
            )
        return upload_summary

    @staticmethod
    def get_rna_bigwig_coverage_upload_summary(
        rna_dna_collections: List[RNADNACollection],
    ) -> List[str]:
        upload_summary: List[str] = []
        for rna_dna_collection in rna_dna_collections:
            upload_summary.extend(
                f"Uploaded bigwig coverage file for sample {rna_dna_collection.dna_sample_name} in case {dna_case}."
                for dna_case in rna_dna_collection.dna_case_ids
            )
        return upload_summary

    def upload_rna_junctions_to_scout(self, dry_run: bool, case_id: str) -> None:
        """Upload RNA junctions splice files to Scout."""
        self.upload_splice_junctions_bed_to_scout(dry_run=dry_run, case_id=case_id)
        self.upload_rna_coverage_bigwig_to_scout(case_id=case_id, dry_run=dry_run)

    def get_config_builder(self, analysis, hk_version) -> ScoutConfigBuilder:
        config_builders = {
            Pipeline.BALSAMIC: BalsamicConfigBuilder(
                hk_version_obj=hk_version, analysis_obj=analysis, lims_api=self.lims
            ),
            Pipeline.BALSAMIC_UMI: BalsamicUmiConfigBuilder(
                hk_version_obj=hk_version, analysis_obj=analysis, lims_api=self.lims
            ),
            Pipeline.MIP_DNA: MipConfigBuilder(
                hk_version_obj=hk_version,
                analysis_obj=analysis,
                mip_analysis_api=self.mip_analysis_api,
                lims_api=self.lims,
                madeline_api=self.madeline_api,
            ),
            Pipeline.MIP_RNA: MipConfigBuilder(
                hk_version_obj=hk_version,
                analysis_obj=analysis,
                mip_analysis_api=self.mip_analysis_api,
                lims_api=self.lims,
                madeline_api=self.madeline_api,
            ),
            Pipeline.RNAFUSION: RnafusionConfigBuilder(
                hk_version_obj=hk_version, analysis_obj=analysis, lims_api=self.lims
            ),
        }

        return config_builders[analysis.pipeline]

    def create_rna_dna_collections(self, rna_case: Family) -> List[RNADNACollection]:
        return [self.create_rna_dna_collection(link.sample) for link in rna_case.links]

    def create_rna_dna_collection(self, rna_sample: Sample) -> RNADNACollection:
        """Creates a collection containing the given RNA sample id, its related DNA sample name, and
        a list of ids for the DNA cases connected to the DNA sample."""
        if not rna_sample.subject_id:
            raise CgDataError(
                f"Failed to link RNA sample {rna_sample.internal_id} to DNA samples - subject_id field is empty."
            )

        collaborators: Set[Customer] = rna_sample.customer.collaborators
        subject_id_samples: List[
            Sample
        ] = self.status_db.get_samples_by_customer_id_list_and_subject_id_and_is_tumour(
            customer_ids=[customer.id for customer in collaborators],
            subject_id=rna_sample.subject_id,
            is_tumour=rna_sample.is_tumour,
        )

        subject_id_dna_samples: List[Sample] = self._get_application_prep_category(
            subject_id_samples
        )

        if len(subject_id_dna_samples) != 1:
            raise CgDataError(
                f"Failed to upload files for RNA case: unexpected number of DNA sample matches for subject_id: "
                f"{rna_sample.subject_id}. Number of matches: {len(subject_id_dna_samples)} "
            )
        dna_sample: Sample = subject_id_dna_samples[0]
        dna_cases: List[str] = self._dna_cases_related_to_dna_sample(
            dna_sample=dna_sample, collaborators=collaborators
        )
        return RNADNACollection(
            rna_sample_internal_id=rna_sample.internal_id,
            dna_sample_name=dna_sample.name,
            dna_case_ids=dna_cases,
        )

    def _dna_cases_related_to_dna_sample(
        self, dna_sample: Sample, collaborators: Set[Customer]
    ) -> List[str]:
        """Maps a list of uploaded DNA cases linked to DNA sample."""
        potential_cases_related_to_dna_sample: List[Family] = [
            dna_sample_family_relation.family for dna_sample_family_relation in dna_sample.links
        ]
        return self.filter_cases_related_to_dna_sample(
            list_of_dna_cases=potential_cases_related_to_dna_sample, collaborators=collaborators
        )

    @staticmethod
    def filter_cases_related_to_dna_sample(
        list_of_dna_cases: List[Family], collaborators: Set[Customer]
    ) -> List[str]:
        """Filters the given list of DNA samples and returns a subset of uploaded cases ordered by customers in the
        specified list of collaborators and within the correct pipeline."""
        filtered_dna_cases: List[str] = []
        for case in list_of_dna_cases:
            if (
                case.data_analysis
                in [
                    Pipeline.MIP_DNA,
                    Pipeline.BALSAMIC,
                    Pipeline.BALSAMIC_UMI,
                ]
                and case.customer in collaborators
            ):
                if not case.is_uploaded:
                    LOG.warning(
                        f"Cannot upload RNA report to DNA case {case.internal_id}. DNA case is not uploaded."
                    )
                filtered_dna_cases.append(case.internal_id)
        return filtered_dna_cases

    @staticmethod
    def _get_application_prep_category(
        subject_id_samples: List[Sample],
    ) -> List[Optional[Sample]]:
        """Filter a models Sample list, returning DNA samples selected on their preparation category."""
        subject_id_dna_samples: List[Optional[Sample]] = [
            sample
            for sample in subject_id_samples
            if sample.prep_category
            in [
                PrepCategory.WHOLE_GENOME_SEQUENCING.value,
                PrepCategory.TARGETED_GENOME_SEQUENCING.value,
                PrepCategory.WHOLE_EXOME_SEQUENCING.value,
            ]
        ]

        return subject_id_dna_samples

    def get_related_uploaded_dna_cases(self, rna_case_id: str) -> Set[str]:
        """Returns all uploaded DNA cases related to the specified RNA case."""
        unique_dna_case_ids: Set[str] = self.get_unique_dna_cases_related_to_rna_case(rna_case_id)

        uploaded_dna_cases: Set[str] = set()
        for dna_case_id in unique_dna_case_ids:
            if self.status_db.get_case_by_internal_id(dna_case_id).is_uploaded:
                uploaded_dna_cases.add(dna_case_id)
            else:
                LOG.warning(f"Related DNA case {dna_case_id} has not been completed.")
        return uploaded_dna_cases
