import { it, expect, vi } from 'vitest';
import { createHash, webcrypto } from 'node:crypto';
import { readFileSync } from 'node:fs';
const fixture = JSON.parse(readFileSync(new URL('../public/development.json', import.meta.url), 'utf8'));
import synthetic from '../public/synthetic.json';
import { validate, latest, atTime, loadBundle } from '../src/model';
it('validates the released historical projection and retains full distributions and missing positions', () => {
  const b = validate(fixture);
  expect(b.drivers).toHaveLength(20);
  expect(b.attempts.filter(a => a.state === 'ok').length).toBeGreaterThan(0);
  for (const a of b.attempts.filter(a => a.state === 'ok')) {
    expect(a.p!.length).toBe(Math.max(1,a.scheduledDistance!-a.lap));
    expect(a.p!.reduce((s,p)=>s+p,0)+a.q!).toBeCloseTo(1,9);
  }
  expect(b.frames.every(f => f.rows.every(r => r.progress===null))).toBe(true);
  expect(b.frames.some(f=>new Set(f.rows.map(r=>r.completed)).size>1)).toBe(true);
});
it('refuses final races and fabricated coordinates before they can be shown', () => {
  const b = structuredClone(fixture);
  b.season = 2026;
  expect(()=>validate(b)).toThrow();
  b.season=2024; b.frames[0].rows[0].progress = .3 as never;
  expect(()=>validate(b)).toThrow();
});
it('same-prefix boundaries do not admit later tied attempts or frames', () => {
  const b = validate(fixture);
  const pair=b.frames.find((f,i) => b.frames[i+1]?.time===f.time);
  expect(pair).toBeTruthy();
  const later=b.frames.find(f=>f.time===pair!.time && f.order!>pair!.order!);
  expect(atTime(b,pair!.time,pair!.order)).toBe(pair);
  const laterAttempt=b.attempts.find(a=>a.time===later!.time && a.order===later!.order)!;
  expect(latest(b,laterAttempt.driver,pair!.time,pair!.order)?.id).not.toBe(laterAttempt.id);
});
it('selecting a subject at a fixed clock keeps its latest failure and labels its own lap', () => {
  const b=validate(fixture);
  const found=b.attempts.find(a=>a.state==='ok' && b.drivers.some(d=> {
    const other=latest(b,d.id,a.time,a.order);
    return other?.state==='failed' && other.time<a.time;
  }));
  expect(found).toBeTruthy();
  const failed=b.drivers.map(d=>latest(b,d.id,found!.time,found!.order)).find(a=>a?.state==='failed' && a.time<found!.time)!;
  expect(failed.p).toBeUndefined();
  expect(failed.time).toBeLessThan(found!.time);
  expect(atTime(b,found!.time,found!.order)?.rows).toHaveLength(20);
});
it('rejects download hash mismatches without substituting or repairing a bundle', async()=> {
  vi.stubGlobal('crypto',webcrypto);
  const raw=JSON.stringify(synthetic);
  const sha=createHash('sha256').update(raw).digest('hex');
  vi.stubGlobal('fetch',vi.fn((url:string)=>Promise.resolve({ok:true,json:()=>Promise.resolve({schema:1,file:'synthetic.json',sha256:sha}),text:()=>Promise.resolve(raw+' ')})));
  await expect(loadBundle('/')).rejects.toThrow('cannot be opened');
  vi.unstubAllGlobals();
});
