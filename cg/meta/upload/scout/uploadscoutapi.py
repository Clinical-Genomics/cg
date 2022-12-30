"""File includes api to uploading data into Scout"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, TypedDict


from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.madeline.api import MadelineAPI
from cg.apps.scout.scoutapi import ScoutAPI
from cg.constants import Pipeline
from cg.constants.constants import FileFormat
from cg.constants.constants import PrepCategory
from cg.exc import HousekeeperVersionMissingError, CgDataError
from cg.io.controller import WriteFile
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
        WriteFile.write_file_from_content(
            content=upload_config.dict(exclude_none=True),
            file_format=FileFormat.YAML,
            file_path=file_path,
        )

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
            LOG.info(f"Found config file: {uploaded_config_file}")
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

    def get_multiqc_html_report(self, case_id: str) -> Tuple[str, Optional[hk_models.File]]:
        """Get a multiqc report for case in housekeeper."""

        multiqc_tag = "multiqc-html"
        return (multiqc_tag, self.housekeeper.files(bundle=case_id, tags=[multiqc_tag]).first())

    def get_fusion_report(self, case_id: str, research: bool) -> Optional[hk_models.File]:
        """Get a fusion report for case in housekeeper."""

        tags = {"fusion"}
        if research:
            tags.add("research")
        else:
            tags.add("clinical")

        return self.housekeeper.find_file_in_latest_version(case_id=case_id, tags=tags)

    def get_splice_junctions_bed(self, case_id: str, sample_id: str) -> Optional[hk_models.File]:
        """Get a splice junctions bed file for case in housekeeper."""

        tags: Set[str] = {"junction", "bed", sample_id}
        splice_junctions_bed: Optional[hk_models.File]
        try:
            splice_junctions_bed = self.housekeeper.find_file_in_latest_version(
                case_id=case_id, tags=tags
            )
        except HousekeeperVersionMissingError:
            LOG.debug("Could not find bundle for case %s", case_id)

        return splice_junctions_bed

    def get_rna_coverage_bigwig(self, case_id: str, sample_id: str) -> Optional[hk_models.File]:
        """Get a RNA coverage bigwig file for case in housekeeper."""

        tags: Set[str] = {"coverage", "bigwig", sample_id}

        return self.housekeeper.find_file_in_latest_version(case_id=case_id, tags=tags)


    def get_unique_dna_cases_related_to_rna_case(self, case_id: str) -> Set[str]:
        """Return a set of unique dna cases related to a RNA case"""
        case_obj: models.Family = self.status_db.family(case_id)
        rna_dna_sample_case_map: Dict[str, Dict[str, List[str]]] = self.create_rna_dna_sample_case_map(rna_case=case_obj)
        dna_sample_case_dict: Dict[str, List[str]]
        unique_dna_cases_related_to_rna_case: Set[str] = set()
        for dna_sample_case_dict in rna_dna_sample_case_map:
            case_list: List[str]
            for case_list in dna_sample_case_dict.values():
                for case in case_list:
                    unique_dna_cases_related_to_rna_case.update(case)


        return {
            dna_case
            for dna_case_dict in self.create_rna_dna_sample_case_map(rna_case=case_obj).values()
            for case_list in dna_case_dict.values()
            for dna_case in case_list
        }

    def upload_fusion_report_to_scout(
        self, dry_run: bool, case_id: str, research: bool = False, update: bool = False
    ) -> None:
        """Upload fusion report file for a case to Scout."""

        report_type: str = "Research" if research else "Clinical"

        fusion_report: Optional[hk_models.File] = self.get_fusion_report(case_id, research)
        if fusion_report is None:
            raise FileNotFoundError(
                f"{report_type} fusion report was not found in housekeeper for {case_id}"
            )

        LOG.info(f"{report_type} fusion report {fusion_report.path} found")

        for dna_case_id in self.get_unique_dna_cases_related_to_rna_case(case_id):
            LOG.info(f"Uploading {report_type} fusion report to scout for case {dna_case_id}")

            if dry_run:
                continue
            self.scout_api.upload_fusion_report(
                case_id=dna_case_id,
                report_path=fusion_report.full_path,
                research=research,
                update=update,
            )
            LOG.info(
                f"Uploaded {report_type} fusion report",
            )

        LOG.info(f"Upload {report_type} fusion report finished!")

    def upload_rna_report_scout(
        self,
        dry_run: bool,
        report_type: str,
        report_file: hk_models.File,
        rna_case_id: str,
    ) -> None:
        """Upload report file to DNA cases related to a RNA case in scout."""
        for dna_case_id in self.get_unique_dna_cases_related_to_rna_case(rna_case_id):
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
        report_file: hk_models.File,
    ) -> None:
        """Upload report file a case to Scout."""

        LOG.info(f"Uploading {report_type} report to scout for case {case_id}")

        if dry_run:
            return
        self.scout.upload_report(
            case_id=case_id,
            report_path=report_file.full_path,
            report_type=report_type,
        )
        LOG.info(f"Uploaded {report_type} report")

        LOG.info(f"Upload {report_type} report finished!")

    def upload_rna_coverage_bigwig_to_scout(self, case_id: str, dry_run: bool) -> None:
        """Upload rna_coverage_bigwig file for a case to Scout."""

        scout_api: ScoutAPI = self.scout
        status_db: Store = self.status_db
        rna_case = status_db.family(case_id)
        rna_dna_sample_case_map: Dict[str, Dict[str, list]] = self.create_rna_dna_sample_case_map(
            rna_case=rna_case
        )
        for rna_sample_id in rna_dna_sample_case_map:
            rna_coverage_bigwig: Optional[hk_models.File] = self.get_rna_coverage_bigwig(
                case_id=case_id, sample_id=rna_sample_id
            )

            if rna_coverage_bigwig is None:
                raise FileNotFoundError(
                    f"No RNA coverage bigwig file was found in housekeeper for {rna_sample_id}"
                )

            LOG.info(f"RNA coverage bigwig file {rna_coverage_bigwig.path} found")
            dna_sample_id: str
            dna_cases: List[str]
            dna_sample_id, dna_cases = rna_dna_sample_case_map[rna_sample_id].popitem()
            for dna_case_id in dna_cases:
                LOG.info(
                    f"Uploading RNA coverage bigwig file for {dna_sample_id} in case {dna_case_id} in scout"
                )

                if dry_run:
                    continue

                scout_api.upload_rna_coverage_bigwig(
                    file_path=rna_coverage_bigwig.full_path,
                    case_id=dna_case_id,
                    customer_sample_id=dna_sample_id,
                )
                LOG.info(
                    f"Uploaded RNA coverage bigwig file for {dna_sample_id} in case {dna_case_id}"
                )

        LOG.info("Upload RNA coverage bigwig file finished!")

    def upload_splice_junctions_bed_to_scout(self, dry_run: bool, case_id: str) -> None:
        """Upload splice_junctions_bed file for a case to Scout."""

        scout_api: ScoutAPI = self.scout
        status_db: Store = self.status_db
        rna_case: models.Family = status_db.family(case_id)

        rna_dna_sample_case_map: Dict[str, Dict[str, list]] = self.create_rna_dna_sample_case_map(
            rna_case=rna_case
        )
        for rna_sample_id in rna_dna_sample_case_map:
            splice_junctions_bed: Optional[hk_models.File] = self.get_splice_junctions_bed(
                case_id=case_id, sample_id=rna_sample_id
            )

            if splice_junctions_bed is None:
                raise FileNotFoundError(
                    f"No splice junctions bed file was found in housekeeper for {rna_sample_id}"
                )

            LOG.info(f"Splice junctions bed file {splice_junctions_bed.path} found")
            dna_sample_id: str
            dna_cases: List[str]
            dna_sample_id, dna_cases = rna_dna_sample_case_map[rna_sample_id].popitem()
            for dna_case_id in dna_cases:
                LOG.info(
                    f"Uploading splice junctions bed file for sample {dna_sample_id} in case {dna_case_id} in scout"
                )

                if dry_run:
                    continue

                scout_api.upload_splice_junctions_bed(
                    file_path=splice_junctions_bed.full_path,
                    case_id=dna_case_id,
                    customer_sample_id=dna_sample_id,
                )
                LOG.info(
                    f"Uploaded splice junctions bed file {dna_sample_id} in case {dna_case_id}"
                )

        LOG.info("Upload splice junctions bed file finished!")

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
        }

        return config_builders[analysis.pipeline]



class SubjectIdCaseMapper:

    """Class to map case to other cases by subject id."""

    def __init__(self, case_id: str, subject_id: str, status_db: Store):
        self.case: models.Family = status_db.family(case_id)
        self.subject_id: str = subject_id
        self.status_db: Store = status_db

    def _filter_cases_with_subject_id(self, is_tumour: Optional[bool]) -> List[models.Family]:
        """Get all cases by subject id."""
        return self.status_db.get_cases_with_subject_id(customer_id=self.subject_id,subject_id=self.subject_id,is_tumour=is_tumour)
    
    @staticmethod
    def 

    [
            sample
            for sample in subject_id_samples
            if sample.prep_category
            in [
                PrepCategory.WHOLE_GENOME_SEQUENCING.value,
                PrepCategory.TARGETED_GENOME_SEQUENCING.value,
                PrepCategory.WHOLE_EXOME_SEQUENCING.value,
            ]
        ]



























    class RnaToDnaCaseMapper:
        """Class to map RNA cases to DNA cases by subject id."""

        def __init__(self, rna_case: models.Family):
            self.rna_case: models.Family = rna_case

        class DnaSampleCaseMap(TypedDict):
            """DNA sample case map."""

            dna_sample_id: str
            dna_cases: List[str]


        class RnaDnaSampleCaseMap(TypedDict):
            """RNA-DNA sample case map."""

            rna_sample_id: str
            dna_cases_related_to_rna_case: DnaSampleCaseMap   


                 

        @classmethod
        def get_rna_dna_sample_case_map(cls, rna_case: models.Family) -> RnaDnaSampleCaseMap:
            """Get RNA-DNA sample case map."""
            rna_dna_sample_case_map: cls.RnaDnaSampleCaseMap = {}
            for link_obj in rna_case.links:
                rna_sample_id: str = link_obj.sample.internal_id
                rna_dna_sample_case_map[rna_sample_id] = cls.get_dna_sample_case_map(
                    rna_case=rna_case, rna_sample_id=rna_sample_id
                )

            return rna_dna_sample_case_map


        @classmethod
        def get_dna_cases_relatated_to_sample_subject_id(
            cls, sample_obj: models.Sample, status_db: Store
        ):
            """Get DNA cases related to a subject id."""
            dna_cases: List[str] = []

            samples_with_sample_subject_id: List[models.Sample] = status_db.status_db.samples_by_subject_id(
            customer_id=sample_obj.customer.internal_id,
            subject_id=sample_obj.subject_id,
            is_tumour=sample_obj.is_tumour
            )

            for link_obj in sample_obj.links:
                if link_obj.prep_category in [PrepCategory.WHOLE_GENOME_SEQUENCING.value,PrepCategory.TARGETED_GENOME_SEQUENCING.value,PrepCategory.WHOLE_EXOME_SEQUENCING.value]:
                    dna_cases.append(link_obj.family.internal_id)
                
        def get_sampl


        @classmethod
        def get_dna_sample_case_map(
            cls, rna_case: models.Family, rna_sample_id: str
        ) -> RnaDnaSampleCaseMap.DnaSampleCaseMap:
            """Get DNA sample case map."""
            dna_sample_case_map: cls.RnaDnaSampleCaseMap.DnaSampleCaseMap = {}
            for dna_sample_id in cls.get_dna_sample_ids(rna_case=rna_case):
                dna_cases: List[str] = cls.get_dna_cases(
                    rna_case=rna_case, rna_sample_id=rna_sample_id, dna_sample_id=dna_sample_id
                )
                dna_sample_case_map[dna_sample_id] = dna_cases

            return dna_sample_case_map
        )

        @classmethod
        def get_dna_sample_ids(cls, rna_case: models.Family) -> List[str]:
            """Get DNA sample ids."""
            dna_sample_ids: List[str] = []
            for link_obj in rna_case.links:
                for dna_sample_id in link_obj.sample.links:
                    dna_sample_ids.append(dna_sample_id)

            return dna_sample_ids

        @classmethod
        def get_dna_cases(
            cls, rna_case: models.Family, rna_sample_id: str, dna_sample_id: str
        ) -> List[str]:
            """Get DNA cases."""
            dna_cases: List[str] = []
            for link_obj in rna_case.links:
                if link_obj.sample.internal_id == rna_sample_id:
                    for dna_sample_obj in link_obj.sample.links:
                        if dna_sample_obj.internal_id == dna_sample_id:
                            dna_cases.append(dna_sample_obj.family.internal_id)

            return dna_cases

    
    
    
    
    
    
    # we get a rna case
    # the case hase samples on it
    # those sammples have a subject id# those subject its can exist in another case
    # we want to get the dna case that is related to the rna case
    # but only if those cases are balsamic, dna or balsamic_umi



    def create_rna_dna_sample_case_map(
        self, rna_case: models.Family
    ) -> Dict[str, Dict[str, List[str]]]:
        """Returns a nested dictionary for mapping an RNA sample to a DNA sample and its DNA cases based on
        subject_id. Example dictionary {rna_sample_id : {dna_sample_id : [dna_case1_id, dna_case2_id]}}."""
        rna_dna_sample_case_map: Dict[str, Dict[str, List[str]]] = {}
        for link in rna_case.links:
            self._map_rna_sample(
                rna_sample=link.sample, rna_dna_sample_case_map=rna_dna_sample_case_map
            )
        return rna_dna_sample_case_map

    def _map_rna_sample(
        self, rna_sample: models.Sample, rna_dna_sample_case_map: Dict[str, Dict[str, List[str]]]
    ) -> Dict[str, Dict[str, List[str]]]:
        """Create a dictionary of all DNA samples, and their related cases, related to a RNA sample."""
        dna_sample: models.Sample = self._map_dna_samples_related_to_rna_sample(
            rna_sample=rna_sample, rna_dna_sample_case_map=rna_dna_sample_case_map
        )
        self._map_dna_cases_to_dna_sample(
            dna_sample=dna_sample,
            rna_dna_sample_case_map=rna_dna_sample_case_map,
            rna_sample=rna_sample,
        )
        return rna_dna_sample_case_map

    def _map_dna_samples_related_to_rna_sample(
        self, rna_sample: models.Sample, rna_dna_sample_case_map: Dict[str, Dict[str, List[str]]]
    ) -> models.Sample:
        """Maps an RNA sample to a DNA sample based on subject id."""
        if not rna_sample.subject_id:
            raise CgDataError(
                f"Failed to link RNA sample {rna_sample.internal_id} to dna samples - subject_id field is empty"
            )

        samples_by_subject_id: List[models.Sample] = self.status_db.samples_by_subject_id(
            customer_id=rna_sample.customer.internal_id,
            subject_id=rna_sample.subject_id,
            is_tumour=rna_sample.is_tumour,
        )
        subject_id_dna_samples: List[Optional[models.Sample]] = self._get_application_prep_category(
            samples_by_subject_id
        )
        self.validate_number_of_dna_samples_by_subject_id(
            samples_by_subject_id=subject_id_dna_samples
        )
        rna_dna_sample_case_map[rna_sample.internal_id]: Dict[str, List[str]] = {}
        sample: models.Sample
        for sample in subject_id_dna_samples:
            if sample.internal_id != rna_sample.internal_id:
                rna_dna_sample_case_map[rna_sample.internal_id][sample.name]: List[str] = []
                return sample

    def validate_number_of_dna_samples_by_subject_id(
        self, samples_by_subject_id: List[models.Sample]
    ) -> None:
        """Validates that there are two DNA samples with the same subject_id."""

        if len(samples_by_subject_id) != 1:
            raise CgDataError(
                f"Unexpected number of DNA sample matches for subject_id.\n"
                f"Number of matches: {len(samples_by_subject_id)}"
            )

    @staticmethod
    def _map_dna_cases_to_dna_sample(
        dna_sample: models.Sample,
        rna_dna_sample_case_map: Dict[str, Dict[str, list]],
        rna_sample: models.Sample,
    ) -> None:
        """Maps a list of DNA cases linked to DNA sample."""
        cases_related_to_dna_sample = [link.family for link in dna_sample.links]
        for case in cases_related_to_dna_sample:
            if (
                case.data_analysis in [Pipeline.MIP_DNA, Pipeline.BALSAMIC, Pipeline.BALSAMIC_UMI]
                and case.customer_id == rna_sample.customer_id
            ):
                rna_dna_sample_case_map[rna_sample.internal_id][dna_sample.name].append(
                    case.internal_id
                )

    @staticmethod
    def _get_application_prep_category(
        subject_id_samples: List[models.Sample],
    ) -> List[Optional[models.Sample]]:
        """Filter a models.Sample list, returning DNA samples selected on their prep_category."""
        subject_id_dna_samples: List[Optional[models.Sample]] = [
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
