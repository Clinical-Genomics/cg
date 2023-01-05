import datetime as dt
from copy import deepcopy

import pytest

from cg.constants import DataDelivery, Pipeline
from cg.constants.constants import CaseActions
from cg.exc import OrderError
from cg.meta.orders.api import FastqSubmitter
from cg.meta.orders.balsamic_submitter import BalsamicSubmitter
from cg.meta.orders.balsamic_qc_submitter import BalsamicQCSubmitter
from cg.meta.orders.balsamic_umi_submitter import BalsamicUmiSubmitter
from cg.meta.orders.metagenome_submitter import MetagenomeSubmitter
from cg.meta.orders.microbial_submitter import MicrobialSubmitter
from cg.meta.orders.mip_dna_submitter import MipDnaSubmitter
from cg.meta.orders.mip_rna_submitter import MipRnaSubmitter
from cg.meta.orders.rml_submitter import RmlSubmitter
from cg.meta.orders.sars_cov_2_submitter import SarsCov2Submitter
from cg.meta.orders.submitter import Submitter
from cg.models.orders.order import OrderIn, OrderType
from cg.meta.orders import OrdersAPI
from cg.store import Store

from cg.constants import Priority


def test_pools_to_status(rml_order_to_submit):
    # GIVEN a rml order with three samples in one pool
    order = OrderIn.parse_obj(rml_order_to_submit, OrderType.RML)

    # WHEN parsing for status
    data = RmlSubmitter.order_to_status(order=order)

    # THEN it should pick out the general information
    assert data["customer"] == "cust000"
    assert data["order"] == "#123456"
    assert data["comment"] == "order comment"

    # ... and information about the pool(s)
    assert len(data["pools"]) == 2
    pool = data["pools"][0]
    assert pool["name"] == "pool-1"
    assert pool["application"] == "RMLP05R800"
    assert pool["data_analysis"] == str(Pipeline.FASTQ)
    assert pool["data_delivery"] == str(DataDelivery.FASTQ)
    assert len(pool["samples"]) == 2
    sample = pool["samples"][0]
    assert sample["name"] == "sample1"
    assert sample["comment"] == "test comment"
    assert pool["priority"] == "research"
    assert sample["control"] == "negative"


def test_samples_to_status(fastq_order_to_submit):
    # GIVEN fastq order with two samples
    order = OrderIn.parse_obj(fastq_order_to_submit, OrderType.FASTQ)

    # WHEN parsing for status
    data = FastqSubmitter.order_to_status(order=order)

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
    order = OrderIn.parse_obj(metagenome_order_to_submit, OrderType.METAGENOME)

    # WHEN parsing for status
    data = MetagenomeSubmitter.order_to_status(order=order)
    case = data["families"][0]
    # THEN it should pick out samples and relevant information
    assert len(case["samples"]) == 2
    first_sample = case["samples"][0]
    assert first_sample["name"] == "Bristol"
    assert first_sample["application"] == "METLIFR020"
    assert first_sample["priority"] == "standard"
    assert first_sample["volume"] == "1"


def test_microbial_samples_to_status(microbial_order_to_submit):
    # GIVEN microbial order with three samples
    order = OrderIn.parse_obj(microbial_order_to_submit, OrderType.MICROSALT)

    # WHEN parsing for status
    data = MicrobialSubmitter.order_to_status(order=order)

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
    order = OrderIn.parse_obj(sarscov2_order_to_submit, OrderType.SARS_COV_2)

    # WHEN parsing for status
    data = SarsCov2Submitter.order_to_status(order=order)

    # THEN it should pick out samples and relevant information
    assert len(data["samples"]) == 5
    assert data["customer"] == "cust002"
    assert data["order"] == "Sars-CoV-2 samples"
    assert data["comment"] == "Order comment"
    assert data["data_analysis"] == str(Pipeline.SARS_COV_2)
    assert data["data_delivery"] == str(DataDelivery.FASTQ)

    # THEN first sample should contain all the relevant data from the microbial order
    sample_data = data["samples"][0]
    assert sample_data.get("internal_id") is None
    assert sample_data["priority"] == "research"
    assert sample_data["application"] == "VWGDPTR001"
    assert sample_data["comment"] == "plate comment"
    assert sample_data["name"] == "all-fields"
    assert sample_data["organism_id"] == "SARS CoV-2"
    assert sample_data["reference_genome"] == "NC_111"
    assert sample_data["volume"] == "1"


def test_cases_to_status(mip_order_to_submit):

    # GIVEN a scout order with a trio case
    project: OrderType = OrderType.MIP_DNA
    order = OrderIn.parse_obj(mip_order_to_submit, project=project)

    # WHEN parsing for status
    data = MipDnaSubmitter.order_to_status(order=order)

    # THEN it should pick out the case
    assert len(data["families"]) == 2
    family = data["families"][0]
    assert family["name"] == "family1"
    assert family["data_analysis"] == str(Pipeline.MIP_DNA)
    assert family["data_delivery"] == str(DataDelivery.SCOUT)
    assert family["priority"] == Priority.standard.name
    assert family["cohorts"] == ["Other"]
    assert (
        family["synopsis"]
        == "As for the synopsis it will be this overly complex sentence to prove that the synopsis field might in fact be a very long string, which we should be prepared for."
    )
    assert set(family["panels"]) == {"IEM"}
    assert len(family["samples"]) == 3

    first_sample = family["samples"][0]
    assert first_sample["age_at_sampling"] == 17.18192
    assert first_sample["name"] == "sample1"
    assert first_sample["application"] == "WGSPCFC030"
    assert first_sample["phenotype_groups"] == ["Phenotype-group"]
    assert first_sample["phenotype_terms"] == ["HP:0012747", "HP:0025049"]
    assert first_sample["sex"] == "female"
    assert first_sample["status"] == "affected"
    assert first_sample["subject_id"] == "subject1"
    assert first_sample["mother"] == "sample2"
    assert first_sample["father"] == "sample3"

    # ... second sample has a comment
    assert isinstance(family["samples"][1]["comment"], str)


def test_cases_to_status_synopsis(mip_order_to_submit):
    # GIVEN a scout order with a trio case where synopsis is None
    modified_order: dict = deepcopy(mip_order_to_submit)
    for sample in modified_order["samples"]:
        sample["synopsis"] = None

    project: OrderType = OrderType.MIP_DNA
    order = OrderIn.parse_obj(mip_order_to_submit, project=project)

    # WHEN parsing for status
    MipDnaSubmitter.order_to_status(order=order)

    # THEN No exception should have been raised on synopsis


def test_store_rml(orders_api, base_store, rml_status_data, ticket: str):
    # GIVEN a basic store with no samples and a rml order
    assert base_store.pools().count() == 0
    assert base_store.families().count() == 0
    assert base_store.samples().count() == 0

    submitter: RmlSubmitter = RmlSubmitter(lims=orders_api.lims, status=orders_api.status)

    # WHEN storing the order
    new_pools = submitter.store_items_in_status(
        customer=rml_status_data["customer"],
        order=rml_status_data["order"],
        ordered=dt.datetime.now(),
        ticket=ticket,
        items=rml_status_data["pools"],
    )

    # THEN it should update the database with new pools
    assert len(new_pools) == 2

    assert base_store.pools().count() == base_store.families().count()
    assert base_store.samples().count() == 4

    assert base_store.samples().filter_by(control="negative").count() == 1

    new_pool = base_store.pools().first()
    assert new_pool == new_pools[1]

    assert new_pool.name == "pool-2"
    assert new_pool.application_version.application.tag == "RMLP05R800"
    assert not hasattr(new_pool, "data_analysis")

    # ... and add a delivery
    assert len(new_pool.deliveries) == 1
    assert new_pool.deliveries[0].destination == "caesar"

    new_case = base_store.families().first()
    assert new_case.data_analysis == str(Pipeline.FASTQ)
    assert new_case.data_delivery == str(DataDelivery.FASTQ)

    # and that the pool is set for invoicing but not the samples of the pool
    assert not new_pool.no_invoice
    for link in new_case.links:
        assert link.sample.no_invoice


def test_store_samples(orders_api, base_store, fastq_status_data, ticket: str):
    # GIVEN a basic store with no samples and a fastq order
    assert base_store.samples().count() == 0
    assert base_store.families().count() == 0

    submitter: FastqSubmitter = FastqSubmitter(lims=orders_api.lims, status=orders_api.status)

    # WHEN storing the order
    new_samples = submitter.store_items_in_status(
        customer=fastq_status_data["customer"],
        order=fastq_status_data["order"],
        ordered=dt.datetime.now(),
        ticket=ticket,
        items=fastq_status_data["samples"],
    )

    # THEN it should store the samples and create a case for each sample
    assert len(new_samples) == 2
    assert base_store.samples().count() == 2
    assert base_store.families().count() == 2
    first_sample = new_samples[0]
    assert len(first_sample.links) == 2
    family_link = first_sample.links[0]
    assert family_link.family in base_store.families()
    for sample in new_samples:
        assert len(sample.deliveries) == 1
    assert family_link.family.data_analysis
    assert family_link.family.data_delivery in [DataDelivery.FASTQ, DataDelivery.NO_DELIVERY]


def test_store_samples_sex_stored(orders_api, base_store, fastq_status_data, ticket: str):
    # GIVEN a basic store with no samples and a fastq order
    assert base_store.samples().count() == 0
    assert base_store.families().count() == 0

    submitter = FastqSubmitter(lims=orders_api.lims, status=orders_api.status)

    # WHEN storing the order
    new_samples = submitter.store_items_in_status(
        customer=fastq_status_data["customer"],
        order=fastq_status_data["order"],
        ordered=dt.datetime.now(),
        ticket=ticket,
        items=fastq_status_data["samples"],
    )

    # THEN the sample sex should be stored
    assert new_samples[0].sex == "male"


def test_store_fastq_samples_non_tumour_wgs_to_mip(orders_api, base_store, fastq_status_data):
    # GIVEN a basic store with no samples and a non-tumour fastq order as wgs
    assert base_store.samples().count() == 0
    assert base_store.families().count() == 0
    base_store.application(fastq_status_data["samples"][0]["application"]).prep_category = "wgs"
    fastq_status_data["samples"][0]["tumour"] = False

    submitter = FastqSubmitter(lims=orders_api.lims, status=orders_api.status)

    # WHEN storing the order
    new_samples = submitter.store_items_in_status(
        customer=fastq_status_data["customer"],
        order=fastq_status_data["order"],
        ordered=dt.datetime.now(),
        ticket=1234348,
        items=fastq_status_data["samples"],
    )

    # THEN the analysis for the case should be MAF
    assert new_samples[0].links[0].family.data_analysis == Pipeline.MIP_DNA


def test_store_fastq_samples_tumour_wgs_to_fastq(
    orders_api, base_store, fastq_status_data, ticket: str
):
    # GIVEN a basic store with no samples and a tumour fastq order as wgs
    assert base_store.samples().count() == 0
    assert base_store.families().count() == 0
    base_store.application(fastq_status_data["samples"][0]["application"]).prep_category = "wgs"
    fastq_status_data["samples"][0]["tumour"] = True

    submitter = FastqSubmitter(lims=orders_api.lims, status=orders_api.status)

    # WHEN storing the order
    new_samples = submitter.store_items_in_status(
        customer=fastq_status_data["customer"],
        order=fastq_status_data["order"],
        ordered=dt.datetime.now(),
        ticket=ticket,
        items=fastq_status_data["samples"],
    )

    # THEN the analysis for the case should be FASTQ
    assert new_samples[0].links[0].family.data_analysis == Pipeline.FASTQ


def test_store_fastq_samples_non_wgs_as_fastq(
    orders_api, base_store, fastq_status_data, ticket: str
):
    # GIVEN a basic store with no samples and a fastq order as non wgs
    assert base_store.samples().count() == 0
    assert base_store.families().count() == 0
    non_wgs_prep_category = "wes"
    assert base_store.applications(category=non_wgs_prep_category)
    for sample in fastq_status_data["samples"]:
        sample["application"] = base_store.applications(category=non_wgs_prep_category)[0].tag

    submitter = FastqSubmitter(lims=orders_api.lims, status=orders_api.status)

    # WHEN storing the order
    new_samples = submitter.store_items_in_status(
        customer=fastq_status_data["customer"],
        order=fastq_status_data["order"],
        ordered=dt.datetime.now(),
        ticket=ticket,
        items=fastq_status_data["samples"],
    )

    # THEN the analysis for the case should be fastq (none)
    assert new_samples[0].links[0].family.data_analysis == Pipeline.FASTQ


def test_store_samples_bad_apptag(orders_api, base_store, fastq_status_data, ticket: str):
    # GIVEN a basic store with no samples and a fastq order
    assert base_store.samples().count() == 0
    assert base_store.families().count() == 0

    for sample in fastq_status_data["samples"]:
        sample["application"] = "nonexistingtag"

    submitter = FastqSubmitter(lims=orders_api.lims, status=orders_api.status)

    # THEN it should raise OrderError
    with pytest.raises(OrderError):
        # WHEN storing the order
        submitter.store_items_in_status(
            customer=fastq_status_data["customer"],
            order=fastq_status_data["order"],
            ordered=dt.datetime.now(),
            ticket=ticket,
            items=fastq_status_data["samples"],
        )


def test_store_microbial_samples(orders_api, base_store, microbial_status_data, ticket: str):
    # GIVEN a basic store with no samples and a microbial order and one Organism
    assert base_store.samples().count() == 0
    assert base_store.families().count() == 0
    assert base_store.organisms().count() == 1

    submitter = MicrobialSubmitter(lims=orders_api.lims, status=orders_api.status)

    # WHEN storing the order
    new_samples = submitter.store_items_in_status(
        customer=microbial_status_data["customer"],
        order=microbial_status_data["order"],
        ordered=dt.datetime.now(),
        ticket=ticket,
        items=microbial_status_data["samples"],
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


def test_store_microbial_case_data_analysis_stored(
    orders_api, base_store, microbial_status_data, ticket: str
):
    # GIVEN a basic store with no samples and a microbial order and one Organism
    assert base_store.samples().count() == 0
    assert base_store.families().count() == 0

    submitter = MicrobialSubmitter(lims=orders_api.lims, status=orders_api.status)

    # WHEN storing the order
    submitter.store_items_in_status(
        customer=microbial_status_data["customer"],
        order=microbial_status_data["order"],
        ordered=dt.datetime.now(),
        ticket=ticket,
        items=microbial_status_data["samples"],
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


def test_store_microbial_sample_priority(
    orders_api, base_store, microbial_status_data, ticket: str
):
    # GIVEN a basic store with no samples
    assert base_store.samples().count() == 0

    submitter = MicrobialSubmitter(lims=orders_api.lims, status=orders_api.status)

    # WHEN storing the order
    submitter.store_items_in_status(
        customer=microbial_status_data["customer"],
        order=microbial_status_data["order"],
        ordered=dt.datetime.now(),
        ticket=ticket,
        items=microbial_status_data["samples"],
        comment="",
        data_analysis=Pipeline.MICROSALT,
        data_delivery=DataDelivery.FASTQ_QC,
    )

    # THEN it should store the sample priority
    assert base_store.samples().count() > 0
    microbial_sample = base_store.samples().first()

    assert microbial_sample.priority_human == "research"


def test_store_mip(orders_api, base_store, mip_status_data, ticket: str):
    # GIVEN a basic store with no samples or nothing in it + scout order
    assert base_store.samples().first() is None
    assert base_store.families().first() is None

    submitter: MipDnaSubmitter = MipDnaSubmitter(lims=orders_api.lims, status=orders_api.status)

    # WHEN storing the order
    new_families = submitter.store_items_in_status(
        customer=mip_status_data["customer"],
        order=mip_status_data["order"],
        ordered=dt.datetime.now(),
        ticket=ticket,
        items=mip_status_data["families"],
    )

    # THEN it should create and link samples and the case
    assert len(new_families) == 2
    new_case = new_families[0]
    assert new_case.name == "family1"
    assert set(new_case.panels) == {"IEM"}
    assert new_case.priority_human == Priority.standard.name

    assert len(new_case.links) == 3
    new_link = new_case.links[0]
    assert new_case.data_analysis == str(Pipeline.MIP_DNA)
    assert new_case.data_delivery == str(DataDelivery.SCOUT)
    assert set(new_case.cohorts) == {"Other"}
    assert (
        new_case.synopsis
        == "As for the synopsis it will be this overly complex sentence to prove that the synopsis field might in fact be a very long string, which we should be prepared for."
    )
    assert new_link.status == "affected"
    assert new_link.mother.name == "sample2"
    assert new_link.father.name == "sample3"
    assert new_link.sample.name == "sample1"
    assert new_link.sample.sex == "female"
    assert new_link.sample.application_version.application.tag == "WGSPCFC030"
    assert new_link.sample.is_tumour
    assert isinstance(new_case.links[1].sample.comment, str)

    assert set(new_link.sample.phenotype_groups) == {"Phenotype-group"}
    assert set(new_link.sample.phenotype_terms) == {"HP:0012747", "HP:0025049"}
    assert new_link.sample.subject_id == "subject1"

    assert new_link.sample.age_at_sampling == 17.18192

    assert base_store.deliveries().count() == base_store.samples().count()
    for link in new_case.links:
        assert len(link.sample.deliveries) == 1


def test_store_mip_rna(orders_api, base_store, mip_rna_status_data, ticket: str):
    # GIVEN a basic store with no samples or nothing in it + rna order
    rna_application = "RNAPOAR025"
    assert base_store.samples().first() is None
    assert base_store.families().first() is None
    assert base_store.application(rna_application)

    submitter: MipRnaSubmitter = MipRnaSubmitter(lims=orders_api.lims, status=orders_api.status)

    # WHEN storing the order
    new_cases = submitter.store_items_in_status(
        customer=mip_rna_status_data["customer"],
        order=mip_rna_status_data["order"],
        ordered=dt.datetime.now(),
        ticket=ticket,
        items=mip_rna_status_data["families"],
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


def test_store_metagenome_samples(orders_api, base_store, metagenome_status_data, ticket: str):
    # GIVEN a basic store with no samples and a metagenome order
    assert base_store.samples().count() == 0

    submitter = MetagenomeSubmitter(lims=orders_api.lims, status=orders_api.status)

    # WHEN storing the order
    new_samples = submitter.store_items_in_status(
        customer=metagenome_status_data["customer"],
        order=metagenome_status_data["order"],
        ordered=dt.datetime.now(),
        ticket=ticket,
        items=metagenome_status_data["families"],
    )

    # THEN it should store the samples
    assert len(new_samples) == 2
    assert base_store.samples().count() == 2


def test_store_metagenome_samples_bad_apptag(
    orders_api, base_store, metagenome_status_data, ticket: str
):
    # GIVEN a basic store with no samples and a metagenome order
    assert base_store.samples().count() == 0

    for sample in metagenome_status_data["families"][0]["samples"]:
        sample["application"] = "nonexistingtag"

    submitter = MetagenomeSubmitter(lims=orders_api.lims, status=orders_api.status)

    # THEN it should raise OrderError
    with pytest.raises(OrderError):
        # WHEN storing the order
        submitter.store_items_in_status(
            customer=metagenome_status_data["customer"],
            order=metagenome_status_data["order"],
            ordered=dt.datetime.now(),
            ticket=ticket,
            items=metagenome_status_data["families"],
        )


@pytest.mark.parametrize(
    "submitter", [BalsamicSubmitter, BalsamicQCSubmitter, BalsamicUmiSubmitter]
)
def test_store_cancer_samples(orders_api, base_store, balsamic_status_data, submitter, ticket: str):
    # GIVEN a basic store with no samples and a cancer order
    assert base_store.samples().first() is None
    assert base_store.families().first() is None

    submitter: Submitter = submitter(lims=orders_api.lims, status=orders_api.status)

    # WHEN storing the order
    new_families = submitter.store_items_in_status(
        customer=balsamic_status_data["customer"],
        order=balsamic_status_data["order"],
        ordered=dt.datetime.now(),
        ticket=ticket,
        items=balsamic_status_data["families"],
    )

    # THEN it should create and link samples and the case
    assert len(new_families) == 1
    new_case = new_families[0]
    assert new_case.name == "family1"
    assert new_case.data_analysis in [
        str(Pipeline.BALSAMIC),
        str(Pipeline.BALSAMIC_QC),
        str(Pipeline.BALSAMIC_UMI),
    ]
    assert new_case.data_delivery == str(DataDelivery.FASTQ_ANALYSIS_SCOUT)
    assert set(new_case.panels) == set()
    assert new_case.priority_human == Priority.standard.name

    assert len(new_case.links) == 1
    new_link = new_case.links[0]
    assert new_link.sample.name == "s1"
    assert new_link.sample.sex == "male"
    assert new_link.sample.application_version.application.tag == "WGSPCFC030"
    assert new_link.sample.comment == "other Elution buffer"
    assert new_link.sample.is_tumour

    assert base_store.deliveries().count() == base_store.samples().count()
    for link in new_case.links:
        assert len(link.sample.deliveries) == 1


def test_store_existing_single_sample_from_trio(
    orders_api, base_store, mip_status_data, ticket: str
):

    # GIVEN a stored trio case
    submitter: MipDnaSubmitter = MipDnaSubmitter(lims=orders_api.lims, status=orders_api.status)
    new_families = submitter.store_items_in_status(
        customer=mip_status_data["customer"],
        order=mip_status_data["order"],
        ordered=dt.datetime.now(),
        ticket=ticket,
        items=mip_status_data["families"],
    )

    new_case = new_families[0]
    assert new_case.name == "family1"
    assert set(new_case.panels) == {"IEM"}
    assert new_case.priority_human == Priority.standard.name

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

    submitter: MipDnaSubmitter = MipDnaSubmitter(lims=orders_api.lims, status=orders_api.status)
    new_families = submitter.store_items_in_status(
        customer=mip_status_data["customer"],
        order=mip_status_data["order"],
        ordered=dt.datetime.now(),
        ticket=ticket,
        items=mip_status_data["families"],
    )

    # THEN there should be no complaints about missing parents
    assert len(new_families) == 1
    assert len(new_families[0].links) == 1
    assert not new_families[0].links[0].mother
    assert not new_families[0].links[0].father


def test_store_existing_case(
    orders_api: OrdersAPI, base_store: Store, mip_status_data: dict, ticket: str
):
    # GIVEN a basic store with no samples or nothing in it + scout order
    assert base_store.samples().first() is None
    assert base_store.families().first() is None

    submitter: MipDnaSubmitter = MipDnaSubmitter(lims=orders_api.lims, status=orders_api.status)

    # WHEN storing the order
    submitter.store_items_in_status(
        customer=mip_status_data["customer"],
        order=mip_status_data["order"],
        ordered=dt.datetime.now(),
        ticket=ticket,
        items=mip_status_data["families"],
    )

    base_store.close()
    new_cases = base_store.families().all()

    # Save internal id
    stored_cases_internal_ids = dict([(case["name"], case["internal_id"]) for case in new_cases])
    for case in mip_status_data["families"]:
        case["internal_id"] = stored_cases_internal_ids[case["name"]]

    submitter.store_items_in_status(
        customer=mip_status_data["customer"],
        order=mip_status_data["order"],
        ordered=dt.datetime.now(),
        ticket=ticket,
        items=mip_status_data["families"],
    )

    base_store.close()
    rerun_cases = base_store.families().all()

    # THEN the sample ticket should be appended to previos ticket and action set to analyze
    assert rerun_cases[0].tickets == f"{ticket},{ticket}"
    assert rerun_cases[0].action == CaseActions.ANALYZE
