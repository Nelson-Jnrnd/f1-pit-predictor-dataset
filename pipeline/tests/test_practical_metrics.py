import copy
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from pipeline import practical_metrics as p, historical_audit as a, comparison_data as data

class PracticalTests(unittest.TestCase):
    def test_unknown_and_crossing_sets_are_never_negative(self):
        self.assertIsNone(p.binary_outcome({'kind':'NOT_REALIZED'},10))
        self.assertIsNone(p.binary_outcome({'kind':'REALIZED_REGION_SET','a':2,'b':4},10))
        self.assertEqual(p.binary_outcome({'kind':'REALIZED_REGION_SET','a':0,'b':2},10),1)
        self.assertEqual(p.binary_outcome({'kind':'REALIZED_REGION_SET','a':3,'b':5},10),0)
        self.assertEqual(p.binary_outcome({'kind':'REALIZED_NO_EVENT'},10),0)
    def test_short_grid_keeps_open_final_region(self):
        self.assertEqual(p.binary_outcome({'kind':'REALIZED_REGION','j':0},1),1)
        self.assertEqual(p.binary_outcome({'kind':'REALIZED_REGION','j':2},3),1)
    def test_window_set_ambiguity(self):
        self.assertIsNone(p.window_hit({'kind':'REALIZED_REGION_SET','a':1,'b':3},2,4))
        self.assertEqual(p.window_hit({'kind':'REALIZED_REGION_SET','a':2,'b':3},2,4),1)
        self.assertEqual(p.window_hit({'kind':'REALIZED_REGION_SET','a':0,'b':1},2,4),0)
    def test_confusion_counts_unknown_and_missing(self):
        rows=[dict(y3=1,p3=.9),dict(y3=0,p3=.8),dict(y3=1,p3=.1),dict(y3=0,p3=.1),dict(y3=None,p3=.9),dict(y3=1,p3=None)]
        result=p.confusion(rows,.5)
        self.assertEqual([result[k] for k in ('TP','FP','FN','TN')],[1,1,1,1])
        self.assertEqual(result['unknown_binary'],1);self.assertEqual(result['missing_forecast_known_binary'],1)
        self.assertEqual(result['precision'],.5);self.assertEqual(result['recall'],.5)
        self.assertIsNone(p.confusion([],1)['precision'])
    def test_threshold_tie_and_holdout_isolation(self):
        selection=[dict(y3=1,p3=.9,race='a',date='2025-01-01',season=2025,round=1),dict(y3=0,p3=.1,race='a',date='2025-01-01',season=2025,round=1)]
        holdout=[dict(y3=0,p3=.95,race='b',date='2025-02-01',season=2025,round=2)]
        result=p.chronological_threshold(selection,holdout)
        self.assertEqual(result['threshold'],.9)
        holdout[0]['y3']=1
        self.assertEqual(result,p.chronological_threshold(selection,holdout))
        with self.assertRaisesRegex(ValueError,'chronological'):p.chronological_threshold(holdout,selection)
    def test_final_threshold_cohort_refused(self):
        selection=[dict(y3=1,p3=.9,race='a',date='2025-01-01',season=2025,round=1)]
        holdout=[dict(y3=0,p3=.1,race='b',date='2026-01-01',season=2026,round=1)]
        with self.assertRaisesRegex(ValueError,'Protected'):p.chronological_threshold(selection,holdout)
    def test_unique_events_include_missing_forecast_and_deduplicate(self):
        rows=[dict(event_ref='e',y3=1,p3=.9),dict(event_ref='e',y3=1,p3=.8),dict(event_ref='f',y3=1,p3=None),dict(event_ref='g',y3=0,p3=.9)]
        result=p.unique_stops(rows,.5)
        self.assertEqual(result['with_known_horizon_checkpoint'],2)
        self.assertEqual(result['detected'],1);self.assertEqual(result['recall'],.5)
        self.assertEqual(result['repeated_positive_alerts'],1)
        self.assertEqual(result['without_known_horizon_checkpoint'],1)
    def test_final_saved_fold_refused_before_payload_read(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            data.write_json(root/'complete.json',dict(config=dict(training=[],validation=[dict(season=2026,round=1)],cutoff='2026-01-01'),hashes={'predictions.json.gz':'hash'}))
            with self.assertRaisesRegex(ValueError,'Protected'):p.verified_saved_fold(root)
    def test_hash_corruption_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'predictions.json.gz').write_bytes(b'corrupt')
            data.write_json(root/'complete.json',dict(config=dict(training=[],validation=[dict(season=2025,round=1)],cutoff='2025-01-01'),hashes={'predictions.json.gz':'wrong'}))
            with self.assertRaisesRegex(ValueError,'hash'):p.verified_saved_fold(root)

class AuditTests(unittest.TestCase):
    def test_final_csv_refused_before_read(self):
        with patch.object(Path,'read_bytes',side_effect=AssertionError('Forbidden read')):
            with self.assertRaisesRegex(ValueError,'Protected'):a.audit_csv(Path('/missing'),2026)
    def test_schema_missingness_and_duplicate_audit(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'race.csv'
            path.write_text('Track,DriverNumber,LapNumber,PitStatus\nTrack,1,2,InLap\nTrack,1,2,InLap\n')
            result=a.audit_csv(path,2020)
            self.assertEqual(result['duplicate_driver_lap_rows'],1)
            self.assertIn('TotalLaps',result['missing_required'])
            self.assertIn('TyresNotChanged',result['missing_authority'])
            self.assertEqual(result['admission'],'REJECTED_LEGACY_DERIVED_ROWS')
    def test_season_overlap_without_duplicate_training(self):
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td);text='Track,DriverNumber,LapNumber\nTrack,1,1.0\n'
            (folder/'season.csv').write_text(text);(folder/'race.csv').write_text(text)
            result=a.season_overlap(folder,2020)
            self.assertEqual(result['overlap_keys'],1)

if __name__=='__main__':unittest.main()
