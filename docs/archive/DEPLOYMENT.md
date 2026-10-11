# Public deployment

The application already runs locally. Deployment gives other people a stable public URL;
it is not required to inspect the financials, stress tests or exported memos.

## Three services, three purposes

| Service | Purpose | Required user action |
|---|---|---|
| GitHub | Stores the application source and runs CI | Log in to the intended account; authorize this repository's push. |
| Streamlit Community Cloud | Runs the Python app behind a public URL | Log in and authorize repository access. |
| Managed PostgreSQL, e.g. Supabase | Retains public analyses/memos after hosted restarts | Create/use a database account; provision an isolated app database. |

Codex handles the engineering setup. The user completes login, account terms and any
required authorization. Neither the viewer nor an app visitor needs a DeepSeek account.
The source repository must never contain server secrets.

## Prepared configuration

- Repository entrypoint: `app.py`; Python **3.11**.
- Dependencies: `requirements.txt`, pinned from the tested Python 3.11 environment.
- Server settings: `.streamlit/config.toml`; keep Community Cloud's server protections enabled.
- Server-only secrets: `SEC_USER_AGENT`, `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL`,
  `CACHE_DATABASE_URL`; optional `DEEPSEEK_BASE_URL`.
- PostgreSQL connection should require TLS (`sslmode=require`). For a free Supabase
  deployment, select a connection method reachable from the host; do not publish database
  credentials or grant browser clients direct access to cache tables.
- `MemoStore` creates its minimal tables using the server database role. Use an isolated
  database/schema or dedicated restricted role; no table browser permissions are needed.
- Local files/SQLite are development fallbacks and are **not** durable cloud persistence.

## Release sequence

1. Verify/commit the local application and acceptance evidence.
2. Obtain explicit GitHub synchronization authorization and authenticate.
3. Create/use the intended repository; push the approved commit and inspect actual CI results.
4. Provision PostgreSQL; configure TLS connection server-side; test cache/locks on the real database.
5. Deploy on Community Cloud using the repository, branch and `app.py`; enter secrets through
   its private configuration. User completes any expanded OAuth permissions/account terms.
6. Open the deployed URL in a separate unauthenticated session. Search a cold non-demo ticker,
   load financials, generate/reuse a memo and download a valid one-page PDF without viewer keys.
7. Restart the hosted app and verify that the saved public analysis/memo survives in PostgreSQL.
8. Verify shared request/concurrency limits and source-refresh behavior on the deployed instance.

Do not mark these complete from local tests. At the current checkpoint, no GitHub remote,
managed database, public URL or GitHub CI run has been verified.

Official guides: [Streamlit deployment](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app),
[Streamlit secrets](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management),
[Supabase database connections](https://supabase.com/docs/guides/database/connecting-to-postgres).
