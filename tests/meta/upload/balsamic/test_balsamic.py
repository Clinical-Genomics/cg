from pathlib import Path

from mock import create_autospec

from cg.meta.upload.balsamic.balsamic import BalsamicUploadAPI
from cg.models.cg_config import (
    BalsamicConfig,
    CGConfig,
    IlluminaConfig,
    RunInstruments,
    SlurmConfig,
)
from cg.store.store import Store


def test_upload_with_case_uploading_to_customer_inbox():
    # GIVEN a Balsamic Upload API
    cg_config: CGConfig = create_autospec(
        CGConfig,
        balsamic=create_autospec(
            BalsamicConfig,
            balsamic_cache=Path("balsamic_cache"),
            bed_path=Path("bed_path"),
            binary_path="balsamic_binary",
            cache_version="autospec_data",
            cadd_path="autospec_data",
            cancer_genelist="autospec_data",
            conda_binary="autospec_data",
            conda_env="autospec_data",
            cosmic_path="autospec_data",
            genome_interval_path="autospec_data",
            gens_coverage_female_path="autospec_data",
            gens_coverage_male_path="autospec_data",
            gnomad_af5_path="autospec_data",
            head_job_partition="autospec_data",
            loqusdb_path="autospec_data",
            pon_path="pon_path",
            slurm=create_autospec(
                SlurmConfig,
                account="account",
                mail_user="mail@clinicalgenomics.se",
                qos="high",
            ),
            root="root",
            sentieon_licence_path="autospec_data",
            sentieon_licence_server="autospec_data",
            swegen_path="autospec_drata",
            swegen_snv="rautospec_data",
            swegen_sv="rautospec_data",
        ),
        status_db=create_autospec(Store),
        run_instruments=create_autospec(
            RunInstruments,
            illumina=create_autospec(IlluminaConfig, demultiplexed_runs_dir="some_dir"),
        ),
    )
    balsamic_upload_api = BalsamicUploadAPI(config=cg_config)

    # WHEN uploading a case
