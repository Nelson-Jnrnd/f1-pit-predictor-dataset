import { it,expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
const b=JSON.parse(readFileSync('public/development.json','utf8'));
const registry=JSON.parse(readFileSync('ASSETS.json','utf8'));
it('bundles every released driver portrait with recorded PNG bytes and credits',()=>{
 for(const driver of b.drivers){
  const name=driver.code+'.png',entry=registry.find((x:any)=>x.file===name);
  expect(entry,name).toBeTruthy();
  const png=readFileSync('public/assets/'+name);
  expect(png.subarray(0,8).toString('hex')).toBe('89504e470d0a1a0a');
  expect(png.readUInt32BE(16)).toBeGreaterThan(0);
  expect(png.readUInt32BE(20)).toBeGreaterThan(0);
  expect(createHash('sha256').update(png).digest('hex')).toBe(entry.sha256);
  expect(entry.source).toContain('ae3485d695f07137f6778e03c3437ca1464fb7df');
 }
});
it('retains unsupported early forecasts rather than replacing them with invented probabilities',()=>{
 for(const driver of b.drivers){
  const attempts=b.attempts.filter((a:any)=>a.driver===driver.id);
  expect(attempts.find((a:any)=>a.state==='ok').lap).toBe(33);
  for(const a of attempts.filter((a:any)=>a.lap<33)){
   expect(a.state).toBe('failed'); expect(a.p).toBeUndefined();expect(a.reason).toBeTruthy();
  }
 }
});
