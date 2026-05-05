import logging

import typer

app = typer.Typer(help="All-Of-Osu-DB CLI", no_args_is_help=True)

layerA_app = typer.Typer(help="Layer A source ingestion.", no_args_is_help=True)
app.add_typer(layerA_app, name="layerA")

liquipedia_app = typer.Typer(
    help="Liquipedia tournament mappool scraper.", no_args_is_help=True
)
layerA_app.add_typer(liquipedia_app, name="liquipedia")


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


@liquipedia_app.command("owc")
def liquipedia_owc(
    year: int | None = typer.Option(
        None,
        "--year",
        help="Scrape a single edition (e.g. 2023, or 1/2/3 for ordinal editions). "
             "Omit to scrape all editions.",
    ),
    include_qualifier: bool = typer.Option(
        True,
        "--include-qualifier/--no-qualifier",
        help="Also probe the <edition>/Qualifier subpage.",
    ),
    refresh_cache: bool = typer.Option(
        False,
        "--refresh-cache",
        help="Bypass the on-disk wikitext cache and re-fetch from Liquipedia.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Log what would be fetched/written without writing JSON output.",
    ),
    through_year: int = typer.Option(
        2025,
        "--through-year",
        help="When scraping all editions, stop at this year (inclusive).",
    ),
) -> None:
    """Scrape osu! World Cup mappool(s) from Liquipedia into Layer A JSON cache."""
    from .layerA.liquipedia import scrape_owc

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    manifest = scrape_owc(
        year=year,
        include_qualifier=include_qualifier,
        refresh_cache=refresh_cache,
        dry_run=dry_run,
        through_year=through_year,
    )
    total_rounds = sum(len(e["rounds"]) for e in manifest["editions"])
    total_entries = sum(
        r["entries"] for e in manifest["editions"] for r in e["rounds"]
    )
    typer.echo(
        f"Scraped {len(manifest['editions'])} edition(s), "
        f"{total_rounds} round(s), {total_entries} map entries."
    )


if __name__ == "__main__":
    app()
