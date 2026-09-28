import { existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import type { Game } from './games';
import { withBase } from './url';

const publicDir = fileURLToPath(new URL('../../public/pobierz/', import.meta.url));

function humanSize(bytes: number | null): string | null {
  if (!bytes) return null;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(bytes < 10 * 1024 * 1024 ? 1 : 0)} MB`;
}

const published = (file: string | null): file is string => !!file && existsSync(publicDir + file);

/**
 * A package shows on the site only when the file really sits in public/pobierz,
 * so the site never promises a file that is not there.
 */
export function downloadFor(game: Game) {
  const { kind, file, bytes } = game.download;
  const size = humanSize(bytes);

  if ((kind === 'zip' || kind === 'patch') && published(file)) {
    return {
      available: true as const,
      href: withBase(`pobierz/${file}`),
      // Size and format live in the button; how to install is in the game README.
      meta: [size, 'ZIP'].filter(Boolean).join(' · '),
    };
  }

  if (kind === 'none') {
    return {
      available: false as const,
      href: null,
      label: 'Jeszcze nie ma paczki',
    };
  }

  return {
    available: false as const,
    href: null,
    label: 'Paczka w przygotowaniu',
  };
}
