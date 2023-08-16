"""Utility function returning CommandArgs."""

from cg.models.rnafusion.rnafusion import CommandArgs
from cg.meta.workflow.taxprofiler import TaxprofilerAnalysisAPI
from cg.constants.nf_analysis import NfTowerStatus


def get_command_args(
    analysis_api: TaxprofilerAnalysisAPI,
    case_id: str,
    log: str,
    work_dir: str,
    from_start: bool,
    profile: str,
    config: str,
    params_file: str,
    revision: str,
) -> CommandArgs:
    return CommandArgs(
        log=analysis_api.get_log_path(
            case_id=case_id,
            pipeline=analysis_api.pipeline,
            log=log,
        ),
        work_dir=analysis_api.get_workdir_path(case_id=case_id, work_dir=work_dir),
        resume=not from_start,
        profile=analysis_api.get_profile(profile=profile),
        config=analysis_api.get_nextflow_config_path(nextflow_config=config),
        params_file=analysis_api.get_params_file_path(case_id=case_id, params_file=params_file),
        name=case_id,
        revision=revision or analysis_api.revision,
        wait=NfTowerStatus.SUBMITTED,
    )
