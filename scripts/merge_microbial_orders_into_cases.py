import json
from pathlib import Path
import datetime as dt
from ruamel import yaml
import shutil
import click

from cg.store import Store, models

COMMENT = f"{dt.datetime.now().date()}: Imported from MicrobialSample/PG"


def dict_print(dict_):
    for key in sorted(dict_):
        print(f"{key}: {dict_.get(key)}")


@click.command("merge-microbial-data")
@click.option("-c", "--config-file", type=click.File())
def merge_microbial_data(config_file):
    """One-time script to merge MicrobialSample into Sample and MicrobialOrder into Family"""
    config = yaml.safe_load(config_file)
    store = Store(config["database"])

    for order in models.MicrobialOrder.query.all():
        click.echo(click.style("processing order: " + order.__str__(), fg="yellow"))
        dict_print(order.__dict__)

        for ms in order.microbial_samples:

            click.echo(click.style("processing microbial sample: " + ms.__str__(), fg="yellow"))
            dict_print(ms.__dict__)

            if order.comment:
                sample_comment = f"Order comment: {order.comment}"

                if ms.comment:
                    sample_comment = f"{sample_comment}, sample comment: {ms.comment}"
            else:
                sample_comment = ms.comment

            sample_comment = COMMENT + "\n" + sample_comment if sample_comment else COMMENT

            data_analysis = "microbial|" + ms.data_analysis if ms.data_analysis else "microbial"

            sample = store.add_sample(
                name=ms.name,
                internal_id=ms.internal_id,
                comment=sample_comment,
                priority=ms.priority_human,
                data_analysis=data_analysis,
                customer=order.customer,
                ticket=order.ticket_number,
                sex="unknown",
                order=order.name,
            )

            sample.created_at = dt.datetime.now()
            sample.ordered_at = order.ordered_at
            sample.received_at = ms.received_at
            sample.prepared_at = ms.prepared_at
            sample.sequenced_at = ms.sequenced_at
            sample.delivered_at = ms.delivered_at
            sample.reads = ms.reads
            sample.invoice_id = ms.invoice_id
            sample.application_version_id = ms.application_version_id
            sample.customer_id = order.customer_id

            click.echo(click.style("Saving Sample: " + sample.__str__(), fg="yellow"))
            dict_print(sample.__dict__)
            store.add(sample)

            # find flowcells for the microbial sample
            flowcells = ms.flowcells
            click.echo(
                click.style(
                    "found flowcells for microbial sample: " + flowcells.__str__(), fg="yellow"
                )
            )

            # relate the new sample to the flowcell
            for flowcell in flowcells:
                click.echo(click.style(f"Appending Sample {sample} to FC {flowcell}", fg="green"))
                flowcell.samples.append(sample)
                click.echo(
                    click.style(f"Removing microbial sample {ms} from FC {flowcell}", fg="red")
                )
                flowcell.microbial_samples.remove(ms)

            click.echo(click.style("Deleting microbial sample: " + ms.__str__(), fg="red"))
            store.delete(ms)

        click.echo(click.style("Deleting microbial order: " + order.__str__(), fg="red"))
        store.delete(order)
        store.commit()


if __name__ == "__main__":
    merge_microbial_data()
