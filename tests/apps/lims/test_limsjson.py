from cg.apps.lims import limsjson


def test_parsing_rml_json(rml_order_to_submit: dict) -> None:
    # GIVEN a path to a RML limsjson with 2 sample in a pool
    # WHEN parsing the file
    data = limsjson.parse_json(rml_order_to_submit)

    # THEN it should determine the type of project and customer
    assert data["project_type"] == "rml"
    assert data["customer"] == "cust000"
    assert data["comment"] == "order comment"

    # ... and find all samples
    assert len(data["items"]) == 4

    # ... and collect relevant sample data
    sample_data = data["items"][2]
    assert sample_data["name"] == "sample3"
    assert sample_data["pool"] == "pool-2"
    assert sample_data["application"] == "RMLS05R150"
    assert sample_data["data_analysis"] == "fluffy"
    assert sample_data["volume"] == "30"
    assert sample_data["concentration"] == "5"
    assert sample_data["index"] == "IDT DupSeq 10 bp Set B"
    assert sample_data["index_number"] == "3"
    assert sample_data.get("container_name") is None
    assert sample_data["rml_plate_name"] == "plate1"
    assert sample_data.get("well_position") is None
    assert sample_data["well_position_rml"] == "A:1"
    assert sample_data["index_sequence"] == "A01 - D701-D501 (ATTACTCG-TATAGCCT)"
    assert sample_data["comment"] == "test comment"
    assert sample_data["concentration_sample"] == "6"


def test_parsing_mip_json(mip_json_order_to_submit: dict):

    # GIVEN an order form for a Scout order with samples, 1 trio, in a plate
    # WHEN parsing the order form
    data = limsjson.parse_json(mip_json_order_to_submit)

    # THEN it should detect the type of project
    assert data["project_type"] == "mip-dna"
    assert data["customer"] == "cust000"

    # ... and it should find and group all samples in families
    assert len(data["items"]) == 7

    # ... and collect relevant data about the families
    duo_family = data["items"][4]
    assert len(duo_family["samples"]) == 2
    assert duo_family["name"] == "F0018192"
    assert duo_family["priority"] == "standard"
    assert set(duo_family["panels"]) == set(["CTD"])
    assert duo_family["require_qcok"] is False

    # ... and collect relevant info about the samples
    sibling_sample = duo_family["samples"][0]
    assert sibling_sample["name"] == "2020-16171-81"
    assert sibling_sample["application"] == "WGSPCFC030"
    assert sibling_sample["sex"] == "female"

    # family-id on the family
    # customer on the order (data)
    # require-qc-ok on the family
    assert sibling_sample["source"] == "blood"
    assert sibling_sample.get("tumour") is None
    assert sibling_sample["container"] == "96 well plate"
    assert sibling_sample["container_name"] == "2020-16171-81"
    assert sibling_sample["well_position"] == "A:1"

    # panels on the family
    assert sibling_sample["status"] == "affected"
    assert sibling_sample["mother"] == ""
    assert sibling_sample["father"] == ""
    assert sibling_sample["quantity"] == ""
    assert sibling_sample["comment"] == "F0018192-0 Data finns 2019-19202 duo med bror "
