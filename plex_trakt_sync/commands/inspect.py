import click


@click.command()
@click.argument('input')
def inspect(input):
    """
    Inspect details of an object
    """
