// Public game request from the site form: POST { target, comment?, website? }.
// No login; writes with the admin client (table closed to anon), limited per hashed IP.
import { withSupabase } from 'npm:@supabase/server@1.8.0';
import { submitRequest } from '../_shared/game-request-server.ts';

const secret = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? Deno.env.get('SUPABASE_SECRET_KEYS') ?? '';

export default {
  fetch: withSupabase({ auth: 'none' }, async (req, ctx) => {
    try {
      if (req.method !== 'POST') return Response.json({ error: 'method', message: 'Użyj POST.' }, { status: 405 });
      if (!secret) throw new Error('game-request: no secret for the IP hash');
      let body: unknown;
      try {
        body = await req.json();
      } catch {
        body = null;
      }
      if (typeof body !== 'object' || body === null || Array.isArray(body)) {
        return Response.json({ error: 'bad_request', message: 'Treść żądania musi być obiektem JSON.' }, { status: 400 });
      }
      const ip = req.headers.get('x-forwarded-for')?.split(',')[0]?.trim() || req.headers.get('cf-connecting-ip') || 'unknown';
      const table = () => ctx.supabaseAdmin.from('game_requests');
      const reply = await submitRequest(body as Record<string, unknown>, ip, {
        secret,
        fetch,
        store: {
          async count(since, ipHash) {
            let query = table().select('id', { count: 'exact', head: true }).gte('created_at', since);
            if (ipHash) query = query.eq('ip_hash', ipHash);
            const { count, error } = await query;
            if (error) throw error;
            return count ?? 0;
          },
          async insert(row) {
            const { error } = await table().insert(row);
            if (error) throw error;
          },
        },
      });
      return Response.json(reply.body, { status: reply.status });
    } catch (error) {
      console.error(error);
      return Response.json({ error: 'internal', message: 'Nie udało się zapisać zgłoszenia. Spróbuj później.' }, { status: 500 });
    }
  }),
};
