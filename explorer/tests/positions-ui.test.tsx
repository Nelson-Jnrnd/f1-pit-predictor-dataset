// @vitest-environment jsdom
import { render,screen,fireEvent,within,cleanup } from '@testing-library/react';
import { afterEach,it,expect,vi } from 'vitest';
import { readFileSync } from 'node:fs';
import { createHash,webcrypto } from 'node:crypto';
import App from '../src/App';
const raw=readFileSync('public/development.json','utf8');
const base=JSON.parse(raw),hash=(s:string)=>createHash('sha256').update(s).digest('hex');
const p=JSON.parse(readFileSync('../research/position-evidence/candidate.json','utf8'));
// Test-only approval; no production authority is approved by this fixture.
p.authorityStatus='APPROVED';
const pos=JSON.stringify(p);
afterEach(()=>{cleanup();vi.unstubAllGlobals();location.hash='';});
it('uses historical coordinates at a fixed boundary and preserves keyboard comparison',async()=>{
 vi.stubGlobal('crypto',webcrypto);
 vi.stubGlobal('fetch',vi.fn((url:string)=>{
  const file=url.split('/').pop();
  const data=file==='positions-release.json'?{schema:1,file:'positions.json',sha256:hash(pos),baseBundleSha256:hash(raw)}:
   file==='release.json'?{schema:1,file:'development.json',sha256:hash(raw)}:undefined;
  return Promise.resolve({ok:true,status:200,json:()=>Promise.resolve(data),text:()=>Promise.resolve(file==='development.json'?raw:file==='positions.json'?pos:'<svg><path d="M0 0L500 500"/></svg>')});
 }));
 Object.defineProperty(SVGElement.prototype,'getTotalLength',{configurable:true,value:()=>100});
 Object.defineProperty(SVGElement.prototype,'getPointAtLength',{configurable:true,value:()=>({x:0,y:0})});
 const a=base.attempts.find((a:any)=>a.state==='ok'&&p.frames.some((f:any)=>f.time===a.time&&f.order===a.order&&f.points.length>2));
 location.hash=`race=${base.id}&driver=${a.driver}&lap=${a.lap}&time=${a.time}&order=${a.order}`;
 render(<App/>);
 await screen.findByText(/Positions recorded approximately/);
 const f=p.frames.find((f:any)=>f.time===a.time&&f.order===a.order),point=f.points[0];
 const driver=base.drivers.find((d:any)=>d.id===point.driver);
 const marker=screen.getByRole('button',{name:`Compare ${driver.name}`});
 expect(marker.querySelector('circle')?.getAttribute('cx')).toBe(String(point.x));
 const subject=(screen.getByLabelText('Prediction for') as HTMLSelectElement).value;
 const clock=screen.getByText(/Race time /).textContent;
 fireEvent.keyDown(marker,{key:'Enter'});
 expect(marker.getAttribute('aria-pressed')).toBe('true');
 expect((screen.getByLabelText('Prediction for') as HTMLSelectElement).value).toBe(subject);
 fireEvent.click(screen.getByLabelText('Show actual stop'));
 expect(marker.querySelector('circle')?.getAttribute('cx')).toBe(String(point.x));
 const other=base.drivers.find((d:any)=>d.id!==subject);
 fireEvent.click(screen.getByRole('button',{name:`View prediction for ${other.name}`}));
 expect(screen.getByText(/Race time /).textContent).toBe(clock);
 expect(marker.querySelector('circle')?.getAttribute('cx')).toBe(String(point.x));
 expect(within(screen.getByRole('table')).getAllByRole('row')).toHaveLength(21);
 expect(marker.querySelector('circle')?.getAttribute('cx')).toBe(String(point.x));
 expect(screen.getByText(/Race time /).textContent).toBe(clock);
});
