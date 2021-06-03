"""Sbatch templates for the rsync function"""

RSYNC_COMMAND = """
cg deliver rsync {ticket_id}
"""

ERROR_RSYNC_FUNCTION = """
echo "Rsync failed"
"""
