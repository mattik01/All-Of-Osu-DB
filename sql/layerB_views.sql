-- Layer B v1 views (README §8)

-- std (mode=0) ranked∪approved∪loved, ordered by popularity
CREATE OR REPLACE VIEW ranked_std_popular_v AS
SELECT *
FROM beatmap_reference
WHERE mode = 0
  AND status IN (1, 2, 4)
ORDER BY popularity_rank;

-- convenience single-row-by-md5 lookup shape
CREATE OR REPLACE VIEW by_md5_v AS
SELECT *
FROM beatmap_reference;
