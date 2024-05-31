"""Hold encryption sbatch templates in variables."""

SEQUENCING_RUN_ENCRYPT_ERROR = """
if [[ -e {pending_file_path} ]]
then
    rm -f {pending_file_path}
fi
"""

SEQUENCING_RUN_ENCRYPT_COMMANDS = """
{symmetric_passphrase}

{asymmetrically_encrypt_passphrase}

{make_tmp_encrypt_dir}

{copy_sequencing_run_dir_to_tmp}

{tar_encrypt_tmp_dir} | {parallel_gzip} | {tee} | {sequencing_run_symmetric_encryption}

{sequencing_run_symmetric_decryption} | {md5sum}

{diff}

{mv_passphrase_file}

{remove_pending_file}

{flag_as_complete}

{remove_tmp_encrypt_dir}
"""
