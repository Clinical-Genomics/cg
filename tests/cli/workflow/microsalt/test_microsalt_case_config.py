""" This file groups all tests related to microsalt case config creation """

import logging
from pathlib import Path

from cg.apps.lims import LimsAPI
from snapshottest import Snapshot

from cg.cli.workflow.microsalt.base import config_case

EXIT_SUCCESS = 0


def test_no_arguments(cli_runner, base_context, caplog):
    """Test command without any options"""

    # GIVEN

    # WHEN dry running without anything specified
    result = cli_runner.invoke(config_case, obj=base_context)

    # THEN command should mention missing arguments
    assert result.exit_code != EXIT_SUCCESS
    assert "Aborted!" in result.output
    with caplog.at_level(logging.ERROR):
        assert "Provide ticket and/or sample" in caplog.text


def test_no_sample_found(cli_runner, base_context, caplog):
    """Test missing sample command """

    # GIVEN a not existing sample
    microbial_sample_id = "not_existing_sample"

    # WHEN dry running a sample name
    result = cli_runner.invoke(config_case, [microbial_sample_id], obj=base_context)

    # THEN command should mention missing sample
    assert result.exit_code != EXIT_SUCCESS
    with caplog.at_level(logging.ERROR):
        assert f"No sample found for that ticket/sample_id" in caplog.text


def test_no_order_found(cli_runner, base_context, caplog):
    """Test missing order command """

    # GIVEN a not existing ticket
    ticket = -1

    # WHEN dry running a order name
    result = cli_runner.invoke(config_case, ["--ticket", ticket], obj=base_context)

    # THEN command should mention missing order
    assert result.exit_code != EXIT_SUCCESS
    with caplog.at_level(logging.ERROR):
        assert f"No sample found for that ticket/sample_id" in caplog.text


def test_no_sample_order_found(cli_runner, base_context, caplog):
    """Test missing sample and order command """

    # GIVEN a not existing order
    microbial_sample_id = "not_existing_sample"
    microbial_ticket = "not_existing_order"

    # WHEN dry running a order name
    result = cli_runner.invoke(
        config_case,
        ["--ticket", microbial_ticket, microbial_sample_id],
        obj=base_context,
    )

    # THEN command should mention missing order
    assert result.exit_code != EXIT_SUCCESS
    with caplog.at_level(logging.ERROR):
        assert f"No sample found for that ticket/sample_id" in caplog.text


def test_dry_sample(
    cli_runner, base_context, microbial_sample_id, snapshot: Snapshot, lims_api: LimsAPI
):
    """Test working dry command for sample"""

    # GIVEN project, organism and reference genome is specified in lims
    lims_sample = lims_api.sample(microbial_sample_id)
    lims_sample.sample_data["project"] = {"id": "microbial_order_test"}

    # WHEN dry running a sample name
    result = cli_runner.invoke(config_case, ["--dry-run", microbial_sample_id], obj=base_context)

    # THEN command should give us a json dump
    assert result.exit_code == EXIT_SUCCESS
    snapshot.assert_match(result.output)


def test_dry_sample_order(
    cli_runner,
    base_context,
    microbial_sample_id,
    microbial_ticket,
    snapshot: Snapshot,
    lims_api: LimsAPI,
):
    """Test working dry command for sample in a order"""

    # GIVEN
    lims_sample = lims_api.sample(microbial_sample_id)
    lims_sample.sample_data["project"] = {"id": "microbial_order_test"}

    # WHEN dry running a sample name
    result = cli_runner.invoke(
        config_case,
        ["--dry-run", "--ticket", microbial_ticket, microbial_sample_id],
        obj=base_context,
    )

    # THEN command should give us a json dump
    assert result.exit_code == EXIT_SUCCESS
    snapshot.assert_match(result.output)


def test_dry_order(cli_runner, base_context, microbial_ticket, snapshot: Snapshot):
    """Test working dry command for a order"""

    # GIVEN

    # WHEN dry running a sample name
    result = cli_runner.invoke(
        config_case,
        ["--dry-run", "--ticket", microbial_ticket],
        obj=base_context,
    )

    # THEN command should give us a json dump
    assert result.exit_code == EXIT_SUCCESS
    snapshot.assert_match(result.output)


def test_sample(
    base_context, cli_runner, lims_api, microbial_sample_id, queries_path, snapshot: Snapshot
):
    """Test working command for sample"""

    # GIVEN an existing queries path
    Path(queries_path).mkdir(exist_ok=True)
    lims_api.sample(microbial_sample_id).sample_data["project"] = {"id": "microbial_order_test"}

    # WHEN dry running a sample name
    result = cli_runner.invoke(config_case, [microbial_sample_id], obj=base_context)

    # THEN command should give us a json dump
    assert result.exit_code == EXIT_SUCCESS
    outfilename = queries_path / microbial_sample_id
    outfilename = outfilename.with_suffix(".json")
    with open(outfilename, "r") as outputfile:
        snapshot.assert_match(outputfile.readlines())


def test_gonorrhoeae(cli_runner, microsalt_store, base_context, microbial_sample_id):
    """ Test if the substitution of the organism happens """
    # GIVEN a sample with organism set to gonorrhea
    sample_obj = microsalt_store.sample(microbial_sample_id)
    sample_obj.organism.internal_id = "gonorrhoeae"

    # WHEN getting the case config
    result = cli_runner.invoke(config_case, ["--dry-run", microbial_sample_id], obj=base_context)

    # THEN the organism should now be  ...
    assert "Neisseria spp." in result.output


def test_cutibacterium_acnes(cli_runner, microsalt_store, base_context, microbial_sample_id):
    """ Test if this bacteria gets its name changed """
    # GIVEN a sample with organism set to Cutibacterium acnes
    sample_obj = microsalt_store.sample(microbial_sample_id)
    sample_obj.organism.internal_id = "Cutibacterium acnes"

    # WHEN getting the case config
    result = cli_runner.invoke(config_case, ["--dry-run", microbial_sample_id], obj=base_context)

    # THEN the organism should now be ....
    assert "Propionibacterium acnes" in result.output


def test_vre_nc_017960(cli_runner, microsalt_store, base_context, microbial_sample_id):
    """ Test if this bacteria gets its name changed """
    # GIVEN a sample with organism set to VRE
    sample_obj = microsalt_store.sample(microbial_sample_id)
    sample_obj.organism.internal_id = "VRE"
    sample_obj.organism.reference_genome = "NC_017960.1"

    # WHEN getting the case config
    result = cli_runner.invoke(config_case, ["--dry-run", microbial_sample_id], obj=base_context)

    # THEN the organism should now be ....
    assert "Enterococcus faecium" in result.output


def test_vre_nc_004668(cli_runner, microsalt_store, base_context, microbial_sample_id):
    """ Test if this bacteria gets its name changed """
    # GIVEN a sample with organism set to VRE
    sample_obj = microsalt_store.sample(microbial_sample_id)
    sample_obj.organism.internal_id = "VRE"
    sample_obj.organism.reference_genome = "NC_004668.1"

    # WHEN getting the case config
    result = cli_runner.invoke(config_case, ["--dry-run", microbial_sample_id], obj=base_context)

    # THEN the organism should now be ....
    assert "Enterococcus faecalis" in result.output


def test_vre_comment(cli_runner, microsalt_store, lims_api, base_context, microbial_sample_id):
    """ Test if this bacteria gets its name changed """
    # GIVEN a sample with organism set to VRE and a comment set in LIMS
    sample_obj = microsalt_store.sample(microbial_sample_id)
    sample_obj.organism.internal_id = "VRE"
    lims_sample = lims_api.sample(microbial_sample_id)
    lims_sample.sample_data["comment"] = "ABCD123"

    # WHEN getting the case config
    result = cli_runner.invoke(config_case, ["--dry-run", microbial_sample_id], obj=base_context)

    # THEN the organism should now be ....
    assert "ABCD123" in result.output
