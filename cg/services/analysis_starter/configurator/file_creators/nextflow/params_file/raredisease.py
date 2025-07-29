import logging
from pathlib import Path

from cg.apps.lims import LimsAPI
from cg.constants import FileExtensions
from cg.constants.scout import ScoutExportFileName
from cg.constants.symbols import EMPTY_STRING
from cg.exc import CgDataError
from cg.io.csv import write_csv
from cg.io.yaml import read_yaml, write_yaml_nextflow_style
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.abstract import (
    ParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.models import (
    RarediseaseParameters,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.utils import (
    replace_values_in_params_file,
)
from cg.store.models import BedVersion, Case, Sample
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class RarediseaseParamsFileCreator(ParamsFileCreator):

    def __init__(self, store: Store, lims: LimsAPI, params: str):
        self.store = store
        self.lims = lims
        self.params = Path(params)

    def create(self, case_id: str, case_path: Path, sample_sheet_path: Path) -> None:
        """Create the params file for a case."""
        LOG.debug(f"Creating params file for case {case_id}")
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
        workflow_parameters: dict = read_yaml(self.params)
        duplicate_keys = set(case_workflow_parameters.keys()) & set(workflow_parameters.keys())
        if duplicate_keys:
            raise CgDataError(f"Duplicate parameter keys found: {duplicate_keys}")
        parameters: dict = case_workflow_parameters | workflow_parameters
        curated_parameters: dict = replace_values_in_params_file(parameters)
        return curated_parameters

    def _get_case_parameters(
        self, case_id: str, case_path: Path, sample_sheet_path: Path
    ) -> RarediseaseParameters:
        """Return case-specific parameters for the analysis."""
        analysis_type: str = self._get_data_analysis_type(case_id)
        target_bed_file: str = self._get_target_bed_from_lims(case_id)
        sample_mapping_file: Path = self._create_sample_mapping_file(
            case_id=case_id, case_path=case_path
        )
        return RarediseaseParameters(
            input=sample_sheet_path,
            outdir=case_path,
            analysis_type=analysis_type,
            target_bed_file=target_bed_file,
            save_mapped_as_cram=True,
            vcfanno_extra_resources=f"{case_path}/{ScoutExportFileName.MANAGED_VARIANTS}",
            vep_filters_scout_fmt=f"{case_path}/{ScoutExportFileName.PANELS}",
            sample_id_map=sample_mapping_file,
        )

    def _get_data_analysis_type(self, case_id: str) -> str:
        """
        Return case analysis type (WEG, WGS, WTS or TGS). Assumes all case samples have the same
        analysis type.
        """
        sample: Sample = self.store.get_samples_by_case_id(case_id=case_id)[0]
        return sample.application_version.application.analysis_type

    def _get_target_bed_from_lims(self, case_id: str) -> str:
        """
        Get target bed filename from LIMS. Return an empty string if no target bed is found in LIMS.
        Raises:
            CgDataError: if the bed target capture version is not found in StatusDB.
        """
        case: Case = self.store.get_case_by_internal_id(internal_id=case_id)
        sample: Sample = case.samples[0]
        if sample.from_sample:
            sample: Sample = self.store.get_sample_by_internal_id(internal_id=sample.from_sample)
        target_bed_shortname: str | None = self.lims.capture_kit(lims_id=sample.internal_id)
        if not target_bed_shortname:
            return EMPTY_STRING
        bed_version: BedVersion | None = self.store.get_bed_version_by_short_name(
            bed_version_short_name=target_bed_shortname
        )
        if not bed_version:
            raise CgDataError(f"Bed-version {target_bed_shortname} does not exist")
        return bed_version.filename

    def _create_sample_mapping_file(self, case_id: str, case_path: Path) -> Path:
        """Create a sample mapping file for the case and returns its path."""
        file_path = Path(case_path, f"{case_id}_customer_internal_mapping").with_suffix(
            FileExtensions.CSV
        )
        content: list[list[str]] = [["customer_id", "internal_id"]]
        case: Case = self.store.get_case_by_internal_id(internal_id=case_id)
        for sample in case.samples:
            content.append([sample.name, sample.internal_id])
        write_csv(file_path=file_path, content=content)
        return file_path
