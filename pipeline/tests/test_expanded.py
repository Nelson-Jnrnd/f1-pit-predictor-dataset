import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np
from pipeline import expanded_sources as e, expanded_models as m, expanded_comparison as c
from pipeline import comparison_models as base

class ExpandedTests(unittest.TestCase):
    def test_final_refused_before_file_read(self):
        with patch.object(Path,'read_bytes',side_effect=AssertionError('Forbidden final read')):
            with self.assertRaisesRegex(ValueError,'Protected'):e.read_raw(dict(season=2026,round=1))
            with self.assertRaisesRegex(ValueError,'Protected'):e.acquire(dict(season=2026,round=1))
            with self.assertRaisesRegex(ValueError,'Protected'):c.open_race(Path('/x'),dict(season=2026,round=1),Path('/ledger'),'join',1)
    def test_training_cutoff_checked_before_read(self):
        with patch.object(Path,'read_bytes',side_effect=AssertionError('Late read')):
            with self.assertRaisesRegex(ValueError,'cutoff'):c.open_race(Path('/x'),dict(season=2019,round=1,date='2019-01-01'),Path('/ledger'),'join',1,'2019-01-01')
    def test_existing_unsupported_sources_remain_excluded(self):
        with patch.object(e,'read_raw',side_effect=AssertionError('Unsupported read')):
            self.assertEqual(e.verify(dict(season=2018,round=2))['status'],'EXCLUDED')
            self.assertEqual(e.verify(dict(season=2018,round=12))['status'],'EXCLUDED')
    def test_stop_go_penalty_qa_is_recognized(self):
        records={'RaceControlMessages':[
            {'prefix':100,'payload':{'Messages':{'0':{'Message':'10 SECOND STOP/GO PENALTY FOR CAR 87 (BEA) - UNSAFE CONDITION'}}}},
            {'prefix':200,'payload':{'Messages':{'1':{'Message':'PENALTY SERVED - 10 SECOND STOP/GO PENALTY FOR CAR 87 (BEA) - UNSAFE CONDITION'}}}}]}
        visits={'87':[{'entry':150,'lap':10,'class':'NEG'}]}
        result=e.penalty_context(records,visits)
        self.assertEqual(len(result),1);self.assertEqual(result[0]['driver'],'87')
        self.assertEqual(result[0]['class'],'NEG')
    def test_ridge_omission_and_new_compound_fallback(self):
        grid=dict(L=2,N_T=10,K_T=8);b0=dict(id='B0',hazards=[.1]*41,q_open=1.,floor=1e-6)
        ridge=dict(id='TYRE_RIDGE',levels=['SOFT'],beta=[0,0,0,0],q_open=1.,floor=1e-6)
        expected=base.predict(b0,grid,{},b0)
        self.assertEqual(m.predict(ridge,grid,dict(fallback='missing'),b0),expected)
        self.assertEqual(m.predict(ridge,grid,dict(compound='WET',age=2),b0),expected)
        full=m.predict(ridge,grid,dict(compound='SOFT',age=2),b0)
        self.assertAlmostEqual(sum(full['event_region_probabilities'])+full['terminal_no_event_probability'],1.)
        self.assertGreaterEqual(full['event_region_probabilities'][-1],1e-6)
    def test_fit_failure_never_uses_arbitrary_coefficients(self):
        grid=dict(L=2,N_T=10,K_T=8);b0=dict(id='B0',hazards=[.1]*41,q_open=1.,floor=1e-6)
        with self.assertRaisesRegex(ValueError,'failed'):m.predict(dict(id='TYRE_RIDGE',fit_failure='failed'),grid,dict(compound='SOFT',age=2),b0)
    def test_boundary_tail_ridge_is_a_separate_candidate(self):
        units=[]
        for lap,age in ((0,2),(1,3),(2,4),(3,5)):
            row={'grid':dict(L=lap,N_T=10,K_T=10-lap),'tyre':dict(age=age,compound='SOFT')}
            units.append((row,{'kind':'REALIZED_REGION','j':2}))
            units.append((row,{'kind':'REALIZED_NO_EVENT'}))
        models=m.fit(units,'2019-01-01',[],'registration')
        self.assertIn('fit_failure',models['B1'])
        self.assertNotIn('fit_failure',models['TYRE_RIDGE'])
        self.assertEqual(models['TYRE_RIDGE']['q_open'],1.)
    def test_selection_uses_explicit_reference_fallback(self):
        from pipeline.tests.test_comparison import ReviewRegressionTests
        from pipeline import comparison as original
        predicted,labels=ReviewRegressionTests().fixture()
        rows=original.join_scores(predicted,labels,'resolution')
        ridge=dict(next(r for r in rows if r['model']=='B0'));ridge['model']='TYRE_RIDGE';rows.append(ridge)
        rows=[{k:v for k,v in r.items() if k not in ('score','p0','p3','q','y0','y3','ynone','entropy','rps','window_mass','window_event_mass','window_hit','event_window_hit')}|{'category':'A4','failure':'unsupported'} if r['model']=='B1' else r for r in rows]
        result=c.selection(rows)
        self.assertEqual(result['reference'],'B0');self.assertEqual(result['selected'],'B0')
        bad=dict(ridge);bad.pop('score');bad['category']='A4';bad['failure']='missing'
        result=c.selection([r for r in rows if r['model']!='TYRE_RIDGE']+[bad])
        self.assertIsNone(result['selected'])
    def test_forecasts_have_no_label_input(self):
        import inspect
        self.assertNotIn('labels',inspect.signature(c.forecasts).parameters)
        self.assertNotIn('labels',inspect.signature(m.predict).parameters)

if __name__=='__main__':unittest.main()
