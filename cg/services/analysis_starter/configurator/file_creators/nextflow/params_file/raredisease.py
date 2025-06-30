from pathlib import Path

from cg.apps.lims import LimsAPI
from cg.constants import DEFAULT_CAPTURE_KIT, FileExtensions
from cg.constants.scout import ScoutExportFileName
from cg.constants.tb import AnalysisType
from cg.exc import CgDataError
from cg.io.yaml import read_yaml, write_yaml_nextflow_style
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.abstract import (
    ParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.models import (
    RarediseaseParameters,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.utils import (
    replace_values_in_params_file,
    validate_no_repeated_parameters,
)
from cg.store.models import BedVersion, Case, Sample
from cg.store.store import Store


class RarediseaseParamsFileCreator(ParamsFileCreator):

    def __init__(self, store: Store, lims: LimsAPI, params: str):
        self.store = store
        self.lims = lims
        self.params = params

    @staticmethod
    def get_file_path(case_id: str, case_path: Path) -> Path:
        """Return the path to the params file."""
        return Path(case_path, f"{case_id}_params_file").with_suffix(FileExtensions.YAML)

    def create(self, case_id: str, case_path: Path, sample_sheet_path: Path) -> None:
        """Create the params file for a case."""
        file_path: Path = self.get_file_path(case_id=case_id, case_path=case_path)
        content: dict = self._get_content(
            case_id=case_id, case_path=case_path, sample_sheet_path=sample_sheet_path
        )
        write_yaml_nextflow_style(file_path=file_path, content=content)

    def _get_content(self, case_id: str, case_path: Path, sample_sheet_path: Path) -> dict:
        """Return the content of a params file for a case."""
        case_workflow_parameters: dict = self._get_case_parameters(
            case_id=case_id, case_path=case_path, sample_sheet_path=sample_sheet_path
        ).model_dump()
        workflow_parameters: any = read_yaml(Path(self.params))
        validate_no_repeated_parameters(
            case_parameters=case_workflow_parameters, workflow_parameters=workflow_parameters
        )
        parameters: dict = case_workflow_parameters | workflow_parameters
        curated_parameters: dict = replace_values_in_params_file(parameters)
        return curated_parameters

    def _get_case_parameters(
        self, case_id: str, case_path: Path, sample_sheet_path: Path
    ) -> RarediseaseParameters:
        """Return case-specific parameters for the analysis."""
        analysis_type: str = self._get_data_analysis_type(case_id)
        target_bed_file: str = self._get_target_bed(case_id=case_id, analysis_type=analysis_type)
        return RarediseaseParameters(
            input=sample_sheet_path,
            outdir=case_path,
            analysis_type=analysis_type,
            target_bed_file=target_bed_file,
            save_mapped_as_cram=True,
            vcfanno_extra_resources=f"{case_path}/{ScoutExportFileName.MANAGED_VARIANTS}",
            vep_filters_scout_fmt=f"{case_path}/{ScoutExportFileName.PANELS}",
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
        Raises:
            ValueError if not capture kit can be assigned to the case.
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
