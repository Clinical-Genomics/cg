from cg.apps.lims import orderform


def test_parsing_rml_orderform(rml_orderform):
    # GIVEN a path to a RML orderform with 2 sample in a pool
    # WHEN parsing the file
    data = orderform.parse_orderform(rml_orderform)

    # THEN it should determine the type of project and customer
    assert data["project_type"] == "rml"
    assert data["customer"] == "cust000"
    # ... and find all samples
    assert len(data["items"]) == 21

    # ... and collect relevant sample data
    sample_data = data["items"][0]
    assert sample_data["name"] == "sample1"
    assert sample_data["pool"] == "pool1"
    assert sample_data["application"] == "RMLP10R150"
    assert sample_data["data_analysis"] == "fastq"
    assert sample_data["volume"] == "1"
    assert sample_data["concentration"] == "2"
    assert sample_data["index"] == "TruSeq Custom Amplicon Dual-index (A7-A5)"
    assert sample_data["index_number"] == "1"

    assert sample_data["container_name"] is None
    assert sample_data["rml_plate_name"] == "plate"
    assert sample_data["well_position"] is None
    assert sample_data["well_position_rml"] == "A:1"

    assert sample_data["reagent_label"] == "A701-A501 (ATCACGAC-TGAACCTT)"

    assert sample_data["custom_index"] == "GATACA"

    assert sample_data["comment"] == "test comment"
    assert sample_data["capture_kit"] == "Agilent Sureselect CRE"


def test_parsing_fastq_orderform(fastq_orderform):

    # GIVEN a FASTQ orderform with 2 samples, one normal, one tumour
    # WHEN parsing the file
    data = orderform.parse_orderform(fastq_orderform)

    # THEN it should determine the project type
    assert data["project_type"] == "fastq"
    # ... and find all samples
    assert len(data["items"]) == 38

    # ... and collect relevant sample info
    normal_sample = data["items"][1]
    tumour_sample = data["items"][0]
    assert normal_sample["name"] == "s2"
    assert normal_sample["container"] == "Tube"
    assert normal_sample["data_analysis"] == "fastq"
    assert normal_sample["application"] == "WGSLIFC030"
    assert normal_sample["sex"] == "female"
    assert normal_sample["case"] == "family"
    assert data["customer"] == "cust000"
    assert normal_sample["require_qcok"] is False
    assert normal_sample["source"] == "blood"
    assert normal_sample["priority"] == "research"

    assert normal_sample["container_name"] == ""
    assert normal_sample["well_position"] == ""

    assert normal_sample["tumour"] is False

    assert tumour_sample["tumour"] is True
    assert tumour_sample["source"] == "other"

    assert tumour_sample["quantity"] == "1"
    assert tumour_sample["comment"] == "other Elution buffer"


def test_parsing_mip_orderform(mip_orderform):

    # GIVEN an order form for a Scout order with 4 samples, 1 trio, in a plate
    # WHEN parsing the order form
    data = orderform.parse_orderform(mip_orderform)

    # THEN it should detect the type of project
    assert data["project_type"] == "mip"
    assert data["customer"] == "cust000"
    # ... and it should find and group all samples in families
    assert len(data["items"]) == 36
    # ... and collect relevant data about the families
    trio_family = data["items"][0]
    assert len(trio_family["samples"]) == 3
    assert trio_family["name"] == "family"
    assert trio_family["priority"] == "research"
    assert set(trio_family["panels"]) == set(["AD-HSP", "Ataxi", "ATX"])
    assert trio_family["require_qcok"] is True
    # ... and collect relevant info about the samples

    proband_sample = trio_family["samples"][0]
    assert proband_sample["name"] == "s1"
    assert proband_sample["container"] == "96 well plate"
    assert proband_sample["data_analysis"] == "MIP"
    assert proband_sample["application"] == "WGSPCFC030"
    assert proband_sample["sex"] == "male"
    # family-id on the family
    # customer on the order (data)
    # require-qc-ok on the family
    assert proband_sample["source"] == "other"
    assert proband_sample["tumour"] is True

    assert proband_sample["container_name"] == "plate"
    assert proband_sample["well_position"] == "A:1"

    # panels on the family
    assert proband_sample["status"] == "affected"

    assert proband_sample["mother"] == "s2"
    assert proband_sample["father"] == "s3"

    assert proband_sample["quantity"] == "1"
    assert proband_sample["comment"] == "other Elution buffer"


def test_parsing_external_orderform(external_orderform):

    # GIVEN an orderform for two external samples, one WES, one WGS
    # WHEN parsing the file
    data = orderform.parse_orderform(external_orderform)

    # THEN it should detect the project type
    assert data["project_type"] == "external"
    assert data["customer"] == "cust002"

    # ... and find all families (1) and samples (2)
    assert len(data["items"]) == 4
    family = data["items"][0]
    assert family["name"] == "fam2"
    assert family["priority"] == "standard"
    assert set(family["panels"]) == set(["CILM", "CTD"])
    # todo: assert set(family['additional_gene_list']) == set(['16PDEL'])

    # ... and collect info about the samples
    wes_sample = family["samples"][0]
    wgs_sample = family["samples"][1]

    assert wes_sample["capture_kit"] == "Agilent Sureselect V5"
    assert wes_sample["application"] == "EXXCUSR000"
    assert wes_sample["sex"] == "male"
    # family name on family
    # priority on family
    # customer on order (data)
    assert wes_sample["source"] == "blood"

    # panels on family
    # additional gene list on family
    assert wes_sample["status"] == "affected"

    assert wes_sample["mother"] == "mother"
    assert wes_sample["father"] == "father"
    # todo: assert wes_sample['other'] == 'other', check if removed in latest OF

    # todo: assert wes_sample['tumour'] == 'Tumor'
    # todo: assert wes_sample['gel_picture'] == 'Y'
    # todo: assert wes_sample['extraction_method'] == 'extraction method'
    assert wes_sample["comment"] == "sample comment"

    assert wgs_sample.get("capture_kit") == "Agilent Sureselect CRE"


def test_parsing_metagenome_orderform(metagenome_orderform):

    # GIVEN an orderform for one metagenome sample
    # WHEN parsing the file
    data = orderform.parse_orderform(metagenome_orderform)

    # THEN it should detect the project type
    assert data["project_type"] == "metagenome"
    # ... and find all samples
    assert len(data["items"]) == 19
    # ... and collect relevant sample info
    sample = data["items"][0]

    assert sample["name"] == "s1"
    assert sample["source"] == "other"
    assert sample["data_analysis"] == "fastq"
    assert sample["application"] == "METPCFR030"
    assert sample["customer"] == "cust000"
    assert sample["require_qcok"] is True
    assert sample["elution_buffer"] == 'Other (specify in "Comments")'
    assert sample["extraction_method"] == "other (specify in comment field)"
    assert sample["container"] == "96 well plate"
    assert sample["priority"] == "research"

    # Required if Plate
    assert sample["container_name"] == "plate1"
    assert sample["well_position"] == "A:1"

    # These fields are not required
    assert sample["concentration_weight"] == "1"
    assert sample["quantity"] == "2"
    assert sample["comment"] == "comment"


def test_parsing_microbial_orderform(microbial_orderform):
    # GIVEN a path to a microbial orderform with 3 samples

    # WHEN parsing the file
    data = orderform.parse_orderform(microbial_orderform)

    # THEN it should determine the type of project and customer
    assert data["project_type"] == "microbial"
    assert data["customer"] == "cust000"

    # ... and find all samples
    assert len(data["items"]) == 14

    # ... and collect relevant sample data
    sample_data = data["items"][0]

    assert sample_data["name"] == "s1"
    assert sample_data.get("internal_id") is None
    assert sample_data["organism"] == "other"
    assert sample_data["reference_genome"] == "NC_00001"
    assert sample_data["data_analysis"] == "fastq"
    assert sample_data["application"] == "MWRNXTR003"
    # customer on order (data)
    assert sample_data["require_qcok"] is True
    assert sample_data["elution_buffer"] == 'Other (specify in "Comments")'
    assert sample_data["extraction_method"] == "other (specify in comment field)"
    assert sample_data["container"] == "96 well plate"
    assert sample_data.get("priority") in "research"

    assert sample_data["container_name"] == "plate1"
    assert sample_data["well_position"] == "A:1"

    assert sample_data["organism_other"] == "other species"

    assert sample_data["concentration_weight"] == "1"
    assert sample_data["quantity"] == "2"
    assert sample_data["comment"] == "comment"


def test_parsing_balsamic_orderform(balsamic_orderform):

    # GIVEN an order form for a cancer order with 11 samples,
    # WHEN parsing the order form
    data = orderform.parse_orderform(balsamic_orderform)

    # THEN it should detect the type of project
    assert data["project_type"] == "balsamic"

    # ... and it should find and group all samples in case
    assert len(data["items"]) == 36

    # ... and collect relevant data about the case
    # ... and collect relevant info about the samples

    case = data["items"][0]
    sample = case["samples"][0]
    assert len(case["samples"]) == 3

    # This information is required

    assert sample["name"] == "s1"
    assert sample["container"] == "96 well plate"
    assert sample["data_analysis"] == "Balsamic "
    assert sample["application"] == "WGSPCFC030"
    assert sample["sex"] == "male"
    assert case["name"] == "family"
    assert data["customer"] == "cust000"
    assert case["require_qcok"] is True
    assert sample["source"] == "other"
    assert case["priority"] == "research"

    # Required if Plate
    assert sample["container_name"] == "plate"
    assert sample["well_position"] == "A:1"

    # This information is required for panel- or exome analysis
    assert sample["elution_buffer"] == 'Other (specify in "Comments")'

    # This information is required for Balsamic analysis (cancer)
    assert sample["tumour"] is True
    assert sample["capture_kit"] == "LymphoMATIC"
    assert sample["tumour_purity"] == "5.0"

    assert sample["formalin_fixation_time"] == "1.0"
    assert sample["post_formalin_fixation_time"] == "2.0"
    assert sample["tissue_block_size"] == "small"

    # This information is optional
    assert sample["quantity"] == "1"
    assert sample["comment"] == "other Elution buffer"


def test_parsing_mip_rna_orderform(mip_rna_orderform):

    # GIVEN an order form for a mip balsamic order with 3 samples, 1 trio, in a plate
    # WHEN parsing the order form
    data = orderform.parse_orderform(mip_rna_orderform)

    # THEN it should detect the type of project
    assert data["project_type"] == "mip_rna"
    assert data["customer"] == "cust000"
    # ... and it should find and group all samples in cases
    assert len(data["items"]) == 36
    # ... and collect relevant data about the cases
    first_case = data["items"][0]
    assert len(first_case["samples"]) == 3
    assert first_case["name"] == "family"
    assert first_case["priority"] == "research"
    assert set(first_case["panels"]) == set(["AD-HSP", "Ataxi", "ATX"])
    assert first_case["require_qcok"] is True
    # ... and collect relevant info about the samples

    first_sample = first_case["samples"][0]
    assert first_sample["name"] == "s1"
    assert first_sample["container"] == "96 well plate"
    assert first_sample["data_analysis"] == "MIP RNA"
    assert first_sample["application"] == "RNAPOAR025"
    assert first_sample["sex"] == "male"
    # case-id on the case
    # customer on the order (data)
    # require-qc-ok on the family
    assert first_sample["source"] == "other"

    assert first_sample["container_name"] == "plate"
    assert first_sample["well_position"] == "A:1"

    # panels on the family
    assert first_sample["status"] == "affected"

    assert first_sample["mother"] == "s2"
    assert first_sample["father"] == "s3"

    assert first_sample["tumour"] is True

    assert first_sample["quantity"] == "1"
    assert first_sample["comment"] == "other Elution buffer"

    # required for RNA samples
    assert first_sample["from_sample"] == "s1"
    assert first_sample["time_point"] == "0"


def test_parse_mip_rna(skeleton_orderform_sample: dict):

    # GIVEN a raw sample with mip only value from orderform 1508 for data_analysis
    raw_sample = skeleton_orderform_sample
    raw_sample["UDF/Data Analysis"] = "MIP RNA"

    # WHEN parsing the sample
    parsed_sample = orderform.parse_sample(raw_sample)

    # THEN data_analysis is mip only
    assert parsed_sample["analysis"] == "mip_rna"


def test_parse_mip_only(skeleton_orderform_sample: dict):

    # GIVEN a raw sample with mip only value from orderform 1508 for data_analysis
    raw_sample = skeleton_orderform_sample
    raw_sample["UDF/Data Analysis"] = "MIP"

    # WHEN parsing the sample
    parsed_sample = orderform.parse_sample(raw_sample)

    # THEN data_analysis is mip only
    assert parsed_sample["analysis"] == "mip"


def test_parse_balsamic_only(skeleton_orderform_sample: dict):

    # GIVEN a raw sample with balsamic only value from orderform 1508 for data_analysis
    raw_sample = skeleton_orderform_sample
    raw_sample["UDF/Data Analysis"] = "Balsamic "

    # WHEN parsing the sample
    parsed_sample = orderform.parse_sample(raw_sample)

    # THEN data_analysis is balsamic only
    assert parsed_sample["analysis"] == "balsamic"
