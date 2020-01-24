"""Click commands to store balsamic analyses"""
import datetime as dt
import logging
from pathlib import Path
import ruamel.yaml
import click

from cg.apps import hk, tb
from cg.exc import AnalysisNotFinishedError, AnalysisDuplicationError
from cg.store import Store

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def store(context):
    """Store results from MIP in housekeeper."""
    context.obj["db"] = Store(context.obj["database"])
    context.obj["tb_api"] = tb.TrailblazerAPI(context.obj)
    context.obj["hk_api"] = hk.HousekeeperAPI(context.obj)


@store.command()
@click.argument("config-stream", type=click.File("r"), required=False)
@click.pass_context
def analysis(context, config_stream):
    """Store a finished analysis in Housekeeper."""
    status = context.obj["db"]
    tb_api = context.obj["tb_api"]
    hk_api = context.obj["hk_api"]

    if not config_stream:
        LOG.error("provide a config, suggestions:")
        for analysis_obj in tb_api.analyses(status="completed", deleted=False)[:25]:
            click.echo(analysis_obj.config_path)
        context.abort()

    new_analysis = _gather_files_and_bundle_in_housekeeper(
        config_stream, context, hk_api, status, tb_api
    )

    status.add_commit(new_analysis)
    click.echo(click.style("included files in Housekeeper", fg="green"))


def _gather_files_and_bundle_in_housekeeper(
    config_stream, context, hk_api, status, tb_api
):
    """Function to gather files and bundle in housekeeper"""

    try:
        bundle_data = _add_analysis(config_stream)
    except AnalysisNotFinishedError as error:
        click.echo(click.style(error.message, fg="red"))
        context.abort()

    try:
        results = hk_api.add_bundle(bundle_data)
        if results is None:
            print(click.style("analysis version already added", fg="yellow"))
            context.abort()
        bundle_obj, version_obj = results
    except FileNotFoundError as error:
        click.echo(click.style(f"missing file: {error.args[0]}", fg="red"))
        context.abort()

    case_obj = _get_case(bundle_obj, status)
    _reset_analysis_action(case_obj)
    new_analysis = _create_analysis(bundle_data, case_obj, status, version_obj)
    version_date = version_obj.created_at.date()
    click.echo(f"new bundle added: {bundle_obj.name}, version {version_date}")
    _include_files_in_housekeeper(bundle_obj, context, hk_api, version_obj)

    return new_analysis


def _include_files_in_housekeeper(bundle_obj, context, hk_api, version_obj):
    """Function to include files in housekeeper"""
    try:
        hk_api.include(version_obj)
    except hk.VersionIncludedError as error:
        click.echo(click.style(error.message, fg="red"))
        context.abort()
    hk_api.add_commit(bundle_obj, version_obj)


def _create_analysis(bundle_data, case_obj, status, version_obj):
    """Function to create and return a new analysis database record"""
    pipeline = case_obj.links[0].sample.data_analysis
    pipeline = pipeline if pipeline else "balsamic"

    if status.analysis(family=case_obj, started_at=version_obj.created_at):
        raise AnalysisDuplicationError(
            f"Analysis object already exists for {case_obj.internal_id}{version_obj.created_at}"
        )

    new_analysis = status.add_analysis(
        pipeline=pipeline,
        version=bundle_data["pipeline_version"],
        started_at=version_obj.created_at,
        completed_at=dt.datetime.now(),
        primary=(len(case_obj.analyses) == 0),
    )
    new_analysis.family = case_obj
    return new_analysis


def _reset_analysis_action(case_obj):
    case_obj.action = None


def _get_case(bundle_obj, status):
    case_obj = status.family(bundle_obj.name)
    return case_obj


@store.command()
@click.pass_context
def completed(context):
    """Store all completed analyses."""
    hk_api = context.obj["hk_api"]
    for analysis_obj in context.obj["tb_api"].analyses(
        status="completed", deleted=False, workflow="balsamic"
    ):

        existing_record = hk_api.version(analysis_obj.family, analysis_obj.started_at)
        if existing_record:
            LOG.debug(
                "analysis stored: %s - %s", analysis_obj.family, analysis_obj.started_at
            )
            continue

        click.echo(click.style(f"storing case: {analysis_obj.case}", fg="blue"))
        with Path(analysis_obj.config_path).open() as config_stream:
            context.invoke(analysis, config_stream=config_stream)


def _parse_config(config_raw):
    return config_raw


def _parse_sampleinfo(sampleinfo_raw):
    return sampleinfo_raw


def _add_analysis(config_stream):
    """Gather information from MIP analysis to store."""
    config_raw = ruamel.yaml.safe_load(config_stream)
    config_data = _parse_config(config_raw)
    sampleinfo_raw = ruamel.yaml.safe_load(Path(config_data["sampleinfo_path"]).open())
    sampleinfo_data = _parse_sampleinfo(sampleinfo_raw)

    if sampleinfo_data["is_finished"] is False:
        raise AnalysisNotFinishedError("analysis not finished")

    new_bundle = _build_bundle(config_data, sampleinfo_data)
    return new_bundle


def _build_bundle(config_data: dict, sampleinfo_data: dict) -> dict:
    """Create a new bundle."""
    data = {
        "name": config_data["case"],
        "created": sampleinfo_data["date"],
        "pipeline_version": sampleinfo_data["version"],
        "files": _get_files(config_data, sampleinfo_data),
    }
    return data


def _get_files(config_data: dict, sampleinfo_data: dict) -> list:
    """Get all the files from the MIP files."""

    data = [
        {
            "path": config_data["config_path"],
            "tags": ["balsamic-config"],
            "archive": True,
        },
        {
            "path": config_data["sampleinfo_path"],
            "tags": ["sampleinfo"],
            "archive": True,
        },
        {
            "path": sampleinfo_data["pedigree_path"],
            "tags": ["pedigree"],
            "archive": False,
        },
        {"path": config_data["log_path"], "tags": ["mip-log"], "archive": True},
        {
            "path": sampleinfo_data["qcmetrics_path"],
            "tags": ["qcmetrics"],
            "archive": True,
        },
        {
            "path": sampleinfo_data["snv"]["bcf"],
            "tags": ["snv-bcf", "snv-gbcf"],
            "archive": True,
        },
        {
            "path": f"{sampleinfo_data['snv']['bcf']}.csi",
            "tags": ["snv-bcf-index", "snv-gbcf-index"],
            "archive": True,
        },
        {"path": sampleinfo_data["sv"]["bcf"], "tags": ["sv-bcf"], "archive": True},
        {
            "path": f"{sampleinfo_data['sv']['bcf']}.csi",
            "tags": ["sv-bcf-index"],
            "archive": True,
        },
        {
            "path": sampleinfo_data["peddy"]["ped_check"],
            "tags": ["peddy", "ped-check"],
            "archive": False,
        },
        {
            "path": sampleinfo_data["peddy"]["ped"],
            "tags": ["peddy", "ped"],
            "archive": False,
        },
        {
            "path": sampleinfo_data["peddy"]["sex_check"],
            "tags": ["peddy", "sex-check"],
            "archive": False,
        },
    ]

    # this key exists only for wgs
    if sampleinfo_data["str_vcf"]:
        data.append(
            {"path": sampleinfo_data["str_vcf"], "tags": ["vcf-str"], "archive": True}
        )

    for variant_type in ["snv", "sv"]:
        for output_type in ["clinical", "research"]:
            vcf_path = sampleinfo_data[variant_type][f"{output_type}_vcf"]
            if vcf_path is None:
                LOG.warning(f"missing file: {output_type} {variant_type} VCF")
                continue
            vcf_tag = f"vcf-{variant_type}-{output_type}"
            data.append({"path": vcf_path, "tags": [vcf_tag], "archive": True})
            data.append(
                {
                    "path": f"{vcf_path}.tbi"
                    if variant_type == "snv"
                    else f"{vcf_path}.csi",
                    "tags": [f"{vcf_tag}-index"],
                    "archive": True,
                }
            )

    for sample_data in sampleinfo_data["samples"]:
        data.append(
            {
                "path": sample_data["sambamba"],
                "tags": ["coverage", sample_data["id"]],
                "archive": False,
            }
        )

        # Bam pre-processing
        bam_path = sample_data["bam"]
        bai_path = f"{bam_path}.bai"
        if not Path(bai_path).exists():
            bai_path = bam_path.replace(".bam", ".bai")

        data.append(
            {"path": bam_path, "tags": ["bam", sample_data["id"]], "archive": False}
        )
        data.append(
            {
                "path": bai_path,
                "tags": ["bam-index", sample_data["id"]],
                "archive": False,
            }
        )

        # Only for wgs data
        # Downsamples MT bam pre-processing
        if sample_data["subsample_mt"]:
            mt_bam_path = sample_data["subsample_mt"]
            mt_bai_path = f"{mt_bam_path}.bai"
            if not Path(mt_bai_path).exists():
                mt_bai_path = mt_bam_path.replace(".bam", ".bai")
            data.append(
                {
                    "path": mt_bam_path,
                    "tags": ["bam-mt", sample_data["id"]],
                    "archive": False,
                }
            )
            data.append(
                {
                    "path": mt_bai_path,
                    "tags": ["bam-mt-index", sample_data["id"]],
                    "archive": False,
                }
            )

        cytosure_path = sample_data["vcf2cytosure"]
        data.append(
            {
                "path": cytosure_path,
                "tags": ["vcf2cytosure", sample_data["id"]],
                "archive": False,
            }
        )

    return data
