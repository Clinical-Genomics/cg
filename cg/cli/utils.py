import click


def echo_lines(lines: list[str]) -> None:
    for line in lines:
        click.echo(line)
