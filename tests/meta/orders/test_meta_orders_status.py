import datetime as dt

import pytest

from cg.constants import DataDelivery, Pipeline
from cg.exc import OrderError
from cg.meta.orders.status import StatusHandler
from cg.store import models


def test_pools_to_status(rml_order_to_submit):
    # GIVEN a rml order with three samples in one pool
    # WHEN parsing for status
    data = StatusHandler.pools_to_status(rml_order_to_submit)
    # THEN it should pick out the general information
    assert data["customer"] == "cust000"
    assert data["order"] == "ctDNA sequencing - order 9"
    assert data["comment"] == "order comment"

    # ... and information about the pool(s)
    assert len(data["pools"]) == 2
    pool = data["pools"][0]
    assert pool["name"] == "pool-1"
    assert pool["application"] == "RMLS05R150"
    assert pool["data_analysis"] == str(Pipeline.FLUFFY)
    assert pool["data_delivery"] == str(DataDelivery.NIPT_VIEWER)
    assert len(pool["samples"]) == 2
    sample = pool["samples"][0]
    assert sample["name"] == "sample1"
    assert sample["comment"] == "test comment"
    assert pool["priority"] == "research"
    assert sample["control"] == "negative"


def test_samples_to_status(fastq_order_to_submit):
    # GIVEN fastq order with two samples
    # WHEN parsing for status
    data = StatusHandler.samples_to_status(fastq_order_to_submit)
    # THEN it should pick out samples and relevant information
    assert len(data["samples"]) == 2
    first_sample = data["samples"][0]
    assert first_sample["name"] == "prov1"
    assert first_sample["application"] == "WGSPCFC060"
    assert first_sample["priority"] == "priority"
    assert first_sample["tumour"] is False
    assert first_sample["volume"] == "1"

    # ... and the other sample is a tumour
    assert data["samples"][1]["tumour"] is True


def test_metagenome_to_status(metagenome_order_to_submit):

    # GIVEN metagenome order with two samples
    # WHEN parsing for status
    data = StatusHandler.samples_to_status(metagenome_order_to_submit)
    # THEN it should pick out samples and relevant information
    assert len(data["samples"]) == 2
    first_sample = data["samples"][0]
    assert first_sample["name"] == "Bristol"
    assert first_sample["application"] == "METLIFR020"
    assert first_sample["priority"] == "standard"
    assert first_sample["volume"] == "1"


def test_microbial_samples_to_status(microbial_order_to_submit):
    # GIVEN microbial order with three samples

    # WHEN parsing for status
    data = StatusHandler.microbial_samples_to_status(microbial_order_to_submit)

    # THEN it should pick out samples and relevant information
    assert len(data["samples"]) == 5
    assert data["customer"] == "cust002"
    assert data["order"] == "Microbial samples"
    assert data["comment"] == "Order comment"
    assert data["data_analysis"] == str(Pipeline.MICROSALT)
    assert data["data_delivery"] == str(DataDelivery.FASTQ)

    # THEN first sample should contain all the relevant data from the microbial order
    sample_data = data["samples"][0]
    assert sample_data["priority"] == "research"
    assert sample_data["name"] == "all-fields"
    assert sample_data.get("internal_id") is None
    assert sample_data["organism_id"] == "M.upium"
    assert sample_data["reference_genome"] == "NC_111"
    assert sample_data["application"] == "MWRNXTR003"
    assert sample_data["comment"] == "plate comment"
    assert sample_data["volume"] == "1"


def test_sarscov2_samples_to_status(sarscov2_order_to_submit):
    # GIVEN sarscov2 order with three samples

    # WHEN parsing for status
    data = StatusHandler.microbial_samples_to_status(sarscov2_order_to_submit)

    # THEN it should pick out samples and relevant information
    assert len(data["samples"]) == 5
    assert data["customer"] == "cust002"
    assert data["order"] == "Sars-CoV-2 samples"
    assert data["comment"] == "Order comment"
    assert data["data_analysis"] == str(Pipeline.MICROSALT)
    assert data["data_delivery"] == str(DataDelivery.FASTQ)

    # THEN first sample should contain all the relevant data from the microbial order
    sample_data = data["samples"][0]
    assert sample_data.get("internal_id") is None
    assert sample_data["priority"] == "research"
    assert sample_data["application"] == "VWGDPTR001"
    assert sample_data["collection_date"] == "2021-05-05"
    assert sample_data["comment"] == "plate comment"
    assert sample_data["lab_code"] == "SE110 Växjö"
    assert sample_data["name"] == "all-fields"
    assert sample_data["organism_id"] == "SARS CoV-2"
    assert sample_data["original_lab"] == "Karolinska University Hospital Solna"
    assert sample_data["original_lab_address"] == "171 76 Stockholm"
    assert sample_data["pre_processing_method"] == "COVIDSeq"
    assert sample_data["reference_genome"] == "NC_111"
    assert sample_data["region"] == "Stockholm"
    assert sample_data["region_code"] == "01"
    assert sample_data["selection_criteria"] == "1. Allmän övervakning"
    assert sample_data["volume"] == "1"


def test_cases_to_status(mip_order_to_submit):

    # GIVEN a scout order with a trio case

    # WHEN parsing for status
    data = StatusHandler.cases_to_status(mip_order_to_submit)

    # THEN it should pick out the case
    assert len(data["families"]) == 2
    family = data["families"][0]
    assert family["name"] == "family1"
    assert family["data_analysis"] == str(Pipeline.MIP_DNA)
    assert family["data_delivery"] == str(DataDelivery.SCOUT)
    assert family["priority"] == "standard"
    assert family["cohorts"] == {"Other"}
    assert family["synopsis"] == "Här kommer det att komma en väldigt lång text med för synopsis."
    assert set(family["panels"]) == {"IEM"}
    assert len(family["samples"]) == 3

    first_sample = family["samples"][0]
    assert first_sample["age_at_sampling"] == "17.18192"
    assert first_sample["name"] == "sample1"
    assert first_sample["application"] == "WGTPCFC030"
    assert first_sample["phenotype_groups"] == ["Phenotype-group"]
    assert first_sample["phenotype_terms"] == ["HP:0012747", "HP:0025049"]
    assert first_sample["sex"] == "female"
    assert first_sample["status"] == "affected"
    assert first_sample["subject_id"] == "sample1"
    assert first_sample["mother"] == "sample2"
    assert first_sample["father"] == "sample3"

    # ... second sample has a comment
    assert isinstance(family["samples"][1]["comment"], str)


def test_cases_to_status_synopsis(mip_order_to_submit):
    # GIVEN a scout order with a trio case where synopsis is None
    for sample in mip_order_to_submit["samples"]:
        sample["synopsis"] = None

    # WHEN parsing for status
    StatusHandler.cases_to_status(mip_order_to_submit)

    # THEN No exception should have been raised on synopsis


def test_store_rml(orders_api, base_store, rml_status_data):
    # GIVEN a basic store with no samples and a rml order
    assert base_store.pools().count() == 0
    assert base_store.families().count() == 0
    assert base_store.samples().count() == 0

    # WHEN storing the order
    new_pools = orders_api.store_rml(
        customer=rml_status_data["customer"],
        order=rml_status_data["order"],
        ordered=dt.datetime.now(),
        ticket=1234348,
        pools=rml_status_data["pools"],
    )

    # THEN it should update the database with new pools
    assert len(new_pools) == 2

    assert base_store.pools().count() == base_store.families().count()
    assert base_store.samples().count() == 4

    assert base_store.samples().filter_by(control="negative").count() == 1

    new_pool = base_store.pools().first()
    assert new_pool == new_pools[1]

    assert new_pool.name == "pool-2"
    assert new_pool.application_version.application.tag == "RMLS05R150"
    assert not hasattr(new_pool, "data_analysis")

    # ... and add a delivery
    assert len(new_pool.deliveries) == 1
    assert new_pool.deliveries[0].destination == "caesar"

    new_case = base_store.families().first()
    assert new_case.data_analysis == str(Pipeline.FLUFFY)
    assert new_case.data_delivery == str(DataDelivery.NIPT_VIEWER)

    # and that the pool is set for invoicing but not the samples of the pool
    assert not new_pool.no_invoice
    for link in new_case.links:
        assert link.sample.no_invoice


def test_store_rml_bad_apptag(orders_api, base_store, rml_status_data):
    # GIVEN a basic store with no samples and a rml order
    assert base_store.pools().count() == 0

    for pool in rml_status_data["pools"]:
        pool["application"] = "nonexistingtag"

    # THEN it should raise OrderError
    with pytest.raises(OrderError):
        # WHEN storing the order
        orders_api.store_rml(
            customer=rml_status_data["customer"],
            order=rml_status_data["order"],
            ordered=dt.datetime.now(),
            ticket=1234348,
            pools=rml_status_data["pools"],
        )


def test_store_samples(orders_api, base_store, fastq_status_data):
    # GIVEN a basic store with no samples and a fastq order
    assert base_store.samples().count() == 0
    assert base_store.families().count() == 0

    # WHEN storing the order
    new_samples = orders_api.store_fastq_samples(
        customer=fastq_status_data["customer"],
        order=fastq_status_data["order"],
        ordered=dt.datetime.now(),
        ticket=1234348,
        samples=fastq_status_data["samples"],
    )

    # THEN it should store the samples and create a case for each sample
    assert len(new_samples) == 2
    assert base_store.samples().count() == 2
    assert base_store.families().count() == 2
    first_sample = new_samples[0]
    assert len(first_sample.links) == 1
    family_link = first_sample.links[0]
    assert family_link.family in base_store.families()
    for sample in new_samples:
        assert len(sample.deliveries) == 1
    assert family_link.family.data_analysis
    assert family_link.family.data_delivery == DataDelivery.FASTQ


def test_store_samples_sex_stored(orders_api, base_store, fastq_status_data):
    # GIVEN a basic store with no samples and a fastq order
    assert base_store.samples().count() == 0
    assert base_store.families().count() == 0

    # WHEN storing the order
    new_samples = orders_api.store_fastq_samples(
        customer=fastq_status_data["customer"],
        order=fastq_status_data["order"],
        ordered=dt.datetime.now(),
        ticket=1234348,
        samples=fastq_status_data["samples"],
    )

    # THEN the sample sex should be stored
    assert new_samples[0].sex == "male"


def test_store_fastq_samples_non_tumour_wgs_to_mip(orders_api, base_store, fastq_status_data):
    # GIVEN a basic store with no samples and a non-tumour fastq order as wgs
    assert base_store.samples().count() == 0
    assert base_store.families().count() == 0
    base_store.application(fastq_status_data["samples"][0]["application"]).prep_category = "wgs"
    fastq_status_data["samples"][0]["tumour"] = False

    # WHEN storing the order
    new_samples = orders_api.store_fastq_samples(
        customer=fastq_status_data["customer"],
        order=fastq_status_data["order"],
        ordered=dt.datetime.now(),
        ticket=1234348,
        samples=fastq_status_data["samples"],
    )

    # THEN the analysis for the case should be MAF
    assert new_samples[0].links[0].family.data_analysis == Pipeline.MIP_DNA


def test_store_fastq_samples_tumour_wgs_to_fastq(orders_api, base_store, fastq_status_data):
    # GIVEN a basic store with no samples and a tumour fastq order as wgs
    assert base_store.samples().count() == 0
    assert base_store.families().count() == 0
    base_store.application(fastq_status_data["samples"][0]["application"]).prep_category = "wgs"
    fastq_status_data["samples"][0]["tumour"] = True

    # WHEN storing the order
    new_samples = orders_api.store_fastq_samples(
        customer=fastq_status_data["customer"],
        order=fastq_status_data["order"],
        ordered=dt.datetime.now(),
        ticket=1234348,
        samples=fastq_status_data["samples"],
    )

    # THEN the analysis for the case should be FASTQ
    assert new_samples[0].links[0].family.data_analysis == Pipeline.FASTQ


def test_store_fastq_samples_non_wgs_as_fastq(orders_api, base_store, fastq_status_data):
    # GIVEN a basic store with no samples and a fastq order as non wgs
    assert base_store.samples().count() == 0
    assert base_store.families().count() == 0
    non_wgs_prep_category = "wes"
    assert base_store.applications(category=non_wgs_prep_category)
    for sample in fastq_status_data["samples"]:
        sample["application"] = base_store.applications(category=non_wgs_prep_category)[0].tag

    # WHEN storing the order
    new_samples = orders_api.store_fastq_samples(
        customer=fastq_status_data["customer"],
        order=fastq_status_data["order"],
        ordered=dt.datetime.now(),
        ticket=1234348,
        samples=fastq_status_data["samples"],
    )

    # THEN the analysis for the case should be fastq (none)
    assert new_samples[0].links[0].family.data_analysis == Pipeline.FASTQ


def test_store_samples_bad_apptag(orders_api, base_store, fastq_status_data):
    # GIVEN a basic store with no samples and a fastq order
    assert base_store.samples().count() == 0
    assert base_store.families().count() == 0

    for sample in fastq_status_data["samples"]:
        sample["application"] = "nonexistingtag"

    # THEN it should raise OrderError
    with pytest.raises(OrderError):
        # WHEN storing the order
        orders_api.store_fastq_samples(
            customer=fastq_status_data["customer"],
            order=fastq_status_data["order"],
            ordered=dt.datetime.now(),
            ticket=1234348,
            samples=fastq_status_data["samples"],
        )


def test_store_microbial_samples(orders_api, base_store, microbial_status_data):
    # GIVEN a basic store with no samples and a microbial order and one Organism
    assert base_store.samples().count() == 0
    assert base_store.families().count() == 0
    assert base_store.organisms().count() == 1

    # WHEN storing the order
    new_samples = orders_api.store_microbial_samples(
        customer=microbial_status_data["customer"],
        order=microbial_status_data["order"],
        ordered=dt.datetime.now(),
        ticket=1234348,
        samples=microbial_status_data["samples"],
        comment="",
        data_analysis=Pipeline.MICROSALT,
        data_delivery=DataDelivery.FASTQ_QC,
    )

    # THEN it should store the samples under a case (case) and the used previously unknown
    # organisms
    assert new_samples
    assert base_store.families().count() == 1
    assert len(new_samples) == 5
    assert base_store.samples().count() == 5
    assert base_store.organisms().count() == 3


def test_store_microbial_case_data_analysis_stored(orders_api, base_store, microbial_status_data):
    # GIVEN a basic store with no samples and a microbial order and one Organism
    assert base_store.samples().count() == 0
    assert base_store.families().count() == 0

    # WHEN storing the order
    new_samples = orders_api.store_microbial_samples(
        customer=microbial_status_data["customer"],
        order=microbial_status_data["order"],
        ordered=dt.datetime.now(),
        ticket=1234348,
        samples=microbial_status_data["samples"],
        comment="",
        data_analysis=Pipeline.MICROSALT,
        data_delivery=DataDelivery.FASTQ_QC,
    )

    # THEN store the samples under a case with the microbial data_analysis type on case level
    assert base_store.samples().count() > 0
    assert base_store.families().count() == 1

    microbial_case = base_store.families().first()
    assert microbial_case.data_analysis == str(Pipeline.MICROSALT)
    assert microbial_case.data_delivery == str(DataDelivery.FASTQ_QC)


def test_store_microbial_samples_bad_apptag(orders_api, microbial_status_data):
    # GIVEN a basic store missing the application on the samples

    for sample in microbial_status_data["samples"]:
        sample["application"] = "nonexistingtag"

    # THEN it should raise OrderError
    with pytest.raises(OrderError):
        # WHEN storing the order
        orders_api.store_microbial_samples(
            customer=microbial_status_data["customer"],
            order=microbial_status_data["order"],
            ordered=dt.datetime.now(),
            ticket=1234348,
            samples=microbial_status_data["samples"],
            comment="",
            data_analysis=Pipeline.MICROSALT,
            data_delivery=DataDelivery.FASTQ_QC,
        )


def test_store_microbial_sample_priority(orders_api, base_store, microbial_status_data):
    # GIVEN a basic store with no samples
    assert base_store.samples().count() == 0

    # WHEN storing the order
    orders_api.store_microbial_samples(
        customer=microbial_status_data["customer"],
        order=microbial_status_data["order"],
        ordered=dt.datetime.now(),
        ticket=1234348,
        samples=microbial_status_data["samples"],
        comment="",
        data_analysis=Pipeline.MICROSALT,
        data_delivery=DataDelivery.FASTQ_QC,
    )

    # THEN it should store the sample priority
    assert base_store.samples().count() > 0
    microbial_sample = base_store.samples().first()

    assert microbial_sample.priority_human == "research"


def test_store_mip(orders_api, base_store, mip_status_data):
    # GIVEN a basic store with no samples or nothing in it + scout order
    assert base_store.samples().first() is None
    assert base_store.families().first() is None

    # WHEN storing the order
    new_families = orders_api.store_cases(
        customer=mip_status_data["customer"],
        order=mip_status_data["order"],
        ordered=dt.datetime.now(),
        ticket=123456,
        cases=mip_status_data["families"],
    )

    # THEN it should create and link samples and the case
    assert len(new_families) == 2
    new_case = new_families[0]
    assert new_case.name == "family1"
    assert set(new_case.panels) == {"IEM"}
    assert new_case.priority_human == "standard"

    assert len(new_case.links) == 3
    new_link = new_case.links[0]
    assert new_case.data_analysis == str(Pipeline.MIP_DNA)
    assert new_case.data_delivery == str(DataDelivery.SCOUT)
    assert set(new_case.cohorts) == {"Other"}
    assert (
        new_case.synopsis
        == "H\u00e4r kommer det att komma en v\u00e4ldigt l\u00e5ng text med f\u00f6r synopsis."
    )
    assert new_link.status == "affected"
    assert new_link.mother.name == "sample2"
    assert new_link.father.name == "sample3"
    assert new_link.sample.name == "sample1"
    assert new_link.sample.sex == "female"
    assert new_link.sample.application_version.application.tag == "WGTPCFC030"
    assert new_link.sample.is_tumour
    assert isinstance(new_case.links[1].sample.comment, str)

    assert set(new_link.sample.phenotype_groups) == {"Phenotype-group"}
    assert set(new_link.sample.phenotype_terms) == {"HP:0012747", "HP:0025049"}
    assert new_link.sample.subject_id == "sample1"

    assert new_link.sample.age_at_sampling == 17.18192

    assert base_store.deliveries().count() == base_store.samples().count()
    for link in new_case.links:
        assert len(link.sample.deliveries) == 1


def test_store_mip_rna(orders_api, base_store, mip_rna_status_data):
    # GIVEN a basic store with no samples or nothing in it + rna order
    rna_application = "RNAPOAR025"
    assert base_store.samples().first() is None
    assert base_store.families().first() is None
    assert base_store.application(rna_application)

    # WHEN storing the order
    new_cases = orders_api.store_cases(
        customer=mip_rna_status_data["customer"],
        order=mip_rna_status_data["order"],
        ordered=dt.datetime.now(),
        ticket=123456,
        cases=mip_rna_status_data["families"],
    )

    # THEN it should create and link samples and the casing
    assert len(new_cases) == 1
    new_casing = new_cases[0]

    assert len(new_casing.links) == 2
    new_link = new_casing.links[0]
    assert new_casing.data_analysis == str(Pipeline.MIP_RNA)
    assert new_casing.data_delivery == str(DataDelivery.SCOUT)
    assert new_link.sample.name == "sample1-rna-t1"
    assert new_link.sample.application_version.application.tag == rna_application
    assert new_link.sample.time_point == 1


def test_store_families_bad_apptag(orders_api, base_store, mip_status_data):
    # GIVEN a basic store with no samples or nothing in it + scout order
    assert base_store.samples().first() is None
    assert base_store.families().first() is None

    for family in mip_status_data["families"]:
        for sample in family["samples"]:
            sample["application"] = "nonexistingtag"

    # THEN it should raise OrderError
    with pytest.raises(OrderError):
        # WHEN storing the order
        orders_api.store_cases(
            customer=mip_status_data["customer"],
            order=mip_status_data["order"],
            ordered=dt.datetime.now(),
            ticket=123456,
            cases=mip_status_data["families"],
        )


def test_store_metagenome_samples(orders_api, base_store, metagenome_status_data):
    # GIVEN a basic store with no samples and a metagenome order
    assert base_store.samples().count() == 0

    # WHEN storing the order
    new_samples = orders_api.store_samples(
        customer=metagenome_status_data["customer"],
        order=metagenome_status_data["order"],
        ordered=dt.datetime.now(),
        ticket=1234348,
        samples=metagenome_status_data["samples"],
    )

    # THEN it should store the samples
    assert len(new_samples) == 2
    assert base_store.samples().count() == 2


def test_store_metagenome_samples_bad_apptag(orders_api, base_store, metagenome_status_data):
    # GIVEN a basic store with no samples and a metagenome order
    assert base_store.samples().count() == 0

    for sample in metagenome_status_data["samples"]:
        sample["application"] = "nonexistingtag"

    # THEN it should raise OrderError
    with pytest.raises(OrderError):
        # WHEN storing the order
        orders_api.store_samples(
            customer=metagenome_status_data["customer"],
            order=metagenome_status_data["order"],
            ordered=dt.datetime.now(),
            ticket=1234348,
            samples=metagenome_status_data["samples"],
        )


def test_store_cancer_samples(orders_api, base_store, balsamic_status_data):
    # GIVEN a basic store with no samples and a cancer order
    assert base_store.samples().first() is None
    assert base_store.families().first() is None

    # WHEN storing the order
    new_families = orders_api.store_cases(
        customer=balsamic_status_data["customer"],
        order=balsamic_status_data["order"],
        ordered=dt.datetime.now(),
        ticket=123456,
        cases=balsamic_status_data["families"],
    )

    # THEN it should create and link samples and the case
    assert len(new_families) == 1
    new_case = new_families[0]
    assert new_case.name == "family1"
    assert new_case.data_analysis == str(Pipeline.BALSAMIC)
    assert new_case.data_delivery == str(DataDelivery.FASTQ_QC_ANALYSIS_CRAM_SCOUT)
    assert set(new_case.panels) == set()
    assert new_case.priority_human == "standard"

    assert len(new_case.links) == 1
    new_link = new_case.links[0]
    assert new_link.sample.name == "s1"
    assert new_link.sample.sex == "male"
    assert new_link.sample.application_version.application.tag == "WGTPCFC030"
    assert new_link.sample.comment == "other Elution buffer"
    assert new_link.sample.is_tumour

    assert base_store.deliveries().count() == base_store.samples().count()
    for link in new_case.links:
        assert len(link.sample.deliveries) == 1


def test_store_existing_single_sample_from_trio(orders_api, base_store, mip_status_data):

    # GIVEN a stored trio case
    new_families = orders_api.store_cases(
        customer=mip_status_data["customer"],
        order=mip_status_data["order"],
        ordered=dt.datetime.now(),
        ticket=123456,
        cases=mip_status_data["families"],
    )

    new_case = new_families[0]
    assert new_case.name == "family1"
    assert set(new_case.panels) == {"IEM"}
    assert new_case.priority_human == "standard"

    assert len(new_case.links) == 3
    new_link = new_case.links[0]
    assert new_link.mother
    assert new_link.father
    name = new_link.sample.name
    internal_id = new_link.sample.internal_id
    assert base_store.sample(internal_id)

    # WHEN storing a new case with one sample from the trio
    for family_idx, family in enumerate(mip_status_data["families"]):
        for sample_idx, sample in enumerate(family["samples"]):
            if sample["name"] == name:
                sample["internal_id"] = internal_id
                family["name"] = "single-from-trio"
            else:
                family["samples"][sample_idx] = {}

        family["samples"] = list(filter(None, family["samples"]))

        if not family["samples"]:
            mip_status_data["families"][family_idx] = {}

    mip_status_data["families"] = list(filter(None, mip_status_data["families"]))

    new_families = orders_api.store_cases(
        customer=mip_status_data["customer"],
        order=mip_status_data["order"],
        ordered=dt.datetime.now(),
        ticket=123456,
        cases=mip_status_data["families"],
    )

    # THEN there should be no complaints about missing parents
    assert len(new_families) == 1
    assert len(new_families[0].links) == 1
    assert not new_families[0].links[0].mother
    assert not new_families[0].links[0].father
