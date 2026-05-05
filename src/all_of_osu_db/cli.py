import logging

import typer

app = typer.Typer(help="All-Of-Osu-DB CLI", no_args_is_help=True)

layerA_app = typer.Typer(help="Layer A source ingestion.", no_args_is_help=True)
app.add_typer(layerA_app, name="layerA")

liquipedia_app = typer.Typer(
    help="Liquipedia tournament mappool scraper.", no_args_is_help=True
)
layerA_app.add_typer(liquipedia_app, name="liquipedia")


etl_app = typer.Typer(help="Layer A → Layer B ETL.", no_args_is_help=True)
app.add_typer(etl_app, name="etl")


@etl_app.command("tournament-mappool")
def etl_tournament_mappool() -> None:
    """Project Layer A tournament_pick → Layer B tournament_mappool (Postgres)."""
    from .etl.tournament_mappool import run_etl

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    counts = run_etl()
    typer.echo(f"Projected {counts['projected']}, upserted {counts['upserted']}")


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


@liquipedia_app.command("export-csv")
def liquipedia_export_csv(
    output: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="CSV output path. Default: data/layerA/liquipedia/owc_mappool.csv",
    ),
    include_unknown: bool = typer.Option(
        False,
        "--include-unknown/--exclude-unknown",
        help="Include parser warning rows (slot=UNKNOWN). Default excluded.",
    ),
) -> None:
    """Flatten all scraped OWC mappool JSON into a single CSV."""
    from pathlib import Path
    from .layerA.liquipedia import export_owc_csv

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    out_path, n = export_owc_csv(
        output_path=Path(output) if output else None,
        include_unknown=include_unknown,
    )
    typer.echo(f"Wrote {n} rows to {out_path}")


@liquipedia_app.command("load-sqlite")
def liquipedia_load_sqlite(
    input_path: str | None = typer.Option(
        None, "--input", "-i",
        help="Verified CSV input (default: data/layerA/liquipedia/owc_mappool_verified.csv).",
    ),
    output_path: str | None = typer.Option(
        None, "--output", "-o",
        help="SQLite output path (default: data/layerA/liquipedia/liquipedia.sqlite).",
    ),
) -> None:
    """Load the verified Liquipedia CSV into the Layer A SQLite mirror."""
    from pathlib import Path
    from .layerA.liquipedia_load import load_to_sqlite

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    counts = load_to_sqlite(
        input_path=Path(input_path) if input_path else None,
        output_path=Path(output_path) if output_path else None,
    )
    typer.echo("SQLite tournament_pick row counts:")
    for k, v in sorted(counts.items()):
        typer.echo(f"  {k:10s} {v}")


@liquipedia_app.command("verify-mappool")
def liquipedia_verify_mappool(
    input_path: str | None = typer.Option(
        None, "--input", "-i",
        help="Input CSV (default: data/layerA/liquipedia/owc_mappool.csv).",
    ),
    output_path: str | None = typer.Option(
        None, "--output", "-o",
        help="Output verified CSV (default: data/layerA/liquipedia/owc_mappool_verified.csv).",
    ),
) -> None:
    """Verify scraped mappool beatmap_ids against the live osu! API v2."""
    from pathlib import Path
    from .layerA.verify_mappool import verify_mappool_csv

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    out, counts = verify_mappool_csv(
        input_path=Path(input_path) if input_path else None,
        output_path=Path(output_path) if output_path else None,
    )
    typer.echo(f"Wrote {out}")
    for status, n in sorted(counts.items()):
        typer.echo(f"  {status:10s} {n}")


if __name__ == "__main__":
    app()
