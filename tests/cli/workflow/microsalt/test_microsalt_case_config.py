""" This file groups all tests related to microsalt case config creation """

import logging
from pathlib import Path

from cg.apps.lims import LimsAPI
from cg.cli.workflow.microsalt.base import config_case
from cg.models.cg_config import CGConfig
from click.testing import CliRunner
from snapshottest import Snapshot

EXIT_SUCCESS = 0


def test_no_arguments(cli_runner: CliRunner, base_context: CGConfig, caplog):
    """Test command without any options"""

    # GIVEN

    # WHEN dry running without anything specified
    result = cli_runner.invoke(config_case, obj=base_context)

    # THEN command should mention missing arguments
    assert result.exit_code != EXIT_SUCCESS
    assert "Missing argument" in result.output


def test_no_sample_found(cli_runner: CliRunner, base_context: CGConfig, caplog):
    """Test missing sample command """

    # GIVEN a not existing sample
    microbial_sample_id = "not_existing_sample"

    # WHEN dry running a sample name
    result = cli_runner.invoke(config_case, [microbial_sample_id, "-s"], obj=base_context)

    # THEN command should mention missing sample
    assert result.exit_code != EXIT_SUCCESS
    with caplog.at_level(logging.ERROR):
        assert f"No sample found with id: {microbial_sample_id}" in caplog.text


def test_no_order_found(
    cli_runner: CliRunner, base_context: CGConfig, caplog, invalid_ticket_number: int
):
    """Test missing order command """

    # GIVEN a not existing ticket
    ticket = invalid_ticket_number

    # WHEN dry running a order name
    result = cli_runner.invoke(config_case, [ticket, "-t"], obj=base_context)

    # THEN command should mention missing order
    assert result.exit_code != EXIT_SUCCESS
    with caplog.at_level(logging.ERROR):
        assert f"No case found for ticket number:  {ticket}" in caplog.text


def test_no_case_found(cli_runner: CliRunner, base_context: CGConfig, caplog):
    """Test missing sample and order command """

    # GIVEN a not existing order
    microbial_case = "smallzergling"

    # WHEN dry running a order name
    result = cli_runner.invoke(
        config_case,
        [microbial_case],
        obj=base_context,
    )

    # THEN command should mention missing order
    assert result.exit_code != EXIT_SUCCESS
    with caplog.at_level(logging.ERROR):
        assert f"No case found with the id:  {microbial_case}" in caplog.text


def test_dry_sample(
    cli_runner: CliRunner,
    base_context: CGConfig,
    microbial_sample_id: str,
    snapshot: Snapshot,
    lims_api: LimsAPI,
):
    """Test working dry command for sample"""

    # GIVEN project, organism and reference genome is specified in lims
    lims_sample = lims_api.sample(microbial_sample_id)
    lims_sample.sample_data["project"] = {"id": "microbial_order_test"}

    # WHEN dry running a sample name
    result = cli_runner.invoke(config_case, [microbial_sample_id, "-s", "-d"], obj=base_context)

    # THEN command should give us a json dump
    assert result.exit_code == EXIT_SUCCESS


def test_dry_order(
    cli_runner: CliRunner, base_context: CGConfig, microbial_ticket, snapshot: Snapshot
):
    """Test working dry command for a order"""

    # GIVEN

    # WHEN dry running a sample name
    result = cli_runner.invoke(
        config_case,
        [microbial_ticket, "-t", "-d"],
        obj=base_context,
    )

    # THEN command should give us a json dump
    assert result.exit_code == EXIT_SUCCESS


def test_sample(base_context, cli_runner, lims_api, microbial_sample_id, snapshot: Snapshot):
    """Test working command for sample"""

    # GIVEN an existing queries path
    Path(base_context.meta_apis["analysis_api"].queries_path).mkdir(exist_ok=True)
    lims_api.sample(microbial_sample_id).sample_data["project"] = {"id": "microbial_order_test"}

    # WHEN dry running a sample name
    result = cli_runner.invoke(config_case, [microbial_sample_id, "-s"], obj=base_context)

    # THEN command should give us a json dump
    assert result.exit_code == EXIT_SUCCESS


def test_gonorrhoeae(cli_runner: CliRunner, base_context: CGConfig, microbial_sample_id):
    """ Test if the substitution of the organism happens """
    # GIVEN a sample with organism set to gonorrhea
    sample_obj = base_context.meta_apis["analysis_api"].status_db.sample(microbial_sample_id)
    sample_obj.organism.internal_id = "gonorrhoeae"

    # WHEN getting the case config
    result = cli_runner.invoke(config_case, [microbial_sample_id, "-d", "-s"], obj=base_context)

    # THEN the organism should now be  ...
    assert "Neisseria spp." in result.output


def test_cutibacterium_acnes(cli_runner: CliRunner, base_context: CGConfig, microbial_sample_id):
    """ Test if this bacteria gets its name changed """
    # GIVEN a sample with organism set to Cutibacterium acnes
    sample_obj = base_context.meta_apis["analysis_api"].status_db.sample(microbial_sample_id)
    sample_obj.organism.internal_id = "Cutibacterium acnes"

    # WHEN getting the case config
    result = cli_runner.invoke(config_case, [microbial_sample_id, "-s", "-d"], obj=base_context)

    # THEN the organism should now be ....
    assert "Propionibacterium acnes" in result.output


def test_vre_nc_017960(cli_runner: CliRunner, base_context: CGConfig, microbial_sample_id):
    """ Test if this bacteria gets its name changed """
    # GIVEN a sample with organism set to VRE
    sample_obj = base_context.meta_apis["analysis_api"].status_db.sample(microbial_sample_id)
    sample_obj.organism.internal_id = "VRE"
    sample_obj.organism.reference_genome = "NC_017960.1"

    # WHEN getting the case config
    result = cli_runner.invoke(config_case, [microbial_sample_id, "-s", "-d"], obj=base_context)

    # THEN the organism should now be ....
    assert "Enterococcus faecium" in result.output


def test_vre_nc_004668(cli_runner: CliRunner, base_context: CGConfig, microbial_sample_id):
    """ Test if this bacteria gets its name changed """
    # GIVEN a sample with organism set to VRE
    sample_obj = base_context.meta_apis["analysis_api"].status_db.sample(microbial_sample_id)
    sample_obj.organism.internal_id = "VRE"
    sample_obj.organism.reference_genome = "NC_004668.1"

    # WHEN getting the case config
    result = cli_runner.invoke(config_case, [microbial_sample_id, "-s", "-d"], obj=base_context)

    # THEN the organism should now be ....
    assert "Enterococcus faecalis" in result.output


def test_vre_comment(cli_runner: CliRunner, base_context: CGConfig, lims_api, microbial_sample_id):
    """ Test if this bacteria gets its name changed """
    # GIVEN a sample with organism set to VRE and a comment set in LIMS
    sample_obj = base_context.meta_apis["analysis_api"].status_db.sample(microbial_sample_id)
    sample_obj.organism.internal_id = "VRE"
    lims_sample = lims_api.sample(microbial_sample_id)
    lims_sample.sample_data["comment"] = "ABCD123"

    # WHEN getting the case config
    result = cli_runner.invoke(config_case, [microbial_sample_id, "-s", "-d"], obj=base_context)

    # THEN the organism should now be ....
    assert "ABCD123" in result.output
