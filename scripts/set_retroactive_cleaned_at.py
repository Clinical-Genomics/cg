import click
import datetime as dt
import yaml
from pathlib import Path
from cg.store import Store, models


@click.command("update-cleaned-status")
@click.argument("config_path")
@click.pass_context
def set_analysis_status_cleaned_mip(config_path: str):
    """Updates all cleaned_at timestamps for mip cases"""

    config_dict = yaml.safe_load(open(config_path))
    case_dir = config_dict["mip-rd-dna"]["root"]
    status_db = Store(config_dict["database"])

    # Fetch all mip cases
    relevant_cases = status_db.query(models.Family).filter(
        models.Family.data_analysis.ilike("%mip%")
    )

    for case_obj in relevant_cases:
        # If there are no analyses, skip
        if not case_obj.analyses:
            continue
        # If path with case files exists, skip
        if Path(case_dir, case_obj.internal_id).exists():
            continue
        # Otherwise set all analyses cleaned_at timestamp to now
        click.echo(f"Setting {case_obj.internal_id} analyses to cleaned!")
        for analysis_obj in case_obj.analyses:
            analysis_obj.cleaned_at = dt.datetime.now()
            status_db.commit()
    click.echo("Update finished!")


if __name__ == "__main__":
    set_analysis_status_cleaned_mip(config_path)
