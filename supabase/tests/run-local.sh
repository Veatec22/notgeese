#!/usr/bin/env bash
# Migration tests on a temporary local PostgreSQL (no Docker, no Supabase project).
# Usage: supabase/tests/run-local.sh   (needs initdb/pg_ctl in PATH or PG_BIN)
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
bin="${PG_BIN:-$(ls -d /usr/lib/postgresql/*/bin 2>/dev/null | sort -V | tail -1)}"
export PATH="$bin:$PATH"
tmp="$(mktemp -d)"
trap 'pg_ctl -D "$tmp/data" -m immediate stop >/dev/null 2>&1 || true; rm -rf "$tmp"' EXIT
initdb -D "$tmp/data" -U postgres --auth=trust >/dev/null
pg_ctl -D "$tmp/data" -o "-k $tmp -c listen_addresses=''" -l "$tmp/log" -w start >/dev/null
psql=(psql -h "$tmp" -U postgres -d postgres -v ON_ERROR_STOP=1 -q)
"${psql[@]}" -f "$here/local-auth-stub.sql"
for migration in "$here"/../migrations/*.sql; do "${psql[@]}" -f "$migration"; done
"${psql[@]}" -f "$here/workspace.sql"
