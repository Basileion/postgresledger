# PostgresLedger

Published managed PostgreSQL pricing (DigitalOcean, Supabase, Neon, Render, PlanetScale, Aiven, Heroku), normalized to a monthly bill by RAM, storage and HA.

- Data: `scripts/mkdata.py` -> `data/vendors.json` (source URL + check date per provider; never invent numbers)
- Build: `python3 scripts/build.py` -> `dist/`, pushed to `gh-pages`.
