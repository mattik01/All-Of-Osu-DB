import psycopg

from .config import Settings


def run_validate() -> None:
    s = Settings()
    with psycopg.connect(s.layer_b_url) as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM beatmap_reference;")
        total = cur.fetchone()[0]

        cur.execute(
            "SELECT mode, COUNT(*) FROM beatmap_reference GROUP BY mode ORDER BY mode;"
        )
        by_mode = cur.fetchall()

        cur.execute(
            "SELECT status, COUNT(*) FROM beatmap_reference GROUP BY status ORDER BY status;"
        )
        by_status = cur.fetchall()

        cur.execute(
            "SELECT COUNT(*) FROM beatmap_reference WHERE popularity_rank IS NULL;"
        )
        unranked = cur.fetchone()[0]

        cur.execute(
            "SELECT popularity_rank, artist, title, version, playcount "
            "FROM beatmap_reference WHERE mode = 0 "
            "ORDER BY popularity_rank LIMIT 5;"
        )
        top5 = cur.fetchall()

    print(f"Total rows:            {total:,}")
    print(f"By mode:               {by_mode}")
    print(f"By status:             {by_status}")
    print(f"Unranked (NULL rank):  {unranked}")
    print("Top 5 std by popularity_rank:")
    for rnk, artist, title, version, playcount in top5:
        print(f"  #{rnk:<4} {artist} - {title} [{version}] ({playcount:,} plays)")
