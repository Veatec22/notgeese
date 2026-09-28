// Open or refresh a game in the workspace: POST { game }.
import { withSupabase } from 'npm:@supabase/server@1.8.0';
import { errorResponse, gameSlug, jsonBody, openGame } from '../_shared/workspace-server.ts';

export default {
  fetch: withSupabase({ auth: 'user' }, async (req, ctx) => {
    try {
      return Response.json(await openGame(ctx.supabase, gameSlug(await jsonBody(req))));
    } catch (error) {
      return errorResponse(error);
    }
  }),
};
