-- Public tile icons; files stay in Storage, outside the repo.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('game-icons', 'game-icons', true, 262144, array['image/png']);

create policy game_icons_admin_select on storage.objects
for select to authenticated
using (bucket_id = 'game-icons' and (select workspace_private.is_admin()));

create policy game_icons_admin_insert on storage.objects
for insert to authenticated
with check (bucket_id = 'game-icons' and name ~ '^[a-z0-9][a-z0-9-]{0,63}\.png$'
  and (select workspace_private.is_admin()));

create policy game_icons_admin_update on storage.objects
for update to authenticated
using (bucket_id = 'game-icons' and (select workspace_private.is_admin()))
with check (bucket_id = 'game-icons' and name ~ '^[a-z0-9][a-z0-9-]{0,63}\.png$'
  and (select workspace_private.is_admin()));

create policy game_icons_admin_delete on storage.objects
for delete to authenticated
using (bucket_id = 'game-icons' and (select workspace_private.is_admin()));
