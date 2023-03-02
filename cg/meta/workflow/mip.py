import logging

from pathlib import Path
from typing import Any, List, Optional, Type, Dict, Union

from pydantic import ValidationError

from cg.apps.mip.confighandler import ConfigHandler
from cg.constants import COLLABORATORS, COMBOS, GenePanelMasterList, Pipeline, FileExtensions
from cg.constants.constants import FileFormat
from cg.constants.housekeeper_tags import HkMipAnalysisTag
from cg.exc import CgError
from cg.io.controller import WriteFile, ReadFile
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.fastq import MipFastqHandler
from cg.models.cg_config import CGConfig
from cg.models.mip.mip_analysis import MipAnalysis
from cg.models.mip.mip_config import MipBaseConfig
from cg.models.mip.mip_metrics_deliverables import MIPMetricsDeliverables
from cg.models.mip.mip_sample_info import MipBaseSampleInfo
from cg.store.models import BedVersion, FamilySample, Family, Sample

CLI_OPTIONS = {
    "config": {"option": "--config_file"},
    "slurm_quality_of_service": {"option": "--slurm_quality_of_service"},
    "email": {"option": "--email"},
    "base": {"option": "--cluster_constant_path"},
    "dryrun": {"option": "--dry_run_all"},
    "gene_list": {"option": "--vcfparser_slt_fl"},
    "max_gaussian": {"option": "--gatk_varrecal_snv_max_gau"},
    "skip_evaluation": {"option": "--qccollect_skip_evaluation"},
    "start_after": {"option": "--start_after_recipe"},
    "start_with": {"option": "--start_with_recipe"},
    "use_bwa_mem": {"option": "--bwa_mem 1 --bwa_mem2 0"},
}
LOG = logging.getLogger(__name__)


class MipAnalysisAPI(AnalysisAPI):
    """The workflow is accessed through Trailblazer but cg provides additional conventions and
    hooks into the status database that makes managing analyses simpler"""

    def __init__(self, config: CGConfig, pipeline: Pipeline):
        super().__init__(pipeline, config)

    @property
    def root(self) -> str:
        raise NotImplementedError

    @property
    def conda_env(self) -> str:
        raise NotImplementedError

    @property
    def mip_pipeline(self) -> str:
        raise NotImplementedError

    @property
    def script(self) -> str:
        raise NotImplementedError

    @property
    def fastq_handler(self):
        return MipFastqHandler

    def get_pedigree_config_path(self, case_id: str) -> Path:
        return Path(self.root, case_id, "pedigree.yaml")

    def get_case_config_path(self, case_id: str) -> Path:
        return Path(self.root, case_id, "analysis", f"{case_id}_config.yaml")

    def get_deliverables_file_path(self, case_id: str) -> Path:
        """
        Location in working directory where deliverables file will be stored upon completion of analysis.
        Deliverables file is used to communicate paths and tag definitions for files in a finished analysis
        """
        return Path(self.root, case_id, "analysis", f"{case_id}_deliverables.yaml")

    def get_sample_info_path(self, case_id: str) -> Path:
        """Get case analysis sample info path"""
        return Path(self.root, case_id, "analysis", f"{case_id}_qc_sample_info.yaml")

    def get_panel_bed(self, panel_bed: str = None) -> Optional[str]:
        """Check and return BED gene panel."""
        if not panel_bed:
            return None
        if panel_bed.endswith(FileExtensions.BED):
            return panel_bed
        bed_version: Optional[BedVersion] = self.status_db.get_bed_version_by_short_name(
            bed_version_short_name=panel_bed
        )
        if not bed_version:
            raise CgError("Please provide a valid panel shortname or a path to panel.bed file!")
        return bed_version.filename

    def pedigree_config(self, case_id: str, panel_bed: str = None) -> dict:
        """Make the MIP pedigree config. Meta data for the family is taken from the family object
        and converted to MIP format via trailblazer.
        """

        # Validate and reformat to MIP pedigree config format
        case_obj: Family = self.status_db.family(case_id)
        return ConfigHandler.make_pedigree_config(
            data={
                "case": case_obj.internal_id,
                "default_gene_panels": case_obj.panels,
                "samples": [
                    self.config_sample(link_obj=link_obj, panel_bed=panel_bed)
                    for link_obj in case_obj.links
                ],
            }
        )

    def write_pedigree_config(self, case_id: str, data: dict) -> None:
        """Write the pedigree config to the the case dir"""
        out_dir = self.get_case_path(case_id=case_id)
        out_dir.mkdir(parents=True, exist_ok=True)
        pedigree_config_path: Path = self.get_pedigree_config_path(case_id=case_id)
        WriteFile.write_file_from_content(
            content=data, file_format=FileFormat.YAML, file_path=pedigree_config_path
        )
        LOG.info("Config file saved to %s", pedigree_config_path)

    @staticmethod
    def get_sample_data(link_obj: FamilySample) -> Dict[str, Union[str, int]]:
        """Return sample specific data."""
        return {
            "sample_id": link_obj.sample.internal_id,
            "sample_display_name": link_obj.sample.name,
            "analysis_type": link_obj.sample.application_version.application.analysis_type,
            "sex": link_obj.sample.sex,
            "phenotype": link_obj.status,
            "expected_coverage": link_obj.sample.application_version.application.min_sequencing_depth,
        }

    def get_sample_fastq_destination_dir(self, case: Family, sample: Sample) -> Path:
        """Return the path to the FASTQ destination directory."""
        return Path(
            self.root,
            case.internal_id,
            sample.application_version.application.analysis_type,
            sample.internal_id,
            FileFormat.FASTQ,
        )

    def link_fastq_files(self, case_id: str, dry_run: bool = False) -> None:
        case_obj = self.status_db.family(case_id)
        for link in case_obj.links:
            self.link_fastq_files_for_sample(
                case_obj=case_obj,
                sample_obj=link.sample,
            )

    def write_panel(self, case_id: str, content: List[str]):
        """Write the gene panel to case dir"""
        out_dir = Path(self.root, case_id)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = Path(out_dir, "gene_panels.bed")
        with out_path.open("w") as out_handle:
            out_handle.write("\n".join(content))

    @staticmethod
    def convert_panels(customer: str, default_panels: List[str]) -> List[str]:
        """Convert between default panels and all panels included in gene list."""
        # check if all default panels are part of master list
        master_list: List[str] = GenePanelMasterList.get_panel_names()
        if customer in COLLABORATORS and set(default_panels).issubset(master_list):
            return master_list

        # the rest are handled the same way
        all_panels = set(default_panels)

        # fill in extra panels if selection is part of a combo
        for panel in default_panels:
            if panel in COMBOS:
                for extra_panel in COMBOS[panel]:
                    all_panels.add(extra_panel)

        # add OMIM to every panel choice
        all_panels.add(GenePanelMasterList.OMIM_AUTO)

        return list(all_panels)

    def _get_latest_raw_file(self, family_id: str, tags: List[str]) -> Any:
        """Get a python object file for a tag and a family ."""

        last_version = self.housekeeper_api.last_version(bundle=family_id)

        analysis_files = self.housekeeper_api.files(
            bundle=family_id, version=last_version.id, tags=tags
        ).all()

        if analysis_files:
            analysis_file_raw = self._open_bundle_file(analysis_files[0].path)
        else:
            raise LOG.warning(
                "No post analysis files received from DeliverAPI for '%s'",
                family_id,
            )

        return analysis_file_raw

    def _open_bundle_file(self, relative_file_path: str) -> Any:
        """Open a bundle file and return it as an Python object"""

        full_file_path: Path = Path(self.housekeeper_api.get_root_dir()).joinpath(
            relative_file_path
        )
        return ReadFile.get_content_from_file(file_format=FileFormat.YAML, file_path=full_file_path)

    def get_latest_metadata(self, family_id: str) -> MipAnalysis:
        """Get the latest trending data for a family"""

        mip_config_raw = self._get_latest_raw_file(
            family_id=family_id, tags=HkMipAnalysisTag.CONFIG
        )
        qc_metrics_raw = self._get_latest_raw_file(
            family_id=family_id, tags=HkMipAnalysisTag.QC_METRICS
        )
        sample_info_raw = self._get_latest_raw_file(
            family_id=family_id, tags=HkMipAnalysisTag.SAMPLE_INFO
        )
        if mip_config_raw and qc_metrics_raw and sample_info_raw:
            try:
                mip_analysis: MipAnalysis = self.parse_analysis(
                    config_raw=mip_config_raw,
                    qc_metrics_raw=qc_metrics_raw,
                    sample_info_raw=sample_info_raw,
                )
                return mip_analysis
            except ValidationError as error:
                LOG.error(
                    "get_latest_metadata failed for '%s', missing attribute: %s",
                    family_id,
                    error,
                )
                raise error
        else:
            LOG.error(f"Unable to retrieve the latest metadata for {family_id}")
            raise CgError

    def parse_analysis(
        self, config_raw: dict, qc_metrics_raw: dict, sample_info_raw: dict
    ) -> MipAnalysis:
        """Parses the output analysis files from MIP

        Args:
            config_raw (dict): raw YAML input from MIP analysis config file
            qc_metrics_raw (dict): raw YAML input from MIP analysis qc metric file
            sample_info_raw (dict): raw YAML input from MIP analysis qc sample info file
        Returns:
            MipAnalysis: parsed MIP analysis data
        """
        mip_config: MipBaseConfig = MipBaseConfig(**config_raw)
        qc_metrics = MIPMetricsDeliverables(**qc_metrics_raw)
        sample_info: MipBaseSampleInfo = MipBaseSampleInfo(**sample_info_raw)

        return MipAnalysis(
            case=mip_config.case_id,
            genome_build=sample_info.genome_build,
            sample_id_metrics=qc_metrics.sample_id_metrics,
            mip_version=sample_info.mip_version,
            rank_model_version=sample_info.rank_model_version,
            sample_ids=mip_config.sample_ids,
            sv_rank_model_version=sample_info.sv_rank_model_version,
        )

    @staticmethod
    def is_dna_only_case(case_obj: Family) -> bool:
        """Returns True if all samples of a case has DNA application type."""

        return all(
            _link.sample.application_version.application.analysis_type not in "wts"
            for _link in case_obj.links
        )

    def get_skip_evaluation_flag(self, case_id: str, skip_evaluation: bool) -> bool:
        """If any sample in this case is downsampled or external, returns true"""
        if skip_evaluation:
            return True
        case_obj = self.status_db.family(case_id)
        for link_obj in case_obj.links:
            downsampled = isinstance(link_obj.sample.downsampled_to, int)
            external = link_obj.sample.application_version.application.is_external
            if downsampled or external:
                LOG.info(
                    "%s: downsampled/external - skip evaluation",
                    link_obj.sample.internal_id,
                )
                return True
        return False

    def get_cases_to_analyze(self) -> List[Family]:
        """Return cases to analyze."""
        cases_query: List[Family] = self.status_db.cases_to_analyze(
            pipeline=self.pipeline, threshold=self.threshold_reads
        )
        cases_to_analyze = []
        for case_obj in cases_query:
            if case_obj.action == "analyze" or not case_obj.latest_analyzed:
                cases_to_analyze.append(case_obj)
            elif (
                self.trailblazer_api.get_latest_analysis_status(case_id=case_obj.internal_id)
                == "failed"
            ):
                cases_to_analyze.append(case_obj)
        return cases_to_analyze

    @staticmethod
    def _append_value_for_non_flags(parameters: list, value) -> None:
        """Add the value of the non boolean options to the parameters"""
        if value is not True:
            parameters.append(value)

    @staticmethod
    def _cg_to_mip_option_map(parameters: list, mip_key) -> None:
        """Map cg options to MIP option syntax"""
        parameters.append(CLI_OPTIONS[mip_key]["option"])

    def run_analysis(self, case_id: str, command_args: dict, dry_run: bool) -> None:
        parameters = [
            case_id,
        ]
        for key, value in command_args.items():
            if value:
                self._cg_to_mip_option_map(parameters, key)
                self._append_value_for_non_flags(parameters, value)

        exit_code = self.process.run_command(dry_run=dry_run, parameters=parameters)
        for line in self.process.stdout_lines():
            LOG.info(line)
        for line in self.process.stderr_lines():
            LOG.info(line)
        return exit_code

    def get_case_path(self, case_id: str) -> Path:
        return Path(self.root, case_id)

    def get_trailblazer_config_path(self, case_id: str) -> Path:
        return Path(self.get_case_path(case_id=case_id), "analysis", "slurm_job_ids.yaml")

    def config_sample(self, link_obj: FamilySample, panel_bed: str) -> dict:
        raise NotImplementedError

    def get_pipeline_version(self, case_id: str) -> str:
        """Get MIP version from sample info file"""
        LOG.debug("Fetch pipeline version")
        sample_info_raw: dict = ReadFile.get_content_from_file(
            file_format=FileFormat.YAML, file_path=self.get_sample_info_path(case_id)
        )
        sample_info: MipBaseSampleInfo = MipBaseSampleInfo(**sample_info_raw)
        return sample_info.mip_version
