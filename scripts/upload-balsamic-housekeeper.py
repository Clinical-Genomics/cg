from pathlib import Path
import json
from cg.store import Store, models
from cg.apps.hk import HousekeeperAPI
import datetime as dt
from ruamel import yaml
import click


@click.command()
@click.option("--database", help="StatusDB address")
@click.option("--housekeeper-root", help="Housekeeper root path")
@click.option("--housekeeper-db", help="Housekeeper database address")
@click.option("--report-dir", help="Path where housekeeper reports were stored")
@click.option("--case-dir", help="Path where all cancer cases are stored")
def upload_cases(database, housekeeper_root, housekeeper_db, report_dir, case_dir):
    """One-time script to upload all BALSAMIC output files to Housekeeper and StatusDB"""
    store_api = Store(database)
    housekeeper_config = {"housekeeper": {"root": housekeeper_root, "database": housekeeper_db}}
    housekeeper_api = HousekeeperAPI(housekeeper_config)

    balsamic_families = (
        store_api.Family.query.outerjoin(models.Analysis)
        .join(models.Family.links, models.FamilySample.sample)
        .filter(models.Sample.data_analysis.ilike("%Balsamic%"))
    )
    fam_names = {x.internal_id: None for x in balsamic_families}
    for obj in Path(case_dir).iterdir():
        if obj.is_dir() and any(x in obj.name for x in fam_names):
            for obj2 in obj.iterdir():
                if obj2.as_posix().endswith(".json"):
                    config_dict = dict(json.load(open(obj2, "r")))
                    case_id = config_dict.get("analysis").get("case_id")
                    creation_date = config_dict.get("analysis").get("config_creation_date")
                    if creation_date:
                        creation_date = dt.datetime.strptime(creation_date, "%Y-%m-%d %H:%M")
                    if not case_id:
                        case_id = obj.name
                    case_id = case_id.split("_")[0]
                    if not Path(f"{case_dir}/{obj.name}/analysis/bam/tumor.merged.bam").is_file():
                        continue
                    if fam_names.get(case_id):
                        if fam_names.get(case_id).get("date") > creation_date:
                            continue
                    fam_names[case_id] = {
                        "bv": config_dict.get("analysis").get("BALSAMIC_version"),
                        "config_name": f"{case_dir}/{obj.name}/{obj2.name}",
                        "date": creation_date,
                        "path": obj.name,
                        "hk": Path(report_dir, obj.name + ".hk"),
                    }
    for case_id in fam_names:
        items = fam_names.get(case_id)
        if items:
            try:
                # Add files to Housekeeper
                config_data = dict(json.load(open(items["config_name"], "r")))
                bundle_data = {
                    "name": case_id,
                    "created": dt.datetime.strptime(
                        config_data["analysis"]["config_creation_date"], "%Y-%m-%d %H:%M"
                    ),
                    "version": config_data["analysis"]["BALSAMIC_version"],
                    "files": parse_deliverables_report(items["hk"]),
                }
                bundle_result = housekeeper_api.add_bundle(bundle_data=bundle_data)
                if not bundle_result:
                    print(f"{case_id} already stored!")
                    continue
                bundle_object, bundle_version = bundle_result
                housekeeper_api.include(bundle_version)
                housekeeper_api.add_commit(bundle_object, bundle_version)
                print(
                    f"Analysis successfully stored in Housekeeper: {case_id} : {bundle_version.created_at}"
                )
                # Add bundle to StatusDB
                case_object = store_api.family(case_id)
                analysis_start = dt.datetime.strptime(
                    config_data["analysis"]["config_creation_date"], "%Y-%m-%d %H:%M"
                )
                case_object.action = None
                new_analysis = store_api.add_analysis(
                    pipeline="balsamic",
                    version=config_data["analysis"]["BALSAMIC_version"],
                    started_at=analysis_start,
                    completed_at=dt.datetime.now(),
                    primary=(len(case_object.analyses) == 0),
                )
                new_analysis.family = case_object
                store_api.add_commit(new_analysis)
                print(f"Analysis successfully stored in ClinicalDB: {case_id} : {analysis_start}")
            except Exception as e:
                print(f"Error uploading {case_id}, {e}")
                housekeeper_api.rollback()
                store_api.rollback()
                continue


def parse_deliverables_report(report_path) -> list:
    """Parse BALSAMIC deliverables report, and return a list of files and their respective tags in bundle"""
    deliverables = dict(yaml.load(open(report_path)))["files"]
    deliverables = dict((k.replace("_", "-"), v) for k, v in deliverables.items() if v is not None)
    bundle_files = []
    for entry in deliverables:
        bundle_file = {
            "path": deliverables[entry][0],
            "tags": [entry],
            "archive": False,
        }
        bundle_files.append(bundle_file)
    return bundle_files


if __name__ == "__main__":
    upload_cases()
