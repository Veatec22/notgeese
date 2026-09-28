-- Workspace migration tests: access, revision, idempotency, atomicity.
-- Uruchamia supabase/tests/run-local.sh (lokalny PostgreSQL, baza tymczasowa).
\set ON_ERROR_STOP on
\set admin '00000000-0000-0000-0000-00000000000a'
\set other '00000000-0000-0000-0000-00000000000b'

insert into auth.users values (:'admin', 'admin@example.test'), (:'other', 'other@example.test');
insert into public.workspace_admins values (:'admin');

create function pg_temp.as_user(uid text) returns void language plpgsql as $$
begin
  perform set_config('request.jwt.claim.sub', uid, true);
  execute 'set local role authenticated';
end $$;

-- 1. Admin: first open without changes, then a save.
begin;
select pg_temp.as_user(:'admin');
do $$
declare r jsonb;
begin
  assert public.workspace_is_admin(), 'administrator';
  r := public.workspace_apply('shotgun-cop-man', 0, repeat('a', 40), '[]', '[]', '[]');
  assert r = '{"ok": true, "revision": 0}'::jsonb, 'otwarcie bez zmian nie podbija rewizji: ' || r;
  r := public.workspace_apply('shotgun-cop-man', 0, repeat('a', 40),
    '[{"namespace":"","key":"mPlay","action":"accept","english":"Play","before":null,"after":"Graj","state":"accepted","missing":false},
      {"namespace":"","key":"mQuit","action":"correct","english":"Quit","before":"Wyjście","after":"Wyjdź  \n","state":"pending","missing":false}]',
    '[]',
    '[{"kind":"accept","namespace":"","key":"mPlay","detail":{}},{"kind":"correct","namespace":"","key":"mQuit","detail":{}}]',
    '11111111-1111-1111-1111-111111111111');
  assert r = '{"ok": true, "revision": 1}'::jsonb, 'zapis: ' || r;
  assert (select count(*) from public.workspace_work) = 2;
  assert (select after from public.workspace_work where key = 'mQuit') = E'Wyjdź  \n', 'tekst bez zmian';
  assert (select array_agg(kind order by id) from public.workspace_journal) = array['accept', 'correct'];
end $$;
commit;

-- 2. A repeated request returns the previous response and does not duplicate the journal.
begin;
select pg_temp.as_user(:'admin');
do $$
declare r jsonb;
begin
  r := public.workspace_apply('shotgun-cop-man', 0, repeat('a', 40), '[]', '[]',
    '[{"kind":"accept","namespace":"","key":"mPlay","detail":{}}]', '11111111-1111-1111-1111-111111111111');
  assert r = '{"ok": true, "revision": 1, "duplicate": true}'::jsonb, 'duplikat: ' || r;
  assert (select count(*) from public.workspace_journal) = 2;
end $$;
commit;

-- 3. A stale revision (second tab) changes nothing.
begin;
select pg_temp.as_user(:'admin');
do $$
declare r jsonb;
begin
  r := public.workspace_apply('shotgun-cop-man', 0, repeat('b', 40), '[]',
    '[{"namespace":"","key":"mPlay"}]', '[{"kind":"unset","namespace":"","key":"mPlay","detail":{}}]',
    '22222222-2222-2222-2222-222222222222');
  assert r = '{"ok": false, "reason": "revision", "revision": 1}'::jsonb, 'rewizja: ' || r;
  assert (select count(*) from public.workspace_work) = 2;
  assert (select main_sha from public.workspace_games) = repeat('a', 40);
  assert not exists (select 1 from public.workspace_requests where request_id = '22222222-2222-2222-2222-222222222222');
end $$;
commit;

-- 4. A bad row aborts the whole transaction: no partial write.
begin;
select pg_temp.as_user(:'admin');
do $$
begin
  begin
    perform public.workspace_apply('shotgun-cop-man', 1, repeat('c', 40),
      '[{"namespace":"","key":"mOk","action":"accept","english":"OK","before":null,"after":"OK","state":"accepted","missing":false},
        {"namespace":"","key":"mBad","action":"accept","english":"X","before":"nie wolno","after":"Y","state":"accepted","missing":false}]',
      '[{"namespace":"","key":"mPlay"}]', '[]');
    assert false, 'oczekiwano błędu ograniczenia';
  exception when check_violation then null;
  end;
  assert (select count(*) from public.workspace_work) = 2;
  assert (select revision from public.workspace_games) = 1;
end $$;
commit;

-- 5. Another signed-in account sees nothing and cannot save.
begin;
select pg_temp.as_user(:'other');
do $$
begin
  assert not public.workspace_is_admin(), 'obce konto nie jest administratorem';
  assert (select count(*) from public.workspace_work) = 0, 'RLS: obce konto';
  assert (select count(*) from public.workspace_journal) = 0;
  assert (select count(*) from public.workspace_games) = 0;
  begin
    perform public.workspace_apply('shotgun-cop-man', 1, null, '[]', '[]', '[]');
    assert false, 'oczekiwano odmowy';
  exception when insufficient_privilege then null;
  end;
end $$;
commit;

-- 6. The admin cannot write to tables bypassing the RPC.
begin;
select pg_temp.as_user(:'admin');
do $$
begin
  begin
    insert into public.workspace_work (game, key, action, english, after, state) values ('shotgun-cop-man', 'x', 'accept', '', '', 'accepted');
    assert false, 'oczekiwano odmowy zapisu';
  exception when insufficient_privilege then null;
  end;
  begin
    perform count(*) from public.workspace_admins;
    assert false, 'oczekiwano odmowy odczytu listy administratorów';
  exception when insufficient_privilege then null;
  end;
end $$;
commit;

-- 7. No session (anon): no read, no RPC.
begin;
set local role anon;
do $$
begin
  begin
    perform count(*) from public.workspace_work;
    assert false, 'anon: odczyt';
  exception when insufficient_privilege then null;
  end;
  begin
    perform public.workspace_apply('shotgun-cop-man', 1, null, '[]', '[]', '[]');
    assert false, 'anon: RPC';
  exception when insufficient_privilege then null;
  end;
  begin
    perform public.workspace_is_admin();
    assert false, 'anon: workspace_is_admin';
  exception when insufficient_privilege then null;
  end;
end $$;
commit;

-- 8. Authenticated without a user session (no sub) is refused too.
begin;
set local role authenticated;
do $$
begin
  assert (select count(*) from public.workspace_work) = 0;
  begin
    perform public.workspace_apply('shotgun-cop-man', 1, null, '[]', '[]', '[]');
    assert false, 'brak sub: RPC';
  exception when insufficient_privilege then null;
  end;
end $$;
commit;

\echo 'workspace.sql: wszystkie testy przeszły'
