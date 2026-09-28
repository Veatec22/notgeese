// Save one game's drafts: POST { game, expected_revision, request_id, actions }.
import { withSupabase } from 'npm:@supabase/server@1.8.0';
import { errorResponse, jsonBody, saveGame } from '../_shared/workspace-server.ts';

export default {
  fetch: withSupabase({ auth: 'user' }, async (req, ctx) => {
    try {
      return Response.json(await saveGame(ctx.supabase, await jsonBody(req)));
    } catch (error) {
      return errorResponse(error);
    }
  }),
};
