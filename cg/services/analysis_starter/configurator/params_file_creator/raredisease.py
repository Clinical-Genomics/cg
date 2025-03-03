import logging
from pathlib import Path

from cg.apps.lims import LimsAPI
from cg.constants import DEFAULT_CAPTURE_KIT, FileExtensions
from cg.constants.scout import ScoutExportFileName
from cg.constants.tb import AnalysisType
from cg.exc import CgDataError
from cg.io.yaml import read_yaml, write_yaml_nextflow_style
from cg.models.raredisease.raredisease import RarediseaseParameters
from cg.services.analysis_starter.configurator.params_file_creator.utils import (
    replace_values_in_params_file,
)
from cg.store.models import BedVersion, Case, Sample

LOG = logging.getLogger(__name__)


class RarediseaseParamsCreator:

    def __init__(self, store, lims: LimsAPI, params: str):
        self.store = store
        self.params = params
        self.lims = lims

    @staticmethod
    def get_file_path(case_id: str, case_path: Path) -> Path:
        return Path(case_path, f"{case_id}_params_file").with_suffix(FileExtensions.YAML)

    def create(
        self, case_id: str, case_path: Path, sample_sheet_path: Path, dry_run: bool = False
    ) -> None:
        """Create parameters file for a case."""
        LOG.debug("Getting parameters information built on-the-fly")
        built_workflow_parameters: dict | None = self._get_built_workflow_parameters(
            case_id=case_id, case_path=case_path, sample_sheet_path=sample_sheet_path
        ).model_dump()
        LOG.debug("Adding parameters from the pipeline config file if it exist")

        workflow_parameters: dict = built_workflow_parameters | (
            read_yaml(self.params) if hasattr(self, "params") and self.params else {}
        )
        replaced_workflow_parameters: dict = replace_values_in_params_file(
            workflow_parameters=workflow_parameters
        )
        if not dry_run:
            self._write_file(
                case_id=case_id, content=replaced_workflow_parameters, case_path=case_path
            )

    def _get_built_workflow_parameters(
        self, case_id: str, case_path: Path, sample_sheet_path: Path
    ) -> RarediseaseParameters:
        """Return parameters."""
        analysis_type: str = self._get_data_analysis_type(case_id=case_id)
        target_bed_file: str = self._get_target_bed(case_id=case_id, analysis_type=analysis_type)
        skip_germlinecnvcaller = self._get_germlinecnvcaller_flag(analysis_type=analysis_type)
        outdir = case_path

        return RarediseaseParameters(
            input=sample_sheet_path,
            outdir=outdir,
            analysis_type=analysis_type,
            target_bed_file=target_bed_file,
            save_mapped_as_cram=True,
            skip_germlinecnvcaller=skip_germlinecnvcaller,
            vcfanno_extra_resources=f"{outdir}/{ScoutExportFileName.MANAGED_VARIANTS}",
            vep_filters_scout_fmt=f"{outdir}/{ScoutExportFileName.PANELS}",
        )

    def _get_data_analysis_type(self, case_id: str) -> str:
        """
        Return case analysis type (WEG, WGS, WTS or TGS). Assumes all case samples have the same
        analysis type.
        """
        sample: Sample = self.store.get_samples_by_case_id(case_id=case_id)[0]
        return sample.application_version.application.analysis_type

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
        """
        Get target bed filename from LIMS.
        Raises:
            CgDataError: if the bed target capture version is not found in StatusDB.
        """
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

    def _write_file(self, case_id: str, case_path: Path, content: dict = None) -> None:
        """Write params-file for analysis."""
        file_path: Path = self.get_file_path(case_id=case_id, case_path=case_path)
        LOG.debug("Writing parameters file")
        if content:
            write_yaml_nextflow_style(
                content=content,
                file_path=file_path,
            )
        else:
            file_path.touch()
