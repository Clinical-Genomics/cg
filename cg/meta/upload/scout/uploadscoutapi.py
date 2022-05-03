"""File includes api to uploading data into Scout"""

import logging
from pathlib import Path
from typing import Optional, Set

import yaml
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.madeline.api import MadelineAPI
from cg.apps.scout.scoutapi import ScoutAPI
from cg.constants import Pipeline
from cg.exc import HousekeeperVersionMissingError, ScoutUploadError, CgDataError
from cg.meta.workflow.analysis import AnalysisAPI
from cg.models.scout.scout_load_config import ScoutLoadConfig
from cg.store import models, Store
from housekeeper.store import models as hk_models

from cg.meta.upload.scout.balsamic_config_builder import BalsamicConfigBuilder
from cg.meta.upload.scout.balsamic_umi_config_builder import BalsamicUmiConfigBuilder
from cg.meta.upload.scout.mip_config_builder import MipConfigBuilder
from cg.meta.upload.scout.scout_config_builder import ScoutConfigBuilder

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
        status_db: Store,
    ):
        self.housekeeper = hk_api
        self.scout = scout_api
        self.madeline_api = madeline_api
        self.mip_analysis_api = analysis_api
        self.lims = lims_api
        self.status_db = status_db

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
        config_builder = self.get_config_builder(analysis=analysis_obj, hk_version=hk_version_obj)

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
        tags = {"fusion"}
        if research:
            tags.add("research")
        else:
            tags.add("clinical")

        fusion_report: Optional[hk_models.File] = self.housekeeper.find_file_in_latest_version(
            case_id=case_id, tags=tags
        )

        return fusion_report

    def get_splice_junctions_bed(self, case_id: str, sample_id: str) -> Optional[hk_models.File]:
        """Get a splice junctions bed file for case in housekeeper

        Args:
            case_id     (string):       Case identifier
            sample_id   (string):       Sample identifier
        Returns:
            File in housekeeper (Optional[hk_models.File])
        """

        # This command can be executed as:
        # ´housekeeper get file -V --tag junction --tag bed <sample_id>´
        tags: {str} = {"junction", "bed", sample_id}
        splice_junctions_bed: Optional[hk_models.File]
        try:
            splice_junctions_bed = self.housekeeper.find_file_in_latest_version(
                case_id=case_id, tags=tags
            )
        except HousekeeperVersionMissingError:
            LOG.debug("Could not find bundle for case %s", case_id)

        return splice_junctions_bed

    def get_rna_coverage_bigwig(self, case_id: str, sample_id: str) -> Optional[hk_models.File]:
        """Get a rna coverage bigwig file for case in housekeeper

        Args:
            case_id     (string):       Case identifier
            sample_id   (string):       Sample identifier
        Returns:
            File in housekeeper (Optional[hk_models.File])
        """

        # This command can be executed as:
        # ´housekeeper get file -V --tag coverage --tag bigwig <sample_id>´
        tags: {str} = {"coverage", "bigwig", sample_id}

        rna_coverage_bigwig: Optional[
            hk_models.File
        ] = self.housekeeper.find_file_in_latest_version(case_id=case_id, tags=tags)

        return rna_coverage_bigwig

    def upload_fusion_report_to_scout(
        self, dry_run: bool, case_id: str, research: bool = False, update: bool = False
    ) -> None:
        """Upload fusion report file for a case to Scout.
        This can also be run as
        `housekeeper get file -V --tag fusion --tag pdf --tag clinical/research <case_id>`
        `scout load gene-fusion-report [-r] <case_id> <path/to/research_gene_fusion_report.pdf>`

        Args:
            dry_run     (bool):         Skip uploading
            case_id     (string):       Case identifier
            research    (bool):         Upload research report instead of clinical
            update      (bool):         Overwrite existing report
        Returns:
            Nothing
        """

        scout_api: ScoutAPI = self.scout
        status_db: Store = self.status_db
        report_type: str = "Research" if research else "Clinical"

        fusion_report: Optional[hk_models.File] = self.get_fusion_report(case_id, research)
        if fusion_report is None:
            raise FileNotFoundError(
                f"{report_type} fusion report was not found in housekeeper for {case_id}"
            )

        LOG.info(f"{report_type} fusion report %s found", fusion_report.path)

        rna_case = status_db.family(case_id)
        upload_dna_cases: Set[models.Family] = set()
        for link in rna_case.links:
            rna_sample: models.Sample = link.sample
            if not rna_sample.subject_id:
                raise CgDataError(
                    "Failed on RNA sample %s since it is not linked to anything via subject_id"
                    % rna_sample.internal_id,
                )

            dna_cases: [models.Family] = self.status_db.families_by_subject_id(
                customer_id=rna_sample.customer.internal_id,
                data_analyses=[Pipeline.MIP_DNA, Pipeline.BALSAMIC],
                subject_id=rna_sample.subject_id,
                is_tumour=rna_sample.is_tumour,
            )

            self._check_cases_single_connected(dna_cases, rna_sample)

            upload_dna_cases.update(dna_cases)

        if not upload_dna_cases:
            raise CgDataError(
                "Failed to upload on RNA case %s since there are no DNA cases linked to it via subject_id"
                % rna_case.internal_id,
            )

        dna_case: models.Family
        for dna_case in upload_dna_cases:
            dna_case_id: str = dna_case.internal_id

            LOG.info("Uploading %s fusion report to scout for case %s", report_type, dna_case_id)

            if dry_run:
                continue

            scout_api.upload_fusion_report(
                case_id=dna_case_id,
                report_path=fusion_report.full_path,
                research=research,
                update=update,
            )
            LOG.info("Uploaded %s fusion report", report_type)

        LOG.info("Upload %s fusion report finished!", report_type)

    @staticmethod
    def _check_cases_single_connected(
        dna_cases: [models.Family], rna_sample: models.Sample
    ) -> None:
        if not dna_cases:
            raise CgDataError(
                "Failed to upload RNA sample %s since there are no DNA samples linked to it via subject_id"
                % rna_sample.internal_id,
            )

        if len(dna_cases) > 1:
            raise CgDataError(
                "Failed to upload RNA sample %s since there are more than one DNA sample linked to it via subject_id"
                % rna_sample.internal_id,
            )

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

        scout_api: ScoutAPI = self.scout
        status_db: Store = self.status_db
        rna_case = status_db.family(case_id)

        link: models.FamilySample
        rna_coverage_bigwig: Optional[hk_models.File]
        for link in rna_case.links:
            rna_sample: models.Sample = link.sample
            if not rna_sample.subject_id:
                raise CgDataError(
                    "Failed on RNA sample %s since it is not linked to anything via subject_id"
                    % rna_sample.internal_id,
                )
            rna_sample_id: str = rna_sample.internal_id
            rna_coverage_bigwig: Optional[hk_models.File] = self.get_rna_coverage_bigwig(
                case_id=case_id, sample_id=rna_sample_id
            )

            if rna_coverage_bigwig is None:
                raise FileNotFoundError(
                    f"No RNA coverage bigwig file was found in housekeeper for {rna_sample_id}"
                )

            LOG.info(f"RNA coverage bigwig file %s found", rna_coverage_bigwig.path)

            dna_cases: [models.Family] = self.status_db.families_by_subject_id(
                customer_id=rna_sample.customer.internal_id,
                subject_id=rna_sample.subject_id,
                data_analyses=[Pipeline.MIP_DNA, Pipeline.BALSAMIC],
                is_tumour=rna_sample.is_tumour,
            )

            self._check_cases_single_connected(dna_cases, rna_sample)

            dna_case: models.Family
            for dna_case in dna_cases:
                dna_case_id: str = dna_case.internal_id
                dna_sample: models.Sample = self._get_sample(
                    case=dna_case, subject_id=rna_sample.subject_id
                )
                dna_sample_name = dna_sample.name

                LOG.info("Uploading RNA coverage bigwig file to %s in scout", dna_sample_name)

                if dry_run:
                    continue

                scout_api.upload_rna_coverage_bigwig(
                    file_path=rna_coverage_bigwig.full_path,
                    case_id=dna_case_id,
                    customer_sample_id=dna_sample_name,
                )

                LOG.info("Uploaded RNA coverage bigwig file")

        LOG.info("Upload RNA coverage bigwig file finished!")

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
        scout_api: ScoutAPI = self.scout
        status_db: Store = self.status_db
        rna_case: models.Family = status_db.family(case_id)

        link: models.FamilySample
        for link in rna_case.links:
            rna_sample = link.sample
            if not rna_sample.subject_id:
                raise CgDataError(
                    "Failed on RNA sample %s since it is not linked to anything via subject_id"
                    % rna_sample.internal_id,
                )
            rna_sample_id = rna_sample.internal_id
            splice_junctions_bed: Optional[hk_models.File] = self.get_splice_junctions_bed(
                case_id=case_id, sample_id=rna_sample_id
            )

            if splice_junctions_bed is None:
                raise FileNotFoundError(
                    f"No splice junctions bed file was found in housekeeper for {rna_sample_id}"
                )

            LOG.info(f"Splice junctions bed file %s found", splice_junctions_bed.path)

            dna_cases: [models.Family] = self.status_db.families_by_subject_id(
                customer_id=rna_sample.customer.internal_id,
                subject_id=rna_sample.subject_id,
                data_analyses=[Pipeline.MIP_DNA, Pipeline.BALSAMIC],
                is_tumour=rna_sample.is_tumour,
            )

            self._check_cases_single_connected(dna_cases, rna_sample)

            dna_case: models.Family
            for dna_case in dna_cases:
                dna_case_id: str = dna_case.internal_id
                dna_sample: models.Sample = self._get_sample(
                    case=dna_case, subject_id=rna_sample.subject_id
                )
                dna_sample_name: str = dna_sample.name

                LOG.info("Uploading splice junctions bed file for %s in scout", dna_sample_name)

                if dry_run:
                    continue

                scout_api.upload_splice_junctions_bed(
                    file_path=splice_junctions_bed.full_path,
                    case_id=dna_case_id,
                    customer_sample_id=dna_sample_name,
                )
                LOG.info("Uploaded splice junctions bed file")

        LOG.info("Upload splice junctions bed file finished!")

    def upload_rna_junctions_to_scout(self, dry_run: bool, case_id: str) -> None:
        """Upload RNA junctions splice files to Scout.

        Args:
            dry_run     (bool):         Skip uploading
            case_id     (string):       RNA case identifier
        Returns:
            Nothing
        """
        self.upload_splice_junctions_bed_to_scout(dry_run=dry_run, case_id=case_id)
        self.upload_rna_coverage_bigwig_to_scout(case_id=case_id, dry_run=dry_run)

    @staticmethod
    def _get_sample(case: models.Family, subject_id: str) -> Optional[models.Sample]:
        """Get sample of a case for a subject_id.

        Args:
            case     (models.Family):               Case
            subject_id   (str):                     Subject id to search for
        Returns:
            matching sample (models.Sample)
        """

        link: models.FamilySample
        for link in case.links:
            sample: models.Sample = link.sample
            if sample.subject_id == subject_id:
                return sample

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
        }

        return config_builders[analysis.pipeline]
