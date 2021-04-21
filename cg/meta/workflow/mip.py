import logging
from pathlib import Path
from typing import Any, List, Optional

from cg.apps.mip import parse_trending
from cg.apps.mip.confighandler import ConfigHandler
from cg.constants import COLLABORATORS, COMBOS, MASTER_LIST, Pipeline
from cg.exc import CgError
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.fastq import MipFastqHandler
from cg.models.cg_config import CGConfig
from cg.store import models
from ruamel.yaml import ruamel, safe_load

CLI_OPTIONS = {
    "config": {"option": "--config_file"},
    "priority": {"option": "--slurm_quality_of_service"},
    "email": {"option": "--email"},
    "base": {"option": "--cluster_constant_path"},
    "dryrun": {"option": "--dry_run_all"},
    "gene_list": {"option": "--vcfparser_slt_fl"},
    "max_gaussian": {"option": "--gatk_varrecal_snv_max_gau"},
    "skip_evaluation": {"option": "--qccollect_skip_evaluation"},
    "start_with": {"option": "--start_with_recipe"},
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

    def resolve_panel_bed(self, panel_bed: Optional[str]) -> Optional[str]:
        if panel_bed:
            if panel_bed.endswith(".bed"):
                return panel_bed
            bed_version = self.status_db.bed_version(panel_bed)
            if not bed_version:
                raise CgError("Please provide a valid panel shortname or a path to panel.bed file!")
            return bed_version.filename

    def pedigree_config(self, case_id: str, panel_bed: str = None) -> dict:
        """Make the MIP pedigree config. Meta data for the family is taken from the family object
        and converted to MIP format via trailblazer.
        """

        # Validate and reformat to MIP pedigree config format
        case_obj: models.Family = self.status_db.family(case_id)
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
        pedigree_config_path = self.get_pedigree_config_path(case_id=case_id)
        pedigree_config_path.write_text(
            ruamel.yaml.round_trip_dump(data, indent=4, block_seq_indent=2)
        )
        LOG.info("Config file saved to %s", pedigree_config_path)

    @staticmethod
    def get_sample_data(link_obj: models.FamilySample) -> dict:
        return {
            "sample_id": link_obj.sample.internal_id,
            "sample_display_name": link_obj.sample.name,
            "analysis_type": link_obj.sample.application_version.application.analysis_type,
            "sex": link_obj.sample.sex,
            "phenotype": link_obj.status,
            "expected_coverage": link_obj.sample.application_version.application.min_sequencing_depth,
        }

    def get_sample_fastq_destination_dir(
        self, case_obj: models.Family, sample_obj: models.Sample
    ) -> Path:
        return Path(
            self.root,
            case_obj.internal_id,
            sample_obj.application_version.application.analysis_type,
            sample_obj.internal_id,
            "fastq",
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
        if customer in COLLABORATORS and all(panel in MASTER_LIST for panel in default_panels):
            return MASTER_LIST

        # the rest are handled the same way
        all_panels = set(default_panels)

        # fill in extra panels if selection is part of a combo
        for panel in default_panels:
            if panel in COMBOS:
                for extra_panel in COMBOS[panel]:
                    all_panels.add(extra_panel)

        # add OMIM to every panel choice
        all_panels.add("OMIM-AUTO")

        return list(all_panels)

    def _get_latest_raw_file(self, family_id: str, tag: str) -> Any:
        """Get a python object file for a tag and a family ."""

        last_version = self.housekeeper_api.last_version(bundle=family_id)

        analysis_files = self.housekeeper_api.files(
            bundle=family_id, version=last_version.id, tags=[tag]
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
        """Open a bundle file and return it as an Python object."""

        full_file_path = Path(self.housekeeper_api.get_root_dir()).joinpath(relative_file_path)
        return safe_load(open(full_file_path))

    def get_latest_metadata(self, family_id: str) -> dict:
        """Get the latest trending data for a family."""

        mip_config_raw = self._get_latest_raw_file(family_id=family_id, tag="mip-config")
        qcmetrics_raw = self._get_latest_raw_file(family_id=family_id, tag="qcmetrics")
        sampleinfo_raw = self._get_latest_raw_file(family_id=family_id, tag="sampleinfo")
        trending = dict()
        if mip_config_raw and qcmetrics_raw and sampleinfo_raw:
            try:
                trending = parse_trending.parse_mip_analysis(
                    mip_config_raw=mip_config_raw,
                    qcmetrics_raw=qcmetrics_raw,
                    sampleinfo_raw=sampleinfo_raw,
                )
            except KeyError as error:
                LOG.warning(
                    "get_latest_metadata failed for '%s', missing key: %s",
                    family_id,
                    error,
                )
                LOG.warning(
                    "get_latest_metadata failed for '%s', missing key: %s",
                    family_id,
                    error,
                )
                trending = {}
        return trending

    @staticmethod
    def is_dna_only_case(case_obj: models.Family) -> bool:
        """Returns True if all samples of a case has dna application type"""

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

    def get_cases_to_analyze(self) -> List[models.Family]:
        cases_query: List[models.Family] = self.status_db.cases_to_analyze(
            pipeline=self.pipeline, threshold=self.threshold_reads
        )
        cases_to_analyze = []
        for case_obj in cases_query:
            if not case_obj.latest_analyzed:
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

    def config_sample(self, link_obj: models.FamilySample, panel_bed: str) -> dict:
        raise NotImplementedError
