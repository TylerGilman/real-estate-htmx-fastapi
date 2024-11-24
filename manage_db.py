import click
from app.core.database import init_db, reset_db


@click.group()
def cli():
    """Database management commands"""
    pass


@cli.command()
def init():
    """Initialize the database and create tables"""
    click.echo("Initializing database...")
    init_db()
    click.echo("Database initialized successfully!")


@cli.command()
def reset():
    """Reset the database (drop all tables and recreate)"""
    if click.confirm(
        "Are you sure you want to reset the database? This will delete all data!"
    ):
        click.echo("Resetting database...")
        reset_db()
        click.echo("Database reset successfully!")


if __name__ == "__main__":
    cli()
