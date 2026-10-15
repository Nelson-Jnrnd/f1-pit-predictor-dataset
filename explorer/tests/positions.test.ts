import { it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { validate } from '../src/model';
import { validatePositions, positionAt } from '../src/positions';
const raw=readFileSync(new URL('../public/development.json',import.meta.url),'utf8');
const base=validate(JSON.parse(raw)), sha=createHash('sha256').update(raw).digest('hex');
// Approval here is a test fixture only. Production release requires independent review.
const candidate=JSON.parse(readFileSync(new URL('../../research/position-evidence/candidate.json',import.meta.url),'utf8'));
function fixture(){return {...structuredClone(candidate),authorityStatus:'APPROVED'};}
it('joins every common sample to immutable boundaries and preserves lapped timing',()=>{
 const p=validatePositions(fixture(),base,sha);
 expect(p.frames).toHaveLength(base.frames.length);
 const f=p.frames.find(f=>f.points.length)!;
 expect(positionAt(p,f.time,f.order)).toBe(f);
 expect(base.frames.some(f=>new Set(f.rows.map(r=>r.completed)).size>1)).toBe(true);
 expect(p.frames.some(f=>!f.sample)).toBe(true);
});
it('rejects unapproved, mismatched, protected, future and stale exports',()=>{
 expect(()=>validatePositions(candidate,base,sha)).toThrow();
 for(const alter of [
  (p:any)=>p.baseBundleSha256='0'.repeat(64),
  (p:any)=>p.finalData=true,
  (p:any)=>p.geometry[0][0]=NaN,
  (p:any)=>p.frames.pop(),
  (p:any)=>{const f=p.frames.find((f:any)=>f.sample);f.sample.publicationPrefix=f.boundaryPrefix-10;},
  (p:any)=>{const f=p.frames.find((f:any)=>f.sample);f.sample.time=f.time-21;},
  (p:any)=>{const f=p.frames.find((f:any)=>f.sample);f.sample.time=f.time+1;},
  (p:any)=>{const f=p.frames.find((f:any)=>f.points.length);f.points.push(f.points[0]);},
 ]){const p=fixture();alter(p);expect(()=>validatePositions(p,base,sha)).toThrow();}
});
it('keeps unavailable and tied boundaries distinct',()=>{
 const p=fixture(),i=p.frames.findIndex((f:any,j:number)=>p.frames[j+1]?.time===f.time);
 expect(i).toBeGreaterThan(-1);
 p.frames[i].order=p.frames[i+1].order;
 expect(()=>validatePositions(p,base,sha)).toThrow();
 const q=fixture(),f=q.frames.find((f:any)=>!f.sample);
 f.points=[{driver:base.drivers[0].id,x:20,y:20}];
 expect(()=>validatePositions(q,base,sha)).toThrow();
});
