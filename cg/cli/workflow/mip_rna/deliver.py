# -*- coding: utf-8 -*- import logging

import logging
import os
from pathlib import Path

import click
from cg.apps.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.meta.deliver import DeliverAPI
from cg.store import Store

LOG = logging.getLogger(__name__)

CASE_TAGS = []

SAMPLE_TAGS = ["bam", "bam-index", "cram", "cram-index"]


@click.group()
@click.pass_context
def deliver(context):
    """Deliver stuff."""
    context.obj["status_db"] = Store(context.obj["database"])
    context.obj["deliver_api"] = DeliverAPI(
        db=context.obj["status_db"],
        hk_api=HousekeeperAPI(context.obj),
        lims_api=LimsAPI(context.obj),
        case_tags=CASE_TAGS,
        sample_tags=SAMPLE_TAGS,
    )


@deliver.command()
@click.option("-V", "--version", help="version (date) of bundle")
@click.option("-t", "--tag", multiple=True, help="the housekeeper tag(s)")
@click.option(
    "-i",
    "--inbox",
    "inbox_path",
    default="/home/proj/production/customers/{customer}/inbox/{case}/",
    help="customer inbox",
)
@click.argument("case", required=False)
@click.pass_context
def inbox(context, case, version, tag, inbox_path):
    """Link files from HK to cust inbox."""

    if not case:
        _suggest_cases_to_deliver(context.obj["status_db"])
        context.abort()

    case_obj = context.obj["status_db"].family(case)
    if case_obj is None:
        LOG.error("Case '%s' not found.", case)
        context.abort()

    files = context.obj["deliver_api"].get_post_analysis_case_files(
        case=case, version=version, tags=tag
    )
    if not files:
        LOG.warning("No case files found")

    for file_obj in files:
        out_dir = Path(
            inbox_path.format(case=case_obj.name, customer=case_obj.customer.internal_id)
        )
        out_dir.mkdir(parents=True, exist_ok=True)

        out_path = _generate_case_delivery_path(case, case_obj, file_obj, out_dir)
        in_path = Path(file_obj.full_path)

        if not out_path.exists():
            os.link(in_path, out_path)
            LOG.info("linked file: %s -> %s", in_path, out_path)
        else:
            LOG.info("Target file exists: %s", out_path)

    link_obj = context.obj["status_db"].family_samples(case)
    if not link_obj:
        LOG.warning("No sample files found.")

    for case_sample in link_obj:
        sample_obj = case_sample.sample
        files = context.obj["deliver_api"].get_post_analysis_sample_files(
            case=case, sample=sample_obj.internal_id, version=version, tag=tag
        )

        if not files:
            LOG.warning("No sample files found for '%s'.", sample_obj.internal_id)

        for file_obj in files:
            out_dir = Path(
                inbox_path.format(case=case_obj.name, customer=case_obj.customer.internal_id)
            )
            out_dir = out_dir.joinpath(sample_obj.name)
            out_dir.mkdir(parents=True, exist_ok=True)

            out_path = _generate_sample_delivery_path(file_obj, out_dir, sample_obj)
            in_path = Path(file_obj.full_path)

            if not out_path.exists():
                os.link(in_path, out_path)
                LOG.info("linked file: %s -> %s", in_path, out_path)
            else:
                LOG.info("Target file exists: %s", out_path)


def _generate_case_delivery_path(case, case_obj, file_obj, out_dir):
    return Path(f"{out_dir / Path(file_obj.path).name.replace(case, case_obj.name)}")


def _generate_sample_delivery_path(file_obj, out_dir, sample_obj):
    return Path(
        f"{out_dir / Path(file_obj.path).name.replace(sample_obj.internal_id, sample_obj.name)}"
    )


def _suggest_cases_to_deliver(store):
    LOG.warning("provide a case, suggestions:")

    for case_obj in store.analyses_to_deliver(pipeline="mip", limit=50):
        click.echo(case_obj)
