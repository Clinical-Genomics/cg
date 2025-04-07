from pathlib import Path
from unittest import mock

import pytest

from cg.constants.constants import FileFormat
from cg.exc import CgDataError
from cg.io.controller import WriteFile
from cg.services.analysis_starter.configurator.file_creators.microsalt_config import (
    MicrosaltConfigFileCreator,
)
from cg.store.models import Case, Organism, Sample
from cg.store.store import Store


def test_create_success(
    microsalt_config_file_creator: MicrosaltConfigFileCreator, microsalt_case_id: str
):
    # GIVEN a microsalt_config_file_creator
    with mock.patch.object(WriteFile, "write_file_from_content", return_value=True) as file_writer:
        # WHEN creating a microsalt config file
        microsalt_config_file_creator.create(microsalt_case_id)
        # THEN it should be written to disk as json
        file_writer.assert_called_once_with(
            content=mock.ANY,
            file_format=FileFormat.JSON,
            file_path=Path(
                microsalt_config_file_creator.queries_path,
                f"{microsalt_case_id}.{FileFormat.JSON}",
            ),
        )


def test_create_failure_missing_organism(
    microsalt_config_file_creator: MicrosaltConfigFileCreator, microsalt_case_id: str
):
    # GIVEN a microSALT case containing a sample with a missing organism
    store: Store = microsalt_config_file_creator.store
    case: Case = store.get_case_by_internal_id(microsalt_case_id)
    sample: Sample = case.samples[0]
    sample.organism = None

    with pytest.raises(CgDataError) as error:
        # WHEN creating the case's config file
        # THEN the method should raise a CgDataError
        microsalt_config_file_creator.create(microsalt_case_id)
        assert error.value == "Organism missing on Sample"


def test_organism_override(microsalt_store: Store, microsalt_case_id: str):

    # GIVEN a store containing specific organisms
    organism_1: Organism = microsalt_store.add_organism(
        internal_id="gonorrhoeae borealis", name="Aurora"
    )
    organism_2: Organism = microsalt_store.add_organism(
        internal_id="Cutibacterium acnes borealis", name="Aurora"
    )

    # GIVEN that a sample specifies organism_1
    case: Case = microsalt_store.get_case_by_internal_id(microsalt_case_id)
    sample: Sample = case.samples[0]
    sample.organism = organism_1

    # WHEN getting the organism for the sample
    # THEN the organism we get from the MicrosaltConfigurator is transformed
    assert MicrosaltConfigFileCreator._get_organism(sample) == "Neisseria spp."

    # GIVEN that a sample specifies organism_2
    sample.organism = organism_2

    # WHEN getting the organism for the sample
    # THEN the organism we get from the MicrosaltConfigurator is transformed
    assert MicrosaltConfigFileCreator._get_organism(sample) == "Propionibacterium acnes"


def test_reference_genome_override(microsalt_store: Store, microsalt_case_id: str):

    # GIVEN a store containing VRE organisms
    organism_1: Organism = microsalt_store.add_organism(
        internal_id="VRE", name="VRE", reference_genome="NC_017960.1"
    )
    organism_2: Organism = microsalt_store.add_organism(
        internal_id="VRE", name="VRE", reference_genome="NC_004668.1"
    )

    # GIVEN that a sample specifies organism_1
    case: Case = microsalt_store.get_case_by_internal_id(microsalt_case_id)
    sample: Sample = case.samples[0]
    sample.organism = organism_1

    # WHEN getting the organism for the sample
    # THEN the organism we get from the MicrosaltConfigurator is transformed
    assert MicrosaltConfigFileCreator._get_organism(sample) == "Enterococcus faecium"

    # GIVEN that a sample specifies organism_2
    sample.organism = organism_2

    # WHEN getting the organism for the sample
    # THEN the organism we get from the MicrosaltConfigurator is transformed
    assert MicrosaltConfigFileCreator._get_organism(sample) == "Enterococcus faecalis"
