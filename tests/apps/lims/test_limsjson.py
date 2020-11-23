from cg.apps.lims import limsjson


def test_parsing_rml_json(rml_order_to_submit):
    # GIVEN a path to a RML limsjson with 2 sample in a pool
    # WHEN parsing the file
    data = limsjson.parse_json(rml_order_to_submit)

    # THEN it should determine the type of project and customer
    assert data["project_type"] == "rml"
    assert data["customer"] == "cust000"
    assert data["comment"] == "order comment"

    # ... and find all samples
    assert len(data["items"]) == 2

    # ... and collect relevant sample data
    sample_data = data["items"][0]
    assert sample_data["name"] == "sample1"
    assert sample_data["pool"] == "pool-1"
    assert sample_data["application"] == "RMLS05R150"
    assert sample_data["data_analysis"] == "fluffy"
    assert sample_data["volume"] == "30"
    assert sample_data["concentration"] == "5"
    assert sample_data["index"] == "TruSeq Custom Amplicon Dual-index (A7-A5)"
    assert sample_data["index_number"] == "1"
    assert sample_data.get("container_name") is None
    assert sample_data["rml_plate_name"] == "plate"
    assert sample_data.get("well_position") is None
    assert sample_data["well_position_rml"] == "A:1"
    assert sample_data["index_sequence"] == "A01 - D701-D501 (ATTACTCG-TATAGCCT)"
    assert sample_data["comment"] == "test comment"
    assert sample_data["concentration_sample"] == "6"


def test_parsing_mip_json(mip_order_to_submit):

    # GIVEN an order form for a Scout order with samples, 1 trio, in a plate

    # WHEN parsing the order form
    data = limsjson.parse_json(mip_order_to_submit)

    # THEN it should detect the type of project
    assert data["project_type"] == "mip-dna"
    assert data["customer"] == "cust000"

    # ... and it should find and group all samples in families
    print(f'{data["items"]=}')
    assert len(data["items"]) == 2

    # ... and collect relevant data about the families
    trio_family = data["items"][0]

    assert len(trio_family["samples"]) == 3
    assert trio_family["name"] == "family1"
    assert trio_family["priority"] == "standard"
    assert set(trio_family["panels"]) == set(["IEM"])
    assert trio_family["require_qcok"] is True

    # ... and collect relevant info about the samples
    proband_sample = trio_family["samples"][0]
    assert proband_sample["name"] == "sample1"
    assert proband_sample["container"] == "96 well plate"
    assert proband_sample["data_analysis"] == "mip-dna"
    assert proband_sample["application"] == "WGTPCFC030"
    assert proband_sample["sex"] == "female"

    # family-id on the family
    # customer on the order (data)
    # require-qc-ok on the family
    assert proband_sample["source"] == "tissue (fresh frozen)"
    assert proband_sample["tumour"] is True

    assert proband_sample["container_name"] == "CMMS"
    assert proband_sample["well_position"] == "A:1"

    # panels on the family
    assert proband_sample["status"] == "affected"
    assert proband_sample["mother"] == "sample2"
    assert proband_sample["father"] == "sample3"
    assert proband_sample["quantity"] == "220"
    assert proband_sample["comment"] == "comment"


# TODO:
# def test_parsing_fastq_json(fastq_order_to_submit):
#
#     # GIVEN a FASTQ limsjson with 2 samples, one normal, one tumour
#     # WHEN parsing the file
#     data = limsjson.parse_json(fastq_order_to_submit)
#
#     # THEN it should determine the project type
#     assert data["project_type"] == "fastq"
#     assert data["customer"] == "cust000"
#
#     # ... and find all samples
#     assert len(data["items"]) == 38
#
#     # ... and collect relevant sample info
#     normal_sample = data["items"][1]
#
#     assert normal_sample["name"] == "s2"
#     assert normal_sample["container"] == "Tube"
#     assert normal_sample["data_analysis"] == "fastq"
#     assert normal_sample["application"] == "WGSLIFC030"
#     assert normal_sample["sex"] == "female"
#     assert normal_sample["require_qcok"] is False
#     assert normal_sample["source"] == "blood"
#     assert normal_sample["priority"] == "research"
#     assert normal_sample["container_name"] == "s2"
#     assert normal_sample["well_position"] == ""
#     assert normal_sample["tumour"] is False
#
#     tumour_sample = data["items"][0]
#     assert tumour_sample["tumour"] is True
#     assert tumour_sample["source"] == "other"
#     assert tumour_sample["quantity"] == "1"
#     assert tumour_sample["comment"] == "other Elution buffer"


# TODO:
# def test_parsing_external_json(external_order_to_submit):
#
#     # GIVEN an limsjson for two external samples, one WES, one WGS
#     # WHEN parsing the file
#     data = limsjson.parse_json(external_order_to_submit)
#
#     # THEN it should detect the project type
#     assert data["project_type"] == "external"
#     assert data["customer"] == "cust002"
#
#     # ... and find all families (1) and samples (2)
#     assert len(data["items"]) == 4
#     family = data["items"][0]
#     assert family["name"] == "fam2"
#     assert family["priority"] == "standard"
#     assert set(family["panels"]) == set(["CILM", "CTD"])
#     # todo: assert set(family['additional_gene_list']) == set(['16PDEL'])
#
#     # ... and collect info about the samples
#     wes_sample = family["samples"][0]
#     wgs_sample = family["samples"][1]
#
#     assert wes_sample["capture_kit"] == "Agilent Sureselect V5"
#     assert wes_sample["application"] == "EXXCUSR000"
#     assert wes_sample["sex"] == "male"
#     # family name on family
#     # priority on family
#     # customer on order (data)
#     assert wes_sample["source"] == "blood"
#
#     # panels on family
#     # additional gene list on family
#     assert wes_sample["status"] == "affected"
#
#     assert wes_sample["mother"] == "mother"
#     assert wes_sample["father"] == "father"
#     # todo: assert wes_sample['other'] == 'other', check if removed in latest OF
#
#     # todo: assert wes_sample['tumour'] == 'Tumor'
#     # todo: assert wes_sample['gel_picture'] == 'Y'
#     # todo: assert wes_sample['extraction_method'] == 'extraction method'
#     assert wes_sample["comment"] == "sample comment"
#
#     assert wgs_sample.get("capture_kit") == "Agilent Sureselect CRE"


# TODO:
# def test_parsing_metagenome_json(metagenome_order_to_submit):
#
#     # GIVEN an limsjson for one metagenome sample
#     # WHEN parsing the file
#     data = limsjson.parse_json(metagenome_order_to_submit)
#
#     # THEN it should detect the project type
#     assert data["project_type"] == "metagenome"
#     # ... and find all samples
#     assert len(data["items"]) == 19
#     # ... and collect relevant sample info
#     sample = data["items"][0]
#
#     assert sample["name"] == "s1"
#     assert sample["source"] == "other"
#     assert sample["data_analysis"] == "fastq"
#     assert sample["application"] == "METPCFR030"
#     assert sample["customer"] == "cust000"
#     assert sample["require_qcok"] is True
#     assert sample["elution_buffer"] == 'Other (specify in "Comments")'
#     assert sample["extraction_method"] == "other (specify in comment field)"
#     assert sample["container"] == "96 well plate"
#     assert sample["priority"] == "research"
#
#     # Required if Plate
#     assert sample["container_name"] == "plate1"
#     assert sample["well_position"] == "A:1"
#
#     # These fields are not required
#     assert sample["concentration_sample"] == "1"
#     assert sample["quantity"] == "2"
#     assert sample["comment"] == "comment"


# TODO:
# def test_parsing_microbial_json(microbial_order_to_submit):
#     # GIVEN a path to a microbial limsjson with 3 samples
#
#     # WHEN parsing the file
#     data = limsjson.parse_json(microbial_order_to_submit)
#
#     # THEN it should determine the type of project and customer
#     assert data["project_type"] == "microbial"
#     assert data["customer"] == "cust000"
#
#     # ... and find all samples
#     assert len(data["items"]) == 14
#
#     # ... and collect relevant sample data
#     sample_data = data["items"][0]
#
#     assert sample_data["name"] == "s1"
#     assert sample_data.get("internal_id") is None
#     assert sample_data["organism"] == "other"
#     assert sample_data["reference_genome"] == "NC_00001"
#     assert sample_data["data_analysis"] == "fastq"
#     assert sample_data["application"] == "MWRNXTR003"
#     # customer on order (data)
#     assert sample_data["require_qcok"] is True
#     assert sample_data["elution_buffer"] == 'Other (specify in "Comments")'
#     assert sample_data["extraction_method"] == "other (specify in comment field)"
#     assert sample_data["container"] == "96 well plate"
#     assert sample_data.get("priority") in "research"
#
#     assert sample_data["container_name"] == "plate1"
#     assert sample_data["well_position"] == "A:1"
#
#     assert sample_data["organism_other"] == "other species"
#
#     assert sample_data["concentration_sample"] == "1"
#     assert sample_data["quantity"] == "2"
#     assert sample_data["comment"] == "comment"


# TODO:
# def test_parsing_balsamic_json(balsamic_order_to_submit):
#
#     # GIVEN an order form for a cancer order with 11 samples,
#     # WHEN parsing the order form
#     data = limsjson.parse_json(balsamic_order_to_submit)
#
#     # THEN it should detect the type of project
#     assert data["project_type"] == "balsamic"
#
#     # ... and it should find and group all samples in case
#     assert len(data["items"]) == 36
#
#     # ... and collect relevant data about the case
#     # ... and collect relevant info about the samples
#
#     case = data["items"][0]
#     sample = case["samples"][0]
#     assert len(case["samples"]) == 3
#
#     # This information is required
#
#     assert sample["name"] == "s1"
#     assert sample["container"] == "96 well plate"
#     assert sample["data_analysis"] == "Balsamic "
#     assert sample["application"] == "WGSPCFC030"
#     assert sample["sex"] == "male"
#     assert case["name"] == "family"
#     assert data["customer"] == "cust000"
#     assert case["require_qcok"] is True
#     assert sample["source"] == "other"
#     assert case["priority"] == "research"
#
#     # Required if Plate
#     assert sample["container_name"] == "plate"
#     assert sample["well_position"] == "A:1"
#
#     # This information is required for panel- or exome analysis
#     assert sample["elution_buffer"] == 'Other (specify in "Comments")'
#
#     # This information is required for Balsamic analysis (cancer)
#     assert sample["tumour"] is True
#     assert sample["capture_kit"] == "LymphoMATIC"
#     assert sample["tumour_purity"] == "5.0"
#
#     assert sample["formalin_fixation_time"] == "1.0"
#     assert sample["post_formalin_fixation_time"] == "2.0"
#     assert sample["tissue_block_size"] == "small"
#
#     # This information is optional
#     assert sample["quantity"] == "1"
#     assert sample["comment"] == "other Elution buffer"


# TODO:
# def test_parsing_mip_rna_json(mip_rna_order_to_submit):
#
#     # GIVEN an order form for a mip balsamic order with 3 samples, 1 trio, in a plate
#     # WHEN parsing the order form
#     data = limsjson.parse_json(mip_rna_order_to_submit)
#
#     # THEN it should detect the type of project
#     assert data["project_type"] == "mip_rna"
#     assert data["customer"] == "cust000"
#     # ... and it should find and group all samples in cases
#     assert len(data["items"]) == 36
#     # ... and collect relevant data about the cases
#     first_case = data["items"][0]
#     assert len(first_case["samples"]) == 3
#     assert first_case["name"] == "family"
#     assert first_case["priority"] == "research"
#     assert set(first_case["panels"]) == set(["AD-HSP", "Ataxi", "ATX"])
#     assert first_case["require_qcok"] is True
#     # ... and collect relevant info about the samples
#
#     first_sample = first_case["samples"][0]
#     assert first_sample["name"] == "s1"
#     assert first_sample["container"] == "96 well plate"
#     assert first_sample["data_analysis"] == "MIP RNA"
#     assert first_sample["application"] == "RNAPOAR025"
#     assert first_sample["sex"] == "male"
#     # case-id on the case
#     # customer on the order (data)
#     # require-qc-ok on the family
#     assert first_sample["source"] == "other"
#
#     assert first_sample["container_name"] == "plate"
#     assert first_sample["well_position"] == "A:1"
#
#     # panels on the family
#     assert first_sample["status"] == "affected"
#
#     assert first_sample["mother"] == "s2"
#     assert first_sample["father"] == "s3"
#
#     assert first_sample["tumour"] is True
#
#     assert first_sample["quantity"] == "1"
#     assert first_sample["comment"] == "other Elution buffer"
#
#     # required for RNA samples
#     assert first_sample["from_sample"] == "s1"
#     assert first_sample["time_point"] == "0"
