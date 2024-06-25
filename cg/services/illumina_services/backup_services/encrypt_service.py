from pathlib import Path

from cg.apps.slurm.slurm_api import SlurmAPI
from cg.constants import FileExtensions, SPACE
from cg.constants.encryption import GPGParameters
from cg.constants.priority import SlurmQos
from cg.exc import FlowCellError, IlluminaRunEncryptionError
from cg.meta.encryption.encryption import EncryptionAPI, LIMIT_PIGZ_TASK, LOG
from cg.meta.encryption.sbatch import ILLUMINA_RUN_ENCRYPT_ERROR, ILLUMINA_RUN_ENCRYPT_COMMANDS
from cg.meta.tar.tar import TarAPI
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from cg.models.slurm.sbatch import Sbatch


class IlluminaRunEncryptionService(EncryptionAPI):
    """Encryption functionality for Illumina sequencing runs."""

    def __init__(
        self,
        binary_path: str,
        encryption_dir: Path,
        run_dir_data: IlluminaRunDirectoryData,
        pigz_binary_path: str,
        sbatch_parameter: dict[str, str | int],
        slurm_api: SlurmAPI,
        tar_api: TarAPI,
        dry_run: bool = False,
    ):
        super().__init__(binary_path=binary_path, dry_run=dry_run)
        self.run_dir_data: IlluminaRunDirectoryData = run_dir_data
        self.encryption_dir: Path = encryption_dir
        self.tar_api: TarAPI = tar_api
        self.pigz_binary_path: str = pigz_binary_path
        self.slurm_api: SlurmAPI = slurm_api
        self.slurm_account: str = sbatch_parameter.get("account")
        self.slurm_hours: int = sbatch_parameter.get("hours")
        self.slurm_mail_user: str = sbatch_parameter.get("mail_user")
        self.slurm_memory: int = sbatch_parameter.get("memory")
        self.slurm_number_tasks: int = sbatch_parameter.get("number_tasks")
        self.slurm_api.set_dry_run(dry_run=self.dry_run)

    @property
    def run_encryption_dir(self) -> Path:
        return Path(self.encryption_dir, self.run_dir_data.full_name)

    @property
    def run_encrypt_tmp_dir(self) -> Path:
        return Path(self.run_encryption_dir, "tmp")

    @property
    def run_encrypt_file_path_prefix(self) -> Path:
        return Path(self.run_encryption_dir, self.run_dir_data.id)

    @property
    def pending_file_path(self) -> Path:
        return Path(self.run_encrypt_file_path_prefix.with_suffix(FileExtensions.PENDING))

    @property
    def complete_file_path(self) -> Path:
        return Path(self.run_encrypt_file_path_prefix.with_suffix(FileExtensions.COMPLETE))

    @property
    def encrypted_gpg_file_path(self) -> Path:
        return Path(
            self.run_encrypt_file_path_prefix.with_suffix(
                f"{FileExtensions.TAR}{FileExtensions.GZIP}{FileExtensions.GPG}"
            )
        )

    @property
    def encrypted_md5sum_file_path(self) -> Path:
        return Path(
            self.run_encrypt_file_path_prefix.with_suffix(
                f"{FileExtensions.TAR}{FileExtensions.GZIP}{FileExtensions.MD5SUM}"
            )
        )

    @property
    def decrypted_md5sum_file_path(self) -> Path:
        return Path(
            self.run_encrypt_file_path_prefix.with_suffix(
                f"{FileExtensions.TAR}{FileExtensions.GZIP}.degpg{FileExtensions.MD5SUM}"
            )
        )

    @property
    def symmetric_passphrase_file_path(self) -> Path:
        return Path(self.run_encrypt_file_path_prefix.with_suffix(FileExtensions.PASS_PHRASE))

    @property
    def final_passphrase_file_path(self) -> Path:
        return Path(self.run_encrypt_file_path_prefix.with_suffix(f".key{FileExtensions.GPG}"))

    def get_run_symmetric_encryption_command(
        self, output_file: Path, passphrase_file_path: Path
    ) -> str:
        """Generates the Gpg command for symmetric encryption of file."""
        encryption_parameters: list[str] = (
            [self.binary_path]
            + GPGParameters.SYMMETRIC_ENCRYPTION
            + [passphrase_file_path.as_posix()]
            + GPGParameters.OUTPUT_PARAMETER
            + [output_file.as_posix()]
        )
        return SPACE.join(encryption_parameters)

    def get_run_symmetric_decryption_command(
        self, input_file: Path, passphrase_file_path: Path
    ) -> str:
        """Generates the Gpg command for symmetric decryption."""
        decryption_parameters: list[str] = (
            [self.binary_path]
            + GPGParameters.SYMMETRIC_DECRYPTION
            + [passphrase_file_path.as_posix(), input_file.as_posix()]
        )
        return SPACE.join(decryption_parameters)

    def is_encryption_possible(self) -> bool | None:
        """Check if requirements for encryption are meet.
        Raises:
            FlowCellError if sequencing is not ready, encryption is pending or complete.
        """
        if not self.run_dir_data.is_sequencing_run_ready():
            raise FlowCellError(f"Run: {self.run_dir_data.id} is not ready")
        if self.complete_file_path.exists():
            raise IlluminaRunEncryptionError(
                f"Encryption already completed for run: {self.run_dir_data.id}"
            )
        if self.pending_file_path.exists():
            raise IlluminaRunEncryptionError(
                f"Encryption already started for run: {self.run_dir_data.id}"
            )
        return True

    def make_tmp_encrypt_dir(self) -> str:
        return f"mkdir -p {self.run_encrypt_tmp_dir}"

    def copy_run_dir_to_tmp(self) -> str:
        return f"cp -r {self.run_dir_data.path} {self.run_encrypt_tmp_dir}"

    def remove_tmp_encrypt_dir(self) -> str:
        return f"rm -rf {self.run_encrypt_tmp_dir}"

    def encrypt_run(
        self,
    ) -> None:
        """Encrypt a sequencing run via GPG and SLURM."""
        error_function: str = ILLUMINA_RUN_ENCRYPT_ERROR.format(
            pending_file_path=self.pending_file_path
        )
        commands: str = ILLUMINA_RUN_ENCRYPT_COMMANDS.format(
            symmetric_passphrase=self.get_symmetric_passphrase_cmd(
                passphrase_file_path=self.symmetric_passphrase_file_path
            ),
            asymmetrically_encrypt_passphrase=self.get_asymmetrically_encrypt_passphrase_cmd(
                passphrase_file_path=self.symmetric_passphrase_file_path
            ),
            make_tmp_encrypt_dir=self.make_tmp_encrypt_dir(),
            copy_run_dir_to_tmp=self.copy_run_dir_to_tmp(),
            tar_encrypt_tmp_dir=self.tar_api.get_compress_cmd(input_path=self.run_encrypt_tmp_dir),
            parallel_gzip=f"{self.pigz_binary_path} -p {self.slurm_number_tasks - LIMIT_PIGZ_TASK} --fast -c",
            tee=f"tee >(md5sum > {self.encrypted_md5sum_file_path})",
            run_symmetric_encryption=self.get_run_symmetric_encryption_command(
                output_file=self.encrypted_gpg_file_path,
                passphrase_file_path=self.symmetric_passphrase_file_path,
            ),
            run_symmetric_decryption=self.get_run_symmetric_decryption_command(
                input_file=self.encrypted_gpg_file_path,
                passphrase_file_path=self.symmetric_passphrase_file_path,
            ),
            md5sum=f"md5sum > {self.decrypted_md5sum_file_path}",
            diff=f"diff -q {self.encrypted_md5sum_file_path} {self.decrypted_md5sum_file_path}",
            mv_passphrase_file=f"mv {self.symmetric_passphrase_file_path.with_suffix(FileExtensions.GPG)} {self.final_passphrase_file_path}",
            remove_pending_file=f"rm -f {self.pending_file_path}",
            flag_as_complete=f"touch {self.complete_file_path}",
            remove_tmp_encrypt_dir=self.remove_tmp_encrypt_dir(),
        )
        sbatch_parameters = Sbatch(
            account=self.slurm_account,
            commands=commands,
            email=self.slurm_mail_user,
            error=error_function,
            hours=self.slurm_hours,
            job_name="_".join([self.run_dir_data.id, "flow_cell_encryption"]),
            log_dir=self.run_encryption_dir.as_posix(),
            memory=self.slurm_memory,
            number_tasks=self.slurm_number_tasks,
            quality_of_service=SlurmQos.HIGH,
        )
        sbatch_content: str = self.slurm_api.generate_sbatch_content(sbatch_parameters)
        sbatch_path = Path(self.run_encrypt_file_path_prefix.with_suffix(FileExtensions.SBATCH))
        sbatch_number: int = self.slurm_api.submit_sbatch(
            sbatch_content=sbatch_content, sbatch_path=sbatch_path
        )
        LOG.info(f"Run encryption running as job {sbatch_number}")

    def start_encryption(self) -> None:
        """Start encryption if requirements are met."""
        self.is_encryption_possible()
        self.run_encryption_dir.mkdir(exist_ok=True, parents=True)
        self.create_pending_file(pending_path=self.pending_file_path)
        self.encrypt_run()
