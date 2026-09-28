-- Workspace: review work, journal and revision control. Supabase holds no copy of
-- the games, only what results from the user's work.
--
-- Writes go only through public.workspace_apply (SECURITY DEFINER, one transaction).
-- The admin account reads tables via RLS; nobody writes to them directly.

create schema if not exists workspace_private;
revoke all on schema workspace_private from public;
grant usage on schema workspace_private to authenticated;

-- The only account with access. The row is added by hand in SQL after creating the account.
create table public.workspace_admins (
  user_id uuid primary key references auth.users (id) on delete cascade
);
alter table public.workspace_admins enable row level security;
revoke all on public.workspace_admins from anon, authenticated;

create function workspace_private.is_admin()
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (select 1 from public.workspace_admins where user_id = (select auth.uid()));
$$;
revoke all on function workspace_private.is_admin() from public, anon;
grant execute on function workspace_private.is_admin() to authenticated;

-- For Edge Functions: explicit account check before fetching a game.
create function public.workspace_is_admin()
returns boolean
language sql
stable
set search_path = ''
as $$
  select workspace_private.is_admin();
$$;
revoke all on function public.workspace_is_admin() from public, anon;
grant execute on function public.workspace_is_admin() to authenticated;

-- A game the user opened. Revision grows with every change to its work.
create table public.workspace_games (
  game text primary key check (game ~ '^[a-z0-9][a-z0-9-]{0,63}$'),
  revision bigint not null default 0,
  main_sha text check (main_sha ~ '^[0-9a-f]{40}$'),
  refreshed_at timestamptz
);

-- Review work for one entry. No row = "to review".
create table public.workspace_work (
  game text not null references public.workspace_games (game) on delete cascade,
  namespace text not null default '',
  key text not null check (key <> ''),
  action text not null check (action in ('accept', 'correct')),
  english text not null,
  before text,
  after text not null,
  state text not null check (state in ('accepted', 'review', 'pending', 'conflict')),
  missing boolean not null default false,
  updated_at timestamptz not null default now(),
  primary key (game, namespace, key),
  check ((action = 'accept') = (before is null)),
  check (action = 'correct' or state in ('accepted', 'review')),
  check (action = 'accept' or state in ('pending', 'conflict'))
);

create table public.workspace_journal (
  id bigint generated always as identity primary key,
  game text not null references public.workspace_games (game) on delete cascade,
  at timestamptz not null default now(),
  kind text not null check (kind in ('accept', 'correct', 'unset', 'forget', 'settle', 'missing', 'returned')),
  namespace text,
  key text,
  detail jsonb not null default '{}'::jsonb,
  request_id uuid
);
create index workspace_journal_game_id on public.workspace_journal (game, id desc);

-- Save responses by request id: a retry does not duplicate the journal.
create table public.workspace_requests (
  request_id uuid primary key,
  game text not null references public.workspace_games (game) on delete cascade,
  created_at timestamptz not null default now(),
  result jsonb not null
);

do $$
declare
  t text;
begin
  foreach t in array array['workspace_games', 'workspace_work', 'workspace_journal', 'workspace_requests'] loop
    execute format('alter table public.%I enable row level security', t);
    execute format('revoke all on public.%I from anon, authenticated', t);
    execute format('grant select on public.%I to authenticated', t);
    execute format(
      'create policy %I on public.%I for select to authenticated using ((select workspace_private.is_admin()))',
      t || '_admin_read', t
    );
  end loop;
end
$$;

-- One transaction per settle or save. The Edge Function prepares input with the
-- shared rules module; here only access control, revision check and atomic write.
-- Returns {ok, revision} or {ok: false, reason: 'revision', revision} without any change.
create function public.workspace_apply(
  p_game text,
  p_expected_revision bigint,
  p_main_sha text,
  p_upserts jsonb,
  p_deletes jsonb,
  p_journal jsonb,
  p_request_id uuid default null
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_revision bigint;
  v_previous jsonb;
  v_changed boolean;
  v_result jsonb;
begin
  if not workspace_private.is_admin() then
    raise exception 'workspace: brak uprawnień' using errcode = '42501';
  end if;
  if jsonb_typeof(p_upserts) <> 'array' or jsonb_typeof(p_deletes) <> 'array' or jsonb_typeof(p_journal) <> 'array' then
    raise exception 'workspace: upserts, deletes i journal muszą być tablicami' using errcode = '22023';
  end if;

  insert into public.workspace_games (game) values (p_game) on conflict (game) do nothing;
  select revision into v_revision from public.workspace_games where game = p_game for update;

  if p_request_id is not null then
    select result into v_previous from public.workspace_requests where request_id = p_request_id;
    if found then
      return v_previous || jsonb_build_object('duplicate', true);
    end if;
  end if;

  if v_revision <> p_expected_revision then
    return jsonb_build_object('ok', false, 'reason', 'revision', 'revision', v_revision);
  end if;

  delete from public.workspace_work w
  using jsonb_to_recordset(p_deletes) as d (namespace text, key text)
  where w.game = p_game and w.namespace = d.namespace and w.key = d.key;

  insert into public.workspace_work as w (game, namespace, key, action, english, before, after, state, missing, updated_at)
  select p_game, u.namespace, u.key, u.action, u.english, u.before, u.after, u.state, u.missing, now()
  from jsonb_to_recordset(p_upserts) as u (
    namespace text, key text, action text, english text, before text, after text, state text, missing boolean
  )
  on conflict (game, namespace, key) do update set
    action = excluded.action,
    english = excluded.english,
    before = excluded.before,
    after = excluded.after,
    state = excluded.state,
    missing = excluded.missing,
    updated_at = excluded.updated_at;

  insert into public.workspace_journal (game, kind, namespace, key, detail, request_id)
  select p_game, e.item ->> 'kind', e.item ->> 'namespace', e.item ->> 'key',
         coalesce(e.item -> 'detail', '{}'::jsonb), p_request_id
  from jsonb_array_elements(p_journal) with ordinality as e (item, n)
  order by e.n;

  v_changed := jsonb_array_length(p_upserts) + jsonb_array_length(p_deletes) > 0;
  update public.workspace_games
  set revision = revision + case when v_changed then 1 else 0 end,
      main_sha = coalesce(p_main_sha, main_sha),
      refreshed_at = now()
  where game = p_game
  returning revision into v_revision;

  v_result := jsonb_build_object('ok', true, 'revision', v_revision);
  if p_request_id is not null then
    insert into public.workspace_requests (request_id, game, result) values (p_request_id, p_game, v_result);
  end if;
  return v_result;
end;
$$;
revoke all on function public.workspace_apply(text, bigint, text, jsonb, jsonb, jsonb, uuid) from public, anon;
grant execute on function public.workspace_apply(text, bigint, text, jsonb, jsonb, jsonb, uuid) to authenticated;
