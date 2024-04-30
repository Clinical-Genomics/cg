"""Test CG CLI upload observations module."""

import logging

import pytest
from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.upload.observations import upload_observations_to_loqusdb
from cg.cli.upload.observations.utils import (
    get_observations_api,
    get_observations_case,
    get_sequencing_method,
)
from cg.constants import EXIT_SUCCESS
from cg.constants.constants import Workflow
from cg.constants.sequencing import SequencingMethod
from cg.constants.subject import PhenotypeStatus
from cg.exc import CaseNotFoundError, LoqusdbUploadCaseError
from cg.meta.observations.mip_dna_observations_api import MipDNAObservationsAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Case, CaseSample, Sample
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def test_observations(
    cg_context: CGConfig, cli_runner: CliRunner, helpers: StoreHelpers, caplog: LogCaptureFixture
):
    """Test upload of observations."""
    caplog.set_level(logging.DEBUG)
    store: Store = cg_context.status_db

    # GIVEN a case ready to be uploaded to Loqusdb
    case: Case = helpers.add_case(store)
    case.customer.loqus_upload = True
    sample: Sample = helpers.add_sample(store, application_type=SequencingMethod.WES)
    link: CaseSample = store.relate_sample(case=case, sample=sample, status=PhenotypeStatus.UNKNOWN)
    store.session.add(link)

    # WHEN trying to do a dry run upload to Loqusdb
    result = cli_runner.invoke(
        upload_observations_to_loqusdb, [case.internal_id, "--dry-run"], obj=cg_context
    )

    # THEN the execution should have been successful and stop at a dry run step
    assert result.exit_code == EXIT_SUCCESS
    assert "Dry run" in caplog.text


def test_get_observations_case(cg_context: CGConfig, helpers: StoreHelpers):
    """Test get observations supported case."""
    store: Store = cg_context.status_db

    # GIVEN an observations valid case
    case: Case = helpers.add_case(store)
    case.customer.loqus_upload = True

    # WHEN retrieving a case given a specific case ID
    extracted_case: Case = get_observations_case(cg_context, case.internal_id, upload=True)

    # THEN the extracted case should match the stored one
    assert extracted_case == case


def test_get_observations_case_invalid_id(cg_context: CGConfig, caplog: LogCaptureFixture):
    """Test get observations case providing an incorrect ID."""
    caplog.set_level(logging.DEBUG)

    # WHEN retrieving a case given a specific case ID
    with pytest.raises(CaseNotFoundError):
        # THEN a CaseNotFoundError should be raised
        get_observations_case(cg_context, "invalid_case_id", upload=True)

    assert "Invalid case ID. Retrieving available cases for Loqusdb actions." in caplog.text


def test_get_observations_case_to_upload(cg_context: CGConfig, helpers: StoreHelpers):
    """Test get case ready to be uploaded to Loqusdb."""
    store: Store = cg_context.status_db

    # GIVEN a case ready to be uploaded to Loqusdb
    case: Case = helpers.add_case(store)
    case.customer.loqus_upload = True

    # WHEN retrieving a case given a specific case ID
    extracted_case: Case = get_observations_case(cg_context, case.internal_id, upload=True)

    # THEN the extracted case should match the stored one
    assert extracted_case == case


def test_get_observations_api(cg_context: CGConfig, helpers: StoreHelpers):
    """Test get observation API given a Loqusdb supported case."""
    store: Store = cg_context.status_db

    # GIVEN a Loqusdb supported case
    case: Case = helpers.add_case(store, data_analysis=Workflow.MIP_DNA)
    sample: Sample = helpers.add_sample(store, application_type=SequencingMethod.WES)
    link: CaseSample = store.relate_sample(case=case, sample=sample, status=PhenotypeStatus.UNKNOWN)
    store.session.add(link)

    # WHEN retrieving the observation API
    observations_api: MipDNAObservationsAPI = get_observations_api(cg_context, case)

    # THEN a MIP-DNA API should be returned
    assert observations_api
    assert isinstance(observations_api, MipDNAObservationsAPI)


def test_get_sequencing_method(cg_context: CGConfig, helpers: StoreHelpers):
    """Test sequencing method extraction for Loqusdb upload."""
    store: Store = cg_context.status_db

    # GIVEN a case object with a WGS sequencing method
    case: Case = helpers.add_case(store)
    sample: Sample = helpers.add_sample(store, application_type=SequencingMethod.WGS)
    link: CaseSample = store.relate_sample(case=case, sample=sample, status=PhenotypeStatus.UNKNOWN)
    store.session.add(link)

    # WHEN getting the sequencing method
    sequencing_method: SequencingMethod = get_sequencing_method(case)

    # THEN the obtained sequencing method should be WGS
    assert sequencing_method == SequencingMethod.WGS


def test_get_sequencing_method_exception(
    cg_context: CGConfig,
    helpers: StoreHelpers,
    wgs_application_tag: str,
    external_wes_application_tag: str,
    caplog: LogCaptureFixture,
):
    """Test sequencing method extraction for Loqusdb upload when a case contains multiple sequencing types."""
    store: Store = cg_context.status_db

    # GIVEN a case object with a WGS and WES mixed sequencing methods
    case: Case = helpers.add_case(store)
    sample_wgs: Sample = helpers.add_sample(
        store, application_tag=wgs_application_tag, application_type=SequencingMethod.WGS
    )
    sample_wes: Sample = helpers.add_sample(
        store, application_tag=external_wes_application_tag, application_type=SequencingMethod.WES
    )
    link_1: CaseSample = store.relate_sample(
        case=case, sample=sample_wgs, status=PhenotypeStatus.UNKNOWN
    )
    link_2: CaseSample = store.relate_sample(
        case=case, sample=sample_wes, status=PhenotypeStatus.UNKNOWN
    )
    store.session.add_all([link_1, link_2])

    # WHEN getting the sequencing method
    with pytest.raises(LoqusdbUploadCaseError):
        # THEN a LoqusdbUploadCaseError should be raised
        get_sequencing_method(case)

    assert f"Case {case.internal_id} has a mixed analysis type. Cancelling action." in caplog.text
