"""Liquipedia scraper for osu! World Cup mappools.

Phase 1 scope: OWC only. Output is JSON per (edition, round) under
`data/layerA/liquipedia/osu_world_cup/<edition>/<round>.json`, plus a top-level
`data/layerA/liquipedia/index.json` manifest.

Reads only Liquipedia's MediaWiki API (no HTML scraping). Rate-limited per
Liquipedia ToS: one `parse` request per 30 s, one `query` request per 2 s.
Custom User-Agent identifying the project + contact email is mandatory and
configured via `Settings.liquipedia_user_agent`.

Layer A pattern note: README §12 prescribes one MySQL schema per source.
Liquipedia is wiki text, not a SQL dump — for v1 the sink is a JSON file
cache. Re-import into MySQL / Postgres is a later phase once the schema
stabilises across editions.
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import httpx
import mwparserfromhell

from ..config import Settings
from .liquipedia_parsers import MapEntry, parse_round_wikitext

log = logging.getLogger(__name__)

API_URL = "https://liquipedia.net/osu/api.php"
PAGE_BASE = "https://liquipedia.net/osu/"

OWC_ORDINAL_EDITIONS = ("1", "2", "3")
OWC_FIRST_YEAR_EDITION = 2013

MAPPOOL_SECTION_HEADINGS = {"mappool", "map pool", "maps", "map sets"}


@dataclass
class FetchResult:
    title: str
    wikitext: str
    revision_id: int | None
    source_url: str


class LiquipediaClient:
    """MediaWiki API client with on-disk cache and ToS-compliant rate limiting."""

    def __init__(self, settings: Settings, *, refresh_cache: bool = False) -> None:
        self.settings = settings
        self.refresh_cache = refresh_cache
        self.cache_dir = Path(settings.liquipedia_cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._last_parse_at = 0.0
        self._client = httpx.Client(
            headers={"User-Agent": settings.liquipedia_user_agent},
            timeout=30.0,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "LiquipediaClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def _wait_for_parse_slot(self) -> None:
        elapsed = time.monotonic() - self._last_parse_at
        wait = self.settings.liquipedia_min_request_interval_s - elapsed
        if wait > 0:
            log.info("Rate limiting: sleeping %.1fs before next parse call.", wait)
            time.sleep(wait)

    def _cache_path(self, page_title: str) -> Path:
        safe = re.sub(r"[^A-Za-z0-9._/-]", "_", page_title).replace("/", "__")
        return self.cache_dir / f"{safe}.json"

    def fetch_wikitext(self, page_title: str) -> FetchResult | None:
        """Fetch parsed wikitext for a page. Returns None on 404. Cached."""
        cache_path = self._cache_path(page_title)
        if cache_path.exists() and not self.refresh_cache:
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
            return FetchResult(
                title=payload["title"],
                wikitext=payload["wikitext"],
                revision_id=payload.get("revision_id"),
                source_url=payload["source_url"],
            )

        self._wait_for_parse_slot()
        params = {
            "action": "parse",
            "format": "json",
            "page": page_title,
            "prop": "wikitext|revid",
            "redirects": 1,
        }
        for attempt in range(3):
            try:
                resp = self._client.get(API_URL, params=params)
                self._last_parse_at = time.monotonic()
                if resp.status_code == 404:
                    return None
                resp.raise_for_status()
                data = resp.json()
            except (httpx.HTTPError, json.JSONDecodeError) as exc:
                log.warning("Liquipedia fetch failed for %s (attempt %d): %s",
                            page_title, attempt + 1, exc)
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)
                continue
            break

        if "error" in data:
            code = data["error"].get("code")
            if code in {"missingtitle", "invalidtitle"}:
                return None
            raise RuntimeError(f"Liquipedia API error for {page_title}: {data['error']}")

        parsed = data["parse"]
        result = FetchResult(
            title=parsed["title"],
            wikitext=parsed["wikitext"]["*"],
            revision_id=parsed.get("revid"),
            source_url=PAGE_BASE + page_title.replace(" ", "_"),
        )
        cache_path.write_text(
            json.dumps(
                {
                    "title": result.title,
                    "wikitext": result.wikitext,
                    "revision_id": result.revision_id,
                    "source_url": result.source_url,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return result


def iter_owc_editions(through_year: int) -> Iterable[str]:
    """Yield OWC edition page slugs in chronological order."""
    for ordinal in OWC_ORDINAL_EDITIONS:
        yield f"Osu_World_Cup/{ordinal}"
    for year in range(OWC_FIRST_YEAR_EDITION, through_year + 1):
        yield f"Osu_World_Cup/{year}"


def _find_mappool_section(wikitext: str):
    """Return the level-2 Mappool section's parsed mwparserfromhell node, or None."""
    code = mwparserfromhell.parse(wikitext)
    sections = code.get_sections(levels=[2], include_lead=False)
    for section in sections:
        headings = section.filter_headings()
        if not headings:
            continue
        title = str(headings[0].title).strip().lower()
        if title in MAPPOOL_SECTION_HEADINGS:
            return section
    return None


def _split_into_rounds(mappool_section) -> list[tuple[str, str]]:
    """Split a Mappool section into (round_name, round_wikitext) pairs.

    Round headings are level-3 inside the level-2 Mappool section. If no
    level-3 headings exist (some older editions or qualifier-only pages),
    the entire section is returned under a single "Mappool" round.
    """
    rounds: list[tuple[str, str]] = []
    sub_sections = mappool_section.get_sections(levels=[3], include_lead=False)
    if not sub_sections:
        return [("Mappool", str(mappool_section))]
    for sub in sub_sections:
        headings = sub.filter_headings()
        if not headings:
            continue
        round_name = str(headings[0].title).strip()
        body = str(sub).split(str(headings[0]), 1)[-1]
        rounds.append((round_name, body))
    return rounds


def _round_filename(round_name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", round_name.lower()).strip("_") or "round"


def _edition_dir(slug: str, output_dir: Path) -> Path:
    edition_part = slug.split("/", 1)[1].lower()
    return output_dir / "osu_world_cup" / edition_part


def scrape_edition(
    client: LiquipediaClient,
    slug: str,
    *,
    output_dir: Path,
    include_qualifier: bool,
    dry_run: bool,
) -> dict:
    """Scrape one OWC edition (main page + optional Qualifier subpage).

    Returns a manifest entry summarising what was scraped.
    """
    manifest: dict = {"slug": slug, "rounds": [], "warnings": []}
    main = client.fetch_wikitext(slug)
    if main is None:
        manifest["warnings"].append("main_page_404")
        log.warning("OWC edition page missing on Liquipedia: %s", slug)
        return manifest

    sources: list[tuple[str, FetchResult]] = [(slug, main)]
    if include_qualifier:
        qual_slug = f"{slug}/Qualifier"
        qual = client.fetch_wikitext(qual_slug)
        if qual is not None:
            sources.append((qual_slug, qual))
        else:
            log.info("No Qualifier subpage for %s.", slug)

    edition_dir = _edition_dir(slug, output_dir)
    if not dry_run:
        edition_dir.mkdir(parents=True, exist_ok=True)

    tournament_label = slug.replace("_", " ").replace("/", " #") \
        if slug.split("/", 1)[1] in OWC_ORDINAL_EDITIONS \
        else slug.replace("Osu_World_Cup/", "osu! World Cup ")

    for src_slug, fetched in sources:
        section = _find_mappool_section(fetched.wikitext)
        if section is None:
            manifest["warnings"].append(f"no_mappool_section:{src_slug}")
            log.warning("No Mappool section found in %s.", src_slug)
            continue
        rounds = _split_into_rounds(section)
        for round_name, round_text in rounds:
            entries = parse_round_wikitext(
                round_text,
                tournament=tournament_label,
                tournament_slug=src_slug,
                round_name=round_name,
                source_url=fetched.source_url,
                source_revision=fetched.revision_id,
            )
            if not entries:
                continue
            file_stem = f"{_round_filename(src_slug.split('/')[-1])}__{_round_filename(round_name)}" \
                if src_slug.endswith("/Qualifier") \
                else _round_filename(round_name)
            out_path = edition_dir / f"{file_stem}.json"
            payload = {
                "tournament": tournament_label,
                "tournament_slug": src_slug,
                "source_url": fetched.source_url,
                "source_revision": fetched.revision_id,
                "round": round_name,
                "entries": [e.to_dict() for e in entries],
            }
            if not dry_run:
                out_path.write_text(
                    json.dumps(payload, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            warning_count = sum(1 for e in entries if e.slot == "UNKNOWN")
            manifest["rounds"].append({
                "source_slug": src_slug,
                "round": round_name,
                "entries": len(entries),
                "warnings": warning_count,
                "file": str(out_path.relative_to(output_dir)) if not dry_run else None,
            })

    return manifest


def scrape_owc(
    *,
    settings: Settings | None = None,
    year: int | None = None,
    include_qualifier: bool = True,
    refresh_cache: bool = False,
    dry_run: bool = False,
    through_year: int = 2025,
) -> dict:
    """Top-level OWC scrape entrypoint.

    Args:
        year: if set, scrape only that single edition. Special values:
              `1`, `2`, `3` for the ordinal editions (2011-2012).
        include_qualifier: also probe the `<edition>/Qualifier` subpage.
        refresh_cache: bypass the on-disk cache.
        dry_run: log what would be written but do not write JSON files.
        through_year: stop at this year (inclusive) when scanning all editions.

    Returns the run manifest (also written to `index.json` unless `dry_run`).
    """
    settings = settings or Settings()
    output_dir = Path(settings.liquipedia_output_dir)
    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)

    if year is not None:
        slugs = [f"Osu_World_Cup/{year}"]
    else:
        slugs = list(iter_owc_editions(through_year))

    manifest: dict = {
        "tool": "all-of-osu layerA liquipedia owc",
        "include_qualifier": include_qualifier,
        "dry_run": dry_run,
        "editions": [],
    }
    with LiquipediaClient(settings, refresh_cache=refresh_cache) as client:
        for slug in slugs:
            log.info("Scraping %s ...", slug)
            edition_manifest = scrape_edition(
                client,
                slug,
                output_dir=output_dir,
                include_qualifier=include_qualifier,
                dry_run=dry_run,
            )
            manifest["editions"].append(edition_manifest)

    if not dry_run:
        (output_dir / "index.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return manifest
