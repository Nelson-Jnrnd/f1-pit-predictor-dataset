import type { Bundle } from './model';
import { verifiedBundleHash } from './model';
export type PositionPoint = { driver: string; x: number; y: number };
export type PositionFrame = {
  time: number; order: number; boundaryPrefix: number;
  sample: null | { time: number; timestamp: string; publicationPrefix: number; sourceRef: string };
  points: PositionPoint[]; reason: string | null;
};
export type PositionBundle = {
  schema: number; kind: 'PositionContextBundle'; artifact_id: string;
  id: string; baseBundleId: string; baseBundleSha256: string;
  season: number; round: number; finalData: boolean;
  authorityRef: string; authorityStatus: 'APPROVED'; geometryRef: string;
  geometry: number[][]; clockStart: number; maxAge: number; availabilityBounds: number;
  frames: PositionFrame[]; policy: 'common-position-sample/v1';
};
export function validatePositions(value: unknown, base: Bundle, baseHash: string): PositionBundle {
  const fail = (): never => { throw Error('Track positions could not be loaded.'); };
  const p = value as PositionBundle;
  const finite = (n: unknown): n is number => typeof n === 'number' && Number.isFinite(n);
  const hash = (s: unknown) => typeof s === 'string' && /^[a-f0-9]{64}$/.test(s);
  if (!p || p.schema !== 1 || p.kind !== 'PositionContextBundle' ||
      p.season !== 2024 || p.round !== 11 || p.finalData !== false ||
      base.kind !== 'development' || base.season !== p.season || base.raceMetadata?.round !== p.round ||
      p.baseBundleId !== base.id || p.baseBundleSha256 !== baseHash || !hash(baseHash) ||
      p.id !== base.id + '-positions-v1' || p.authorityStatus !== 'APPROVED' ||
      ![p.artifact_id, p.authorityRef, p.geometryRef].every(hash) ||
      p.maxAge !== 20 || p.availabilityBounds !== 5 || !finite(p.clockStart) || p.clockStart < 0 ||
      p.policy !== 'common-position-sample/v1' || !Array.isArray(p.geometry) || p.geometry.length < 150 ||
      p.geometry.some(v => !Array.isArray(v) || v.length !== 2 || v.some(n => !finite(n) || n < 0 || n > 500)) ||
      !Array.isArray(p.frames) || p.frames.length !== base.frames.length) fail();
  const ids = new Set(base.drivers.map(d => d.id)), keys = new Set<string>();
  for (const f of p.frames) {
    const key = f.time + ':' + f.order;
    const original = base.frames.find(x => x.time === f.time && x.order === f.order);
    if (!original || keys.has(key) || !finite(f.boundaryPrefix) ||
        Math.abs(f.boundaryPrefix - f.time - p.clockStart) > 1e-6 || !Array.isArray(f.points) ||
        new Set(f.points.map(x => x.driver)).size !== f.points.length ||
        f.points.some(x => !ids.has(x.driver) || !finite(x.x) || !finite(x.y) || x.x < 0 || x.x > 500 || x.y < 0 || x.y > 500)) fail();
    keys.add(key);
    const attempts = base.attempts.filter(a => a.time === f.time && a.order === f.order);
    if (!attempts.length || attempts.some(a => a.boundaryAvailable === false) && (f.sample !== null || f.points.length !== 0)) fail();
    if (f.sample === null) {
      if (f.points.length || typeof f.reason !== 'string' || !f.reason) fail();
    } else {
      const s = f.sample;
      if (!s || !finite(s.time) || !finite(s.publicationPrefix) || s.publicationPrefix < 0 ||
          !(s.publicationPrefix + 5 < f.boundaryPrefix - 5) || s.time > f.time - 5 ||
          f.time + 5 - s.time > 20 ||
          typeof s.timestamp !== 'string' || !/Z$/.test(s.timestamp) || !Number.isFinite(Date.parse(s.timestamp)) ||
          typeof s.sourceRef !== 'string' || !/^[a-f0-9]{64}:\d+:\d+$/.test(s.sourceRef)) fail();
    }
  }
  return p;
}
export const positionAt = (bundle: PositionBundle | undefined, time: number, order: number) =>
  bundle?.frames.find(f => f.time === time && f.order === order);
export async function loadPositions(baseUrl: string, base: Bundle): Promise<PositionBundle | undefined> {
  const response = await fetch(baseUrl + 'positions-release.json');
  if (response.status === 404) return undefined;
  if (!response.ok) throw Error('Track positions could not be loaded.');
  const release = await response.json(), baseHash = verifiedBundleHash(base);
  if (release.schema !== 1 || release.file !== 'positions.json' || release.baseBundleSha256 !== baseHash ||
      typeof release.sha256 !== 'string' || !/^[a-f0-9]{64}$/.test(release.sha256) || !baseHash) throw Error('Track positions could not be loaded.');
  const download = await fetch(baseUrl + release.file);
  if (!download.ok) throw Error('Track positions could not be loaded.');
  const raw = await download.text();
  const digest = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(raw))))
    .map(x => x.toString(16).padStart(2, '0')).join('');
  if (digest !== release.sha256) throw Error('Track positions could not be loaded.');
  return validatePositions(JSON.parse(raw), base, baseHash);
}
