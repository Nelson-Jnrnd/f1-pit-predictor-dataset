import { it, expect } from 'vitest';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { resolve, join } from 'node:path';
import { createHash } from 'node:crypto';

it('preserves release bytes under a Windows-style Git checkout', () => {
  const root = resolve('..'), destination = mkdtempSync(join(tmpdir(), 'replay-checkout-'));
  const paths = ['explorer/public/development.json', 'explorer/public/release.json',
    'explorer/public/positions.json', 'explorer/public/positions-release.json',
    'explorer/public/synthetic.json', 'research/position-evidence/candidate.json'];
  try {
    // A separate index keeps this test from changing or locking the developer index.
    const env = { ...process.env, GIT_INDEX_FILE: join(destination, 'index') };
    execFileSync('git', ['read-tree', 'HEAD'], { cwd: root, env });
    const prefix = destination.replaceAll('\\', '/') + '/';
    execFileSync('git', ['-c', 'core.autocrlf=true', '-c', 'core.eol=crlf',
      'checkout-index', '--prefix=' + prefix, '--', ...paths], { cwd: root, env });
    for (const path of paths) {
      const blob = execFileSync('git', ['show', 'HEAD:' + path], { cwd: root, maxBuffer: 32 * 1024 * 1024 });
      expect(readFileSync(join(destination, path)).equals(blob), path).toBe(true);
    }
    const hash = (path: string) => createHash('sha256').update(readFileSync(join(destination, path))).digest('hex');
    const release = JSON.parse(readFileSync(join(destination, paths[1]), 'utf8'));
    const positions = JSON.parse(readFileSync(join(destination, paths[3]), 'utf8'));
    expect(hash(paths[0])).toBe(release.sha256);
    expect(hash(paths[2])).toBe(positions.sha256);
    expect(hash(paths[0])).toBe(positions.baseBundleSha256);
  } finally {
    rmSync(destination, { recursive: true, force: true });
  }
});
