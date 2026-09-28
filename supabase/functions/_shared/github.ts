// Server-side repo reads only. Repo and branch are fixed; the client passes at most
// a game slug. Never writes to GitHub.

export const REPO = 'Veatec22/notgeese';
export const BRANCH = 'main';

export class GitHubError extends Error {
  constructor(message: string, public readonly retryAt: string | null = null) {
    super(message);
    this.name = 'GitHubError';
  }
}

function headers(token: string | undefined, accept: string): HeadersInit {
  return {
    Accept: accept,
    'User-Agent': 'notgeese-workspace',
    'X-GitHub-Api-Version': '2022-11-28',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

function rateLimit(response: Response): GitHubError | null {
  if (response.status !== 403 && response.status !== 429) return null;
  const reset = Number(response.headers.get('x-ratelimit-reset'));
  const retryAfter = Number(response.headers.get('retry-after'));
  const at = reset ? new Date(reset * 1000) : retryAfter ? new Date(Date.now() + retryAfter * 1000) : null;
  return new GitHubError('Limit zapytań GitHuba wyczerpany.', at?.toISOString() ?? null);
}

/** One SHA lookup per open/save/refresh; every file then comes from that SHA. */
export async function mainSha(token?: string): Promise<string> {
  const response = await fetch(`https://api.github.com/repos/${REPO}/commits/${BRANCH}`, {
    headers: headers(token, 'application/vnd.github.sha'),
  });
  const limited = rateLimit(response);
  if (limited) throw limited;
  if (!response.ok) throw new GitHubError(`GitHub: nie udało się ustalić SHA ${BRANCH} (${response.status}).`);
  const sha = (await response.text()).trim();
  if (!/^[0-9a-f]{40}$/.test(sha)) throw new GitHubError('GitHub: nieoczekiwana odpowiedź przy ustalaniu SHA.');
  return sha;
}

/** File from a given commit; null when absent. */
export async function readFile(sha: string, path: string, token?: string): Promise<string | null> {
  const response = await fetch(`https://raw.githubusercontent.com/${REPO}/${sha}/${path}`, {
    headers: token ? { Authorization: `Bearer ${token}`, 'User-Agent': 'notgeese-workspace' } : { 'User-Agent': 'notgeese-workspace' },
  });
  if (response.status === 404) {
    await response.body?.cancel();
    return null;
  }
  const limited = rateLimit(response);
  if (limited) throw limited;
  if (!response.ok) throw new GitHubError(`GitHub: nie udało się pobrać ${path} (${response.status}).`);
  return await response.text();
}
