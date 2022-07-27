from pathlib import Path

from cg.io.json import read_json


def test_get_content_from_file(mip_json_order_form_path: Path):
    """
    Tests read_yaml
    """
    # GIVEN a json file

    # WHEN reading the json file
    raw_mip_order_form_info: dict = read_json(file_path=mip_json_order_form_path)

    # Then assert a dict is returned
    assert isinstance(raw_mip_order_form_info, dict)
