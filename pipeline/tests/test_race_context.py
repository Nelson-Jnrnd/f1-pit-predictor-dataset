import copy
from pathlib import Path
import tempfile
import unittest
import numpy as np
from pipeline import race_features as f, race_models as rf, comparison_models as m


def observation(lap=8):
    return dict(artifact_id='obs',semantic_observation_key=['2024-R10-R','1',lap],selected_driver_completed_laps=lap,
        canonical_state=dict(timing={'1':dict(_last_time_completed_lap=lap,LastLapTime={'Value':'1:30.0'},
            BestLapTime={'Lap':4,'Value':'1:28.5'},Position='3',GapToLeader='+4.5',IntervalToPositionAhead={'Value':'+0.9'})}),
        causal_input_fact_refs=['source:4'])


class RaceFeaturesTests(unittest.TestCase):
    def test_unfinished_or_future_lap_values_never_supply_pace(self):
        o=observation();o['canonical_state']['timing']['1']['_last_time_completed_lap']=9
        o['canonical_state']['timing']['1']['BestLapTime']['Lap']=9
        values=f.view(o)['values']
        self.assertIsNone(values['last_lap']);self.assertIsNone(values['best_lap']);self.assertIsNone(values['pace_delta'])

    def test_future_and_target_fields_are_ignored(self):
        o=observation();before=f.view(o)
        o['canonical_state']['timing']['1'].update(PitStatus='InLap',NextCompound='SOFT',NumberOfPitStops=4,CurrentLapTime='0:54')
        self.assertEqual(before,f.view(o))

    def test_lapped_or_invalid_fields_stay_missing(self):
        o=observation();t=o['canonical_state']['timing']['1'];t.update(GapToLeader='1 LAP',Position='-1',IntervalToPositionAhead={'Value':'nan'})
        result=f.view(o)
        self.assertTrue({'gap','position','interval'}<=set(result['omissions']))
        self.assertEqual(result['values']['pace_delta'],1.5)

    def test_inference_freezes_context_and_advances_only_registered_projection(self):
        row=dict(grid=dict(L=8,N_T=60,K_T=52),tyre=dict(age=4,compound='MEDIUM'),race_features=f.view(observation()))
        first=rf.design(row,0,'RF_CONTEXT');later=rf.design(row,10,'RF_CONTEXT')
        self.assertEqual(first[14:],later[14:]);self.assertEqual(later[6]-first[6],10)
        row['tyre']={'fallback':'STINT_MISSING'}
        values=rf.design(row,4,'RF_TYRE');self.assertEqual(values[6:8],[-1.,1.]);self.assertEqual(sum(values[8:]),0)

    def test_forest_output_retains_terminal_mass_and_matches_grid(self):
        row=dict(grid=dict(L=8,N_T=12,K_T=4),tyre=dict(age=4,compound='MEDIUM'),race_features=f.view(observation()))
        units=[(copy.deepcopy(row),dict(kind='REALIZED_REGION',j=1)) for _ in range(250)]
        units.extend((copy.deepcopy(row),dict(kind='REALIZED_NO_EVENT')) for _ in range(250))
        b0=dict(cutoff='2024-01-01',q_open=.8,k_terciles=[3,8],dataset_refs=[])
        with tempfile.TemporaryDirectory() as tmp:
            model,estimator=rf.fit(units,'RF_CONTEXT',b0,Path(tmp),'reg')
            rows=[row,{**row,'grid':dict(L=12,N_T=12,K_T=1)}]
            distributions=rf.distributions(rows,'RF_CONTEXT',model,estimator)
        for dist in distributions:
            p=dist['event_region_probabilities'];q=dist['terminal_no_event_probability']
            self.assertEqual(len(p),dist['region_grid']['K_T']);self.assertAlmostEqual(sum(p)+q,1)
            self.assertTrue(all(np.isfinite(v) and v>=1e-6 for v in p+[q]))
        self.assertAlmostEqual(distributions[1]['terminal_no_event_probability'],.8*(1-2e-6)+1e-6)
        self.assertIsNone(model['parameters']['class_weight'])


if __name__=='__main__':unittest.main()
