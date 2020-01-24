# """Tests for cg.cli.store.balsamic"""
# import logging
# from datetime import datetime
#
from cg.cli.workflow.balsamic.store import analysis

# from click import Path
#
EXIT_SUCCESS = 0


def test_command_suggests(cli_runner, store_context, caplog):
    """Test store command without arguments"""

    # GIVEN no cases available for storage

    # WHEN calling analysis
    result = cli_runner.invoke(analysis, obj=store_context)

    # THEN command should suggest no files to store
    assert result.exit_code != EXIT_SUCCESS
    assert "provide a config, suggestions" in caplog.text


def test_store_analysis(cli_runner, base_context, meta_file):
    """Test store command without arguments"""

    # GIVEN a meta file for a balsamic analysis

    # WHEN calling store with meta file
    result = cli_runner.invoke(analysis, [meta_file], obj=base_context)

    # THEN we should not get a message that the analysis has been stored
    print(result.output)
    print(result.exception)
    assert result.exit_code == EXIT_SUCCESS
    assert "included files in Housekeeper" in result.output


# def test_already_stored_analysis(cli_runner, base_context, meta_file):
#     """Test store command without arguments"""
#
#     # GIVEN a meta file for a balsamic analysis
#     # GIVEN the analysis has already been stored
#     cli_runner.invoke(balsamic, [meta_file], obj=base_context)
#
#     # WHEN calling store with meta file
#     result = cli_runner.invoke(balsamic, [meta_file], obj=base_context)
#
#     # THEN we should get a message that the analysis has previously been stored
#     assert result.exit_code == EXIT_SUCCESS
#     assert "analysis version already added" in result.output
#
#
# def ensure_application_version(
#     disk_store, application_tag="dummy_tag", is_external=False
# ):
#     """utility function to return existing or create application version for tests"""
#     application = disk_store.application(tag=application_tag)
#     if not application:
#         application = disk_store.add_application(
#             tag=application_tag,
#             category="wgs",
#             description="dummy_description",
#             is_external=is_external,
#         )
#         disk_store.add_commit(application)
#
#     prices = {"standard": 10, "priority": 20, "express": 30, "research": 5}
#     version = disk_store.application_version(application, 1)
#     if not version:
#         version = disk_store.add_version(
#             application, 1, valid_from=datetime.now(), prices=prices
#         )
#
#         disk_store.add_commit(version)
#     return version
#
#
# def ensure_customer(disk_store, customer_id="cust_test"):
#     """utility function to return existing or create customer for tests"""
#     customer_group = disk_store.customer_group("dummy_group")
#     if not customer_group:
#         customer_group = disk_store.add_customer_group("dummy_group", "dummy group")
#
#         customer = disk_store.add_customer(
#             internal_id=customer_id,
#             name="Test Customer",
#             scout_access=False,
#             customer_group=customer_group,
#             invoice_address="dummy_address",
#             invoice_reference="dummy_reference",
#         )
#         disk_store.add_commit(customer)
#     customer = disk_store.customer(customer_id)
#     return customer
#
#
# def add_sample(disk_store, sample_id="test_sample", is_external=False, flowcell=None):
#     """utility function to add a sample to use in tests"""
#     customer = ensure_customer(disk_store)
#     application_version_id = ensure_application_version(
#         disk_store, is_external=is_external
#     ).id
#     sample = disk_store.add_sample(name=sample_id, sex="female")
#     sample.application_version_id = application_version_id
#     sample.customer = customer
#     sample.is_external = is_external
#     if flowcell:
#         sample.flowcells.append(flowcell)
#     disk_store.add_commit(sample)
#     return sample
#
#
# def add_flowcell(disk_store, sample_id="flowcell_test", sample=None):
#     """utility function to get a flowcell to use in tests"""
#     flowcell = disk_store.add_flowcell(
#         name=sample_id,
#         sequencer="dummy_sequencer",
#         sequencer_type="hiseqx",
#         date=datetime.now(),
#     )
#     if sample:
#         flowcell.samples.append(sample)
#     disk_store.add_commit(flowcell)
#     return flowcell
#
#
# def add_panel(disk_store, panel_id="panel_test", customer_id="cust_test"):
#     """utility function to add a panel to use in tests"""
#     customer = ensure_customer(disk_store, customer_id)
#     panel = disk_store.add_panel(
#         customer=customer,
#         name=panel_id,
#         abbrev=panel_id,
#         version=1.0,
#         date=datetime.now(),
#         genes=1,
#     )
#     disk_store.add_commit(panel)
#     return panel
#
#
# def add_family(disk_store, family_id="family_test", customer_id="cust_test"):
#     """utility function to add a family to use in tests"""
#     panel_name = add_panel(disk_store).name
#     customer = ensure_customer(disk_store, customer_id)
#     family = disk_store.add_family(name=family_id, panels=panel_name)
#     family.customer = customer
#     disk_store.add_commit(family)
#     return family
#
#
# def add_relationship(disk_store, sample, family):
#     """utility function to add a sample to use in tests"""
#     link = disk_store.relate_sample(sample=sample, family=family, status="unknown")
#     disk_store.add_commit(link)
#     return link
