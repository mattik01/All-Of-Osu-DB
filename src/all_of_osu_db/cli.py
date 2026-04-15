import typer

app = typer.Typer(help="All-Of-Osu-DB CLI", no_args_is_help=True)


@app.command()
def etl() -> None:
    """Run Layer A → Layer B ETL for beatmap_reference."""
    from .etl import run_etl

    run_etl()


@app.command()
def validate() -> None:
    """Row-count and spot-check validation on Layer B."""
    from .validate import run_validate

    run_validate()


if __name__ == "__main__":
    app()
