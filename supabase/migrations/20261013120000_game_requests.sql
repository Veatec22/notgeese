-- Game requests from the site form. One row per submission; the admin panel groups them
-- by game_key (steam:<appid>, gog:<slug>, title:<normalized title>).
--
-- Writes only from the `game-request` Edge Function (admin client). The admin account
-- reads and deletes via RLS; anon has no access.

create table public.game_requests (
  id bigint generated always as identity primary key,
  created_at timestamptz not null default now(),
  game_key text not null check (game_key ~ '^(steam:[0-9]{1,10}|gog:[a-z0-9_]{1,100}|title:.{1,200})$'),
  store text check (store in ('steam', 'gog')),
  title text not null check (char_length(title) between 1 and 200),
  url text check (url is null or char_length(url) <= 300),
  comment text check (comment is null or char_length(comment) <= 500),
  -- Store lists Polish; null = unknown (plain title or store lookup failed).
  polish boolean,
  -- HMAC of IP and UTC day; only for the daily limit.
  ip_hash text not null check (ip_hash ~ '^[0-9a-f]{32}$')
);
create index game_requests_created on public.game_requests (created_at);
create index game_requests_ip on public.game_requests (ip_hash, created_at);

alter table public.game_requests enable row level security;
revoke all on public.game_requests from anon, authenticated;
grant select, delete on public.game_requests to authenticated;

create policy game_requests_admin_read on public.game_requests
for select to authenticated using ((select workspace_private.is_admin()));

create policy game_requests_admin_delete on public.game_requests
for delete to authenticated using ((select workspace_private.is_admin()));
