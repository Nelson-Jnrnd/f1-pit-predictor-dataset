// @vitest-environment jsdom
import { afterEach,it,expect } from 'vitest';
import { cleanup,render,screen,fireEvent } from '@testing-library/react';
import DriverPortrait from '../src/DriverPortrait';
afterEach(cleanup);
it('shows a readable missing-image fallback and loads the next driver without refreshing',()=>{
 const {container,rerender}=render(<DriverPortrait src='/assets/MAG.png' code='MAG' name='Kevin Magnussen'/>);
 fireEvent.error(container.querySelector('img')!);
 expect(screen.getByRole('img',{name:'Portrait unavailable for Kevin Magnussen'}).textContent).toBe('MAG');
 rerender(<DriverPortrait src='/assets/NOR.png' code='NOR' name='Lando Norris'/>);
 const next=container.querySelector('img')!;
 expect(next.getAttribute('src')).toBe('/assets/NOR.png');
 expect(next.hidden).toBe(false);
 fireEvent.load(next);
 expect(screen.queryByRole('img',{name:/unavailable/})).toBeNull();
 rerender(<DriverPortrait src='/assets/HAM.png' code='HAM' name='Lewis Hamilton'/>);
 expect(container.querySelector('img')!.hidden).toBe(false);
});
