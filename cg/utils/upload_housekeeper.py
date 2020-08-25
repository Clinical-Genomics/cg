import json
from pathlib import Path
import datetime as dt
from ruamel import yaml
import shutil
import click

from cg.store import Store, models
from cg.apps.hk import HousekeeperAPI
from housekeeper.store import models as hkmodels


@click.command("upload-old-cases")
@click.option("--report-dir", help="Path where housekeeper reports were stored")
@click.option("--case-dir", help="Path where all cancer cases are stored")
@click.pass_context
def upload_cases(context, report_dir, case_dir):
    """One-time script to upload all BALSAMIC output files to Housekeeper and StatusDB"""
    store_api = Store(context.obj["database"])
    housekeeper_api = HousekeeperAPI(context.obj)

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
        if not items:
            continue
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
                print(f"{case_id} already stored, re-storing!!")
                version_obj = (
                    housekeeper_api.Version.query.join(hkmodels.Bundle)
                    .filter(
                        hkmodels.Version.created_at
                        == dt.datetime.strptime(
                            config_data["analysis"]["config_creation_date"], "%Y-%m-%d %H:%M"
                        )
                    )
                    .filter(hkmodels.Bundle.name == case_id)
                    .first()
                )
                shutil.rmtree(version_obj.full_path, ignore_errors=True)
                version_obj.delete()
                housekeeper_api.commit()
                bundle_result = housekeeper_api.add_bundle(bundle_data=bundle_data)
                continue
            bundle_object, bundle_version = bundle_result
            housekeeper_api.include(bundle_version)
            housekeeper_api.add_commit(bundle_object, bundle_version)
            print(
                f"Analysis successfully stored in Housekeeper: {case_id} : {bundle_version.created_at}"
            )

        except FileExistsError:
            # If files exist but no bundle, clean up path and try again
            housekeeper_api.rollback()
            print("Files found for non-existing bundle, cleaning up!")
            shutil.rmtree(bundle_version.full_path, ignore_errors=True)
            housekeeper_api.include(bundle_version)
            housekeeper_api.add_commit(bundle_object, bundle_version)

        except PermissionError:
            housekeeper_api.rollback()
            print(f"No permission to link files for {case_id}, skipping")
            continue

        finally:
            # Add bundle to StatusDB
            case_object = store_api.family(case_id)
            analysis_start = dt.datetime.strptime(
                config_data["analysis"]["config_creation_date"], "%Y-%m-%d %H:%M"
            )
            analysis = (
                store_api.Analysis.query.join(models.Family)
                .filter(models.Family.internal_id == case_object.internal_id)
                .filter(models.Analysis.started_at == analysis_start)
                .first()
            )
            if analysis:
                print(
                    f"Analysis already stored in ClinicalDB: {case_id} : {analysis_start}, skipping Status"
                )
            else:
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
