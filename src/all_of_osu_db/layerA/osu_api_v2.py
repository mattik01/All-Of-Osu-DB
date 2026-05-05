"""osu! API v2 client (OAuth2 client-credentials, batched beatmap lookup).

Used for verifying scraped Liquipedia beatmap_ids against the live osu!
catalogue. The token is cached on disk and refreshed when expired; per-
beatmap responses are cached on disk so re-runs don't re-hit the API.

Public API:
    OsuApiV2Client(settings).get_beatmaps(ids) -> dict[int, dict | None]

Endpoint reference (osu! API v2):
    POST /oauth/token                        — client_credentials grant
    GET  /api/v2/beatmaps?ids[]=…&ids[]=…    — up to 50 ids per call
    GET  /api/v2/beatmaps/lookup?id=<id>     — single fallback (rarely needed)
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import httpx

from ..config import Settings

log = logging.getLogger(__name__)

BATCH_SIZE = 50
TOKEN_REFRESH_LEEWAY_S = 60


class OsuApiV2Error(RuntimeError):
    pass


class OsuApiV2Client:
    """Client-credentials OAuth2 client for osu! API v2.

    Token + per-beatmap responses are cached on disk under paths from
    `Settings`. `get_beatmaps()` returns a dict {id -> beatmap_dict or None}
    where None means the API returned 404 / didn't include the id.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        if not self.settings.osu_client_id or not self.settings.osu_client_secret:
            raise OsuApiV2Error(
                "OSU_CLIENT_ID / OSU_CLIENT_SECRET not set in .env. Register an "
                "OAuth client at https://osu.ppy.sh/home/account/edit#new-oauth-application"
            )
        self._client = httpx.Client(
            timeout=30.0,
            headers={"Accept": "application/json", "User-Agent": "All-Of-Osu-DB/0.1"},
        )
        self._token: str | None = None
        self._token_expires_at: float = 0.0
        Path(self.settings.osu_api_response_cache_dir).mkdir(parents=True, exist_ok=True)
        Path(self.settings.osu_api_token_cache).parent.mkdir(parents=True, exist_ok=True)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "OsuApiV2Client":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def _load_cached_token(self) -> None:
        path = Path(self.settings.osu_api_token_cache)
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            self._token = data.get("access_token")
            self._token_expires_at = float(data.get("expires_at", 0))
        except Exception:
            self._token = None
            self._token_expires_at = 0.0

    def _save_cached_token(self) -> None:
        Path(self.settings.osu_api_token_cache).write_text(
            json.dumps(
                {"access_token": self._token, "expires_at": self._token_expires_at}
            ),
            encoding="utf-8",
        )

    def _ensure_token(self) -> str:
        if self._token is None:
            self._load_cached_token()
        if self._token and self._token_expires_at - time.time() > TOKEN_REFRESH_LEEWAY_S:
            return self._token
        log.info("Fetching new osu! API v2 access token.")
        resp = self._client.post(
            self.settings.osu_api_token_url,
            data={
                "client_id": self.settings.osu_client_id,
                "client_secret": self.settings.osu_client_secret,
                "grant_type": "client_credentials",
                "scope": "public",
            },
        )
        resp.raise_for_status()
        body = resp.json()
        self._token = body["access_token"]
        self._token_expires_at = time.time() + int(body["expires_in"])
        self._save_cached_token()
        return self._token

    def _cache_path(self, beatmap_id: int) -> Path:
        return Path(self.settings.osu_api_response_cache_dir) / f"{beatmap_id}.json"

    def _read_cache(self, beatmap_id: int) -> dict | None | object:
        """Returns dict (cached hit), None (cached miss), or sentinel if not cached.

        Cached miss is encoded as `{"_missing": true}` so we don't re-query
        beatmap_ids that the API confirmed don't exist.
        """
        path = self._cache_path(beatmap_id)
        if not path.exists():
            return _NOT_CACHED
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("_missing"):
            return None
        return data

    def _write_cache(self, beatmap_id: int, payload: dict | None) -> None:
        path = self._cache_path(beatmap_id)
        if payload is None:
            path.write_text(json.dumps({"_missing": True}), encoding="utf-8")
        else:
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def get_beatmaps(self, ids: list[int]) -> dict[int, dict | None]:
        """Look up many beatmap_ids. Returns {id -> dict | None}.

        Uses the on-disk cache for ids already fetched (including confirmed
        misses). Unknown ids are fetched in batches of 50 via /beatmaps.
        """
        result: dict[int, dict | None] = {}
        to_fetch: list[int] = []
        for bid in ids:
            cached = self._read_cache(bid)
            if cached is _NOT_CACHED:
                to_fetch.append(bid)
            else:
                result[bid] = cached  # type: ignore[assignment]

        if not to_fetch:
            return result

        token = self._ensure_token()
        headers = {"Authorization": f"Bearer {token}"}
        unique_to_fetch = list(dict.fromkeys(to_fetch))
        for i in range(0, len(unique_to_fetch), BATCH_SIZE):
            chunk = unique_to_fetch[i : i + BATCH_SIZE]
            params = [("ids[]", str(b)) for b in chunk]
            resp = self._client.get(
                f"{self.settings.osu_api_base}/beatmaps",
                params=params,
                headers=headers,
            )
            if resp.status_code == 401:
                self._token = None
                token = self._ensure_token()
                headers = {"Authorization": f"Bearer {token}"}
                resp = self._client.get(
                    f"{self.settings.osu_api_base}/beatmaps",
                    params=params,
                    headers=headers,
                )
            resp.raise_for_status()
            payload = resp.json()
            returned = {bm["id"]: bm for bm in payload.get("beatmaps", [])}
            for bid in chunk:
                bm = returned.get(bid)
                self._write_cache(bid, bm)
                result[bid] = bm
            log.info(
                "API batch %d/%d: requested %d, received %d",
                (i // BATCH_SIZE) + 1,
                (len(unique_to_fetch) + BATCH_SIZE - 1) // BATCH_SIZE,
                len(chunk),
                len(returned),
            )
        return result


_NOT_CACHED = object()
