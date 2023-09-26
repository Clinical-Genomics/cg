"""Hold encryption sbatch templates in variables."""

FLOW_CELL_ENCRYPT_ERROR = """
if [[ -e {flow_cell_encrypt_dir} ]]
then
    rm -rf {flow_cell_encrypt_dir}
fi
"""

FLOW_CELL_ENCRYPT_COMMANDS = """
{symmetric_passphrase}
{asymmetrically_encrypt_passphrase}
{tar_encrypt_flow_cell_dir} | {parallel_gzip} | {tee} | {flow_cell_symmetric_encryption}
{flow_cell_symmetric_decryption} | {md5sum}
{diff}
{mv_passphrase_file}
{remove_pending_file}
"""
