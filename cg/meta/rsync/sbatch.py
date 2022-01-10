"""Sbatch templates for the rsync function"""

RSYNC_COMMAND = """
rsync -rvLa {source_path} {destination_path}
"""

RSYNC_CONTENTS_COMMAND = """
rsync -rvLa {source_path}/ {destination_path}
"""

COVID_RSYNC = """
rsync -rvLa {source_path} {destination_path}
rsync -rvLa {covid_report_path} {covid_destination_path}
"""

ERROR_RSYNC_FUNCTION = """
echo "Rsync failed"
"""
