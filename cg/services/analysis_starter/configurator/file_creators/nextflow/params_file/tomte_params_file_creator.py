from cg.io.yaml import read_yaml
from cg.models.tomte.tomte import TomteParameters
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.abstract import (
    ParamsFileCreator,
)


class TomteParamsFileCreator(ParamsFileCreator):

    def _get_content(self, case_id: str) -> TomteParameters:
        case_parameters = TomteParameters(
            input=self.get_sample_sheet_path(case_id=case_id),
            outdir=self.get_case_path(case_id=case_id),
            gene_panel_clinical_filter=self.get_gene_panels_path(case_id=case_id),
            tissue=self.get_case_source_type(case_id=case_id),
            genome=self.get_genome_build(case_id=case_id),
        ).model_dump()

        workflow_params = self._get_workflow_params()
        workflow_parameters: dict = built_workflow_parameters | (workflow_params)
        replaced_workflow_parameters: dict = self.replace_values_in_params_file(
            workflow_parameters=workflow_parameters
        )

    def _get_workflow_params(self) -> dict:
        return read_yaml(self.params)
