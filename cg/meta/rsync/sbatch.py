"""Sbatch templates for the rsync function"""

RSYNC_COMMAND = """
rsync -avL {source_path} {destination_path}
"""

RSYNC_CONTENTS_COMMAND = """
rsync -avL {source_path}/ {destination_path}
"""

COVID_RSYNC = """
rsync -avL {source_path} {destination_path}
rsync -avL {covid_report_path} {covid_destination_path}
"""

ERROR_RSYNC_FUNCTION = """
echo "Rsync failed"
"""
