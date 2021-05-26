"""Tests for the shipping api"""
import logging
from pathlib import Path
from typing import Dict

import pytest

from cg.apps.shipping import ShippingAPI


def build_expected_output_string(
    api: ShippingAPI, app_name: str = None, app_config: Path = None
) -> str:
    """Create a string that is expected to be logged when deploying with shipping"""
    output = ["Running", "command", api.binary_path, "--host-config", api.host_config]
    if app_name:
        output.extend(["--tool-name", app_name])
    if app_config:
        output.extend(["--app-config", str(app_config)])
    output.append("deploy")
    return " ".join(output)


def test_init_shipping_api(shipping_configs: Dict[str, str]):
    """Test to initialize the shipping api"""
    # GIVEN a config with some information about host file and binary
    configs = shipping_configs

    # WHEN initializing the api
    api = ShippingAPI(config=configs)

    # THEN assert that the base command is as expected
    assert api.process.base_call == [
        configs["binary_path"],
        "--host-config",
        configs["host_config"],
    ]


def test_shipping_api_deploy_tool_name(shipping_api: ShippingAPI, caplog):
    """Test to run deploy with the shipping api with just a tool name"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a shipping api and a dummy tool name
    tool_name = "dummy"

    # WHEN running the deploy method
    shipping_api.deploy(app_name=tool_name)

    # THEN assert that call to deploy was communicated
    output_str = build_expected_output_string(api=shipping_api, app_name=tool_name)
    assert output_str in caplog.text


def test_shipping_api_deploy_app_config(shipping_api: ShippingAPI, caplog):
    """Test to run deploy with the shipping api providing an app config"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a shipping api and a dummy app config
    app_config = Path("path/to/app_config.yml")
    app_name = "myapp"

    # WHEN running the deploy method
    shipping_api.deploy(app_name=app_name, app_config=app_config)

    # THEN assert that call to deploy was communicated
    output_str = build_expected_output_string(api=shipping_api, app_config=app_config)

    assert output_str in caplog.text


def test_shipping_api_deploy_shipping(shipping_api: ShippingAPI, caplog):
    """Test to run deploy with shipping itself"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a shipping api
    # GIVEN a shipping app name
    app_name = "shipping"

    # WHEN running the deploy method shipping method
    shipping_api.deploy(app_name=app_name)

    # THEN assert that call to deploy was communicated
    output_str = build_expected_output_string(api=shipping_api, app_name=app_name)
    assert output_str in caplog.text


def test_shipping_api_deploy_genotype(shipping_api: ShippingAPI, caplog):
    """Test to run deploy with genotype"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a shipping api
    # GIVEN a genotype app name
    app_name = "genotype"

    # WHEN running the deploy method shipping method
    shipping_api.deploy(app_name=app_name)

    # THEN assert that call to deploy was communicated
    output_str = build_expected_output_string(api=shipping_api, app_name=app_name)
    assert output_str in caplog.text
