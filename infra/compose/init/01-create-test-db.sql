-- Runs only when the postgres_data volume is created fresh, so the
-- backend test suite can target a dedicated database. On an existing
-- volume, create it once by hand:
--   docker compose exec postgres createdb -U rinavi rinavi_test
CREATE DATABASE rinavi_test;
