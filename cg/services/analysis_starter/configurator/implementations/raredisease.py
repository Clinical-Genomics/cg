import logging
from pathlib import Path

from cg.apps.lims import LimsAPI
from cg.constants import DEFAULT_CAPTURE_KIT, FileExtensions, Priority, Workflow
from cg.constants.scout import ScoutExportFileName
from cg.constants.tb import AnalysisType
from cg.exc import CgDataError
from cg.io.txt import concat_txt
from cg.io.yaml import read_yaml, write_yaml_nextflow_style
from cg.models.cg_config import RarediseaseConfig
from cg.models.raredisease.raredisease import RarediseaseParameters
from cg.services.analysis_starter.configurator.abstract_service import Configurator
from cg.services.analysis_starter.configurator.models.nextflow import NextflowCaseConfig
from cg.services.analysis_starter.configurator.utils import (
    get_slurm_qos_for_case,
    replace_values_in_params_file,
    write_content_to_file_or_stdout,
)
from cg.store.models import BedVersion, Case, Sample
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class RarediseaseConfigurator(Configurator):
    """Configurator for Raredisease analysis."""

    def __init__(self, store: Store, config: RarediseaseConfig, lims: LimsAPI):
        self.account: str = config.slurm.account
        self.lims: LimsAPI = lims
        self.platform: str = config.platform
        self.resources: str = config.resources
        self.root_dir: str = config.root
        self.store: Store = store
        self.workflow_config_path: str = config.config

    def create_config(self, case_id: str, dry_run: bool = False) -> NextflowCaseConfig:
        self._create_case_directory(case_id=case_id, dry_run=False)
        self._create_nextflow_config(case_id=case_id, dry_run=False)
        self._create_params_file(case_id=case_id, dry_run=False)
        return NextflowCaseConfig(
            case_id=case_id,
            case_priority=self._get_case_priority(case_id),
            workflow=self._get_case_workflow(case_id),
            netxflow_config_file=self._get_nextflow_config_path(case_id=case_id).as_posix(),
            params_file=self._get_params_file_path(case_id=case_id).as_posix(),
            work_dir=self._get_work_dir(case_id=case_id).as_posix(),
        )

    def _create_case_directory(self, case_id: str, dry_run: bool = False) -> None:
        """Create case working directory."""
        case_path: Path = self._get_case_path(case_id=case_id)
        if dry_run:
            LOG.info(f"Would have created case directory {case_path.as_posix()}")
            return
        case_path.mkdir(parents=True, exist_ok=True)
        LOG.debug(f"Created case directory {case_path.as_posix()} successfully")

    def _create_nextflow_config(self, case_id: str, dry_run: bool = False) -> None:
        """Create nextflow config file."""
        content: str = self._get_nextflow_config_content(case_id=case_id)
        file_path: Path = self._get_nextflow_config_path(case_id=case_id)
        write_content_to_file_or_stdout(content=content, file_path=file_path, dry_run=dry_run)
        LOG.debug(f"Created nextflow config file {file_path.as_posix()} successfully")

    def _create_params_file(self, case_id: str, dry_run: bool = False) -> None:
        """Create parameters file for a case."""
        LOG.debug("Getting parameters information built on-the-fly")
        built_workflow_parameters: dict | None = self._get_built_workflow_parameters(
            case_id=case_id
        ).model_dump()
        LOG.debug("Adding parameters from the pipeline config file if it exist")

        workflow_parameters: dict = built_workflow_parameters | (
            read_yaml(self.params) if hasattr(self, "params") and self.params else {}
        )
        replaced_workflow_parameters: dict = replace_values_in_params_file(
            workflow_parameters=workflow_parameters
        )
        if not dry_run:
            self._write_params_file(
                case_id=case_id, replaced_workflow_parameters=replaced_workflow_parameters
            )

    def _get_data_analysis_type(self, case_id: str) -> str:
        """Return data analysis type carried out."""
        sample: Sample = self.store.get_samples_by_case_id(case_id=case_id)[0]
        return sample.application_version.application.analysis_type

    def _get_built_workflow_parameters(self, case_id: str) -> RarediseaseParameters:
        """Return parameters."""
        analysis_type: str = self._get_data_analysis_type(case_id=case_id)
        target_bed_file: str = self._get_target_bed(case_id=case_id, analysis_type=analysis_type)
        skip_germlinecnvcaller = self._get_germlinecnvcaller_flag(analysis_type=analysis_type)
        outdir = self._get_case_path(case_id=case_id)

        return RarediseaseParameters(
            input=self._get_sample_sheet_path(case_id=case_id),
            outdir=outdir,
            analysis_type=analysis_type,
            target_bed_file=target_bed_file,
            save_mapped_as_cram=True,
            skip_germlinecnvcaller=skip_germlinecnvcaller,
            vcfanno_extra_resources=f"{outdir}/{ScoutExportFileName.MANAGED_VARIANTS}",
            vep_filters_scout_fmt=f"{outdir}/{ScoutExportFileName.PANELS}",
        )

    def _get_case_path(self, case_id: str) -> Path:
        """Path to case working directory."""
        return Path(self.root_dir, case_id)

    def _get_case_priority(self, case_id: str) -> Priority:
        return self.store.get_case_by_internal_id(case_id).priority

    def _get_case_workflow(self, case_id: str) -> Workflow:
        case: Case = self.store.get_case_by_internal_id(case_id)
        return Workflow(case.data_analysis)

    def _get_cluster_options(self, case_id: str) -> str:
        case: Case = self.store.get_case_by_internal_id(case_id)
        qos: str = get_slurm_qos_for_case(case)
        return f'process.clusterOptions = "-A {self.account} --qos={qos}"\n'

    @staticmethod
    def _get_germlinecnvcaller_flag(analysis_type: str) -> bool:
        if analysis_type == AnalysisType.WGS:
            return True
        return False

    def _get_nextflow_config_content(self, case_id: str) -> str:
        config_files_list: list[str] = [
            self.platform,
            self.workflow_config_path,
            self.resources,
        ]
        case_specific_params: list[str] = [
            self._get_cluster_options(case_id=case_id),
        ]
        return concat_txt(
            file_paths=config_files_list,
            str_content=case_specific_params,
        )

    def _get_nextflow_config_path(self, case_id: str) -> Path:
        return Path((self._get_case_path(case_id)), f"{case_id}_nextflow_config").with_suffix(
            FileExtensions.JSON
        )

    def _get_params_file_path(self, case_id: str) -> Path:
        return Path((self._get_case_path(case_id)), f"{case_id}_params_file").with_suffix(
            FileExtensions.YAML
        )

    def _get_sample_sheet_path(self, case_id: str) -> Path:
        """Path to sample sheet."""
        return Path(self._get_case_path(case_id), f"{case_id}_samplesheet").with_suffix(
            FileExtensions.CSV
        )

    def _get_target_bed(self, case_id: str, analysis_type: str) -> str:
        """
        Return the target bed file from LIMS or use default capture kit for WHOLE_GENOME_SEQUENCING.
        """
        target_bed_file: str = self._get_target_bed_from_lims(case_id=case_id)
        if not target_bed_file:
            if analysis_type == AnalysisType.WGS:
                return DEFAULT_CAPTURE_KIT
            raise ValueError("No capture kit was found in LIMS")
        return target_bed_file

    def _get_target_bed_from_lims(self, case_id: str) -> str | None:
        """Get target bed filename from LIMS."""
        case: Case = self.store.get_case_by_internal_id(internal_id=case_id)
        sample: Sample = case.links[0].sample
        if sample.from_sample:
            sample: Sample = self.store.get_sample_by_internal_id(internal_id=sample.from_sample)
        target_bed_shortname: str | None = self.lims.capture_kit(lims_id=sample.internal_id)
        if not target_bed_shortname:
            return None
        bed_version: BedVersion | None = self.store.get_bed_version_by_short_name(
            bed_version_short_name=target_bed_shortname
        )
        if not bed_version:
            raise CgDataError(f"Bed-version {target_bed_shortname} does not exist")
        return bed_version.filename

    def _get_work_dir(self, case_id: str) -> Path:
        return Path(self.root_dir, case_id, "work")

    def _write_params_file(self, case_id: str, replaced_workflow_parameters: dict = None) -> None:
        """Write params-file for analysis."""
        LOG.debug("Writing parameters file")
        if replaced_workflow_parameters:
            write_yaml_nextflow_style(
                content=replaced_workflow_parameters,
                file_path=self._get_params_file_path(case_id=case_id),
            )
        else:
            self._get_params_file_path(case_id=case_id).touch()
