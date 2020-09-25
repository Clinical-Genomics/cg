import datetime as dt

import click
from cg.store import Store, models
from ruamel import yaml

COMMENT = f"{dt.datetime.now().date()}: Imported from MicrobialSample/PG"


def dict_print(dict_):
    for key in sorted(dict_):
        print(f"{key}: {dict_.get(key)}")


@click.command("merge-microbial-data")
@click.option("-c", "--config-file", type=click.File())
def create_microbial_cases(config_file):
    """One-time script to create cases for all microbial samples"""
    config = yaml.safe_load(config_file)
    store = Store(config["database"])

    # fix samples without sample id
    ids = {"data_analysis": "microbial"}
    microbial_samples = store.samples_by_ids(**ids).all()

    for microbial_sample in microbial_samples:

        if microbial_sample.ticket_number:
            continue

        click.echo(click.style("processing sample without ticket: " + microbial_sample.__str__(),
                               fg="white"))

        if microbial_sample.order == "Mikro v. 39 2019":
            microbial_sample.ticket_number = 712035
        elif microbial_sample.order == "Mikro v.41 2019":
            microbial_sample.ticket_number = 859941
        elif microbial_sample.order == "Mikro v. 41 2019":
            microbial_sample.ticket_number = 290386
        elif microbial_sample.order == "2019mikrovecka47":
            microbial_sample.ticket_number = 978844
        elif microbial_sample.order == "Mikro v.51 2019":
            microbial_sample.ticket_number = 712083

        if not microbial_sample.ticket_number:
            click.echo(click.style("failed to determine ticket for: " + microbial_sample.__str__(),
                                   fg="red"))
            return

        click.echo(click.style("changed ticket to: " + str(microbial_sample.ticket_number),
                               fg="green"))

    store.commit()

    for microbial_sample in microbial_samples:

        click.echo(click.style("processing sample: " + microbial_sample.__str__(), fg="white"))

        ticket = microbial_sample.ticket_number
        if not ticket:
            click.echo(click.style("stopping on sample without ticket: " +
                                   microbial_sample.__str__(),
                                   fg="red"))
            return

        existing_case = store.find_family(customer=microbial_sample.customer, name=ticket)
        if existing_case:
            click.echo(click.style("skipping processed sample: " + microbial_sample.__str__(),
                                   fg="yellow"))
            continue

        ids = {"ticket_number": ticket}
        ticket_samples = store.samples_by_ids(**ids).all()
        case = store.add_family(name=ticket, panels=None, priority=microbial_sample.priority_human)
        case.customer_id = microbial_sample.customer_id

        click.echo(click.style("created case: " + case.__str__(), fg="green"))

        for ticket_sample in ticket_samples:
            click.echo(click.style("relating sample: " + ticket_sample.__str__(), fg="green"))
            store.relate_sample(family=case, sample=ticket_sample, status="unknown")

        click.echo(click.style("saving case: " + case.__str__(), fg="white"))
        store.add_commit(case)


if __name__ == "__main__":
    create_microbial_cases()
