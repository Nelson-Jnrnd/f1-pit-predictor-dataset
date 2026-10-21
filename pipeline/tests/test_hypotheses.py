import copy
from pathlib import Path
import tempfile
import unittest
from pipeline import hypothesis_models as h, hypotheses as run
from pipeline.tests.test_race_context import observation
from pipeline import race_features as features, comparison_data as data


def row(n=60,lap=12,age=6):
    return dict(grid=dict(L=lap,N_T=n,K_T=n-lap),tyre=dict(age=age,compound='MEDIUM'),race_features=features.view(observation(lap)))


class HypothesisTests(unittest.TestCase):
    def test_percent_features_use_scheduled_distance_and_preserve_missingness(self):
        r=row();v=h.design(r,3,'H1_PERCENT')
        self.assertEqual(v[:6],[.2,.05,.25,1/60,.15,0.])
        r['tyre']={'fallback':'missing'};v=h.design(r,3,'H1_PERCENT')
        self.assertEqual(v[4:6],[-1.,1.]);self.assertEqual(sum(v[6:12]),0)
        r['eventual_distance']=22;r['future_stop_count']=2
        self.assertEqual(v,h.design(r,3,'H1_PERCENT'))

    def test_all_hypotheses_freeze_context(self):
        r=row()
        for name in h.IDS:
            offset=12 if name=='H1_PERCENT' else 14
            self.assertEqual(h.design(r,0,name)[offset:],h.design(r,10,name)[offset:])
        with self.assertRaises(ValueError):h.design(r,0,'extra')

    def test_recent_scope_uses_earlier_admitted_seasons_and_blocks_2026(self):
        part=[dict(season=y,round=1,date=f'{y}-03-01') for y in (2018,2019,2020,2021,2023,2024,2025)]
        self.assertEqual([r['season'] for r in h.scope(part,'2023-01-01','H4_RECENT')],[2020,2021])
        self.assertEqual([r['season'] for r in h.scope(part,'2026-01-01','H4_RECENT')],[2024,2025])
        with self.assertRaises(ValueError):h.scope(part+[dict(season=2026,round=1,date='2026-03-01')],'2027-01-01','H4_RECENT')

    def test_subset_b0_and_estimators_keep_complete_probability_output(self):
        r=row(16,12);units=[(copy.deepcopy(r),dict(kind='REALIZED_REGION',j=1)) for _ in range(150)]
        units.extend((copy.deepcopy(r),dict(kind='REALIZED_NO_EVENT')) for _ in range(150))
        b0=h.b0_subset(units,'2025-01-01',[],'reg')
        self.assertEqual(b0['q_open'],1.)
        with tempfile.TemporaryDirectory() as tmp:
            for name in ('H2_DETAIL','H3_BOOST'):
                model,est=h.fit(units,name,b0,Path(tmp),'reg',[])
                out=h.distributions([r,{**r,'grid':dict(L=16,N_T=16,K_T=1)}],name,model,est)
                self.assertIsNone(model['parameters']['class_weight'])
                for dist in out:
                    values=dist['event_region_probabilities']+[dist['terminal_no_event_probability']]
                    self.assertAlmostEqual(sum(values),1);self.assertGreaterEqual(min(values),1e-6)

    def test_completed_payload_tampering_and_configuration_changes_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);data.write_json(path/'model.json',{})
            data.write_json(path/'complete.json',dict(config={'x':1},files={'model.json':run.sha(path/'model.json')}))
            run.verify(path,config={'x':1})
            with self.assertRaises(ValueError):run.verify(path,config={'x':2})
            data.write_json(path/'model.json',{'changed':True})
            with self.assertRaises(ValueError):run.verify(path)

if __name__=='__main__':unittest.main()
