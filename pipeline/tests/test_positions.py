import copy
import datetime as dt
import gzip
import hashlib
import json
import os
from pathlib import Path
import time
import unittest
from unittest.mock import patch
from pipeline import development as d
from pipeline import positions as p

class PositionBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.clock={'start':1000,'end':2000,'unhealthy':[]}
        self.boundary={'prefix':1100,'ordinal':3,'stream':'TimingData'}
        self.evidence={'shared_clock_evidence':{'base_epoch':0},'geometry':{'trace':[[0,0],[100,0],[100,100],[0,100]],'transform':{'minX':0,'maxY':100,'scale':1}}}
    def sample(self,prefix,epoch=None,x=30,driver='1'):
        return dict(prefix=prefix,epoch=prefix if epoch is None else epoch,ordinal=int(prefix),sample_ordinal=0,ref=str(prefix),timestamp='UTC',entries={driver:{'X':x,'Y':30,'Z':0}})
    def test_strict_publication_margin_and_no_future_sample(self):
        at=self.sample(1090)
        self.assertIsNone(p.project([at],self.boundary,self.clock,self.evidence,['1'])['sample'])
        past=self.sample(1089)
        future=self.sample(1099)
        result=p.project([past,future],self.boundary,self.clock,self.evidence,['1'])
        self.assertEqual(result['sample']['publicationPrefix'],1089)
        result=p.project([self.sample(1089,epoch=1100)],self.boundary,self.clock,self.evidence,['1'])
        self.assertIsNone(result['sample'])
    def test_common_clock_missing_car_and_latest_correction(self):
        a=self.sample(1087,epoch=1085,x=20);b=self.sample(1088,epoch=1085,x=40)
        result=p.project([a,b],self.boundary,self.clock,self.evidence,['1','2'])
        self.assertEqual(result['sample']['sourceRef'],b['ref'])
        self.assertEqual([r['driver'] for r in result['points']],['1'])
        self.assertEqual(result['points'][0]['x'],60)
        self.assertEqual(p.project([a,b],{'prefix':1098,'ordinal':2,'stream':'TimingData'},self.clock,self.evidence,['1'])['sample']['sourceRef'],a['ref'])
    def test_freshness_and_gap_no_carry(self):
        self.assertIsNone(p.project([self.sample(1075)],self.boundary,self.clock,self.evidence,['1'])['sample'])
        self.clock['unhealthy']=[[1087,1088]]
        self.assertIsNone(p.project([self.sample(1086)],self.boundary,self.clock,self.evidence,['1'])['sample'])
        self.assertIsNotNone(p.project([self.sample(1089)],self.boundary,self.clock,self.evidence,['1'])['sample'])
        self.assertIsNone(p.project([self.sample(1089)],{'prefix':1088,'ordinal':1,'stream':'TimingData'},self.clock,self.evidence,['1'])['sample'])
    def test_invalid_off_circuit_and_zero_coordinates(self):
        s=self.sample(1089,x=1000)
        self.assertEqual(p.project([s],self.boundary,self.clock,self.evidence,['1'])['points'],[])
        self.assertFalse(p.valid_coord({'X':0,'Y':0,'Z':0}))
        self.assertFalse(p.valid_coord({'X':True,'Y':1,'Z':0}))
        self.assertFalse(p.valid_coord({'X':float('nan'),'Y':1,'Z':0}))
    def pit_event(self,prefix,value):
        return dict(prefix=prefix,ordinal=0,stream='TimingData',pit=value)
    def test_pit_at_sample_not_later_boundary_and_converse(self):
        initial=self.pit_event(600,False)
        entry=self.pit_event(1060,True);exit_=self.pit_event(1090,False)
        self.assertFalse(p.sample_pit_safe([initial,entry,exit_],1085,self.boundary,self.clock))
        self.assertTrue(p.sample_pit_safe([initial,self.pit_event(1099,True)],1085,self.boundary,self.clock))
    def test_ambiguous_unknown_and_gap_pit_states_fail_closed(self):
        initial=self.pit_event(600,False)
        for prefix in (1075,1085,1095):
            self.assertFalse(p.sample_pit_safe([initial,self.pit_event(prefix,True)],1085,self.boundary,self.clock))
        self.assertFalse(p.sample_pit_safe([],1085,self.boundary,self.clock))
        self.clock['unhealthy']=[[1060,1070]]
        self.assertFalse(p.sample_pit_safe([initial],1085,self.boundary,self.clock))
        self.assertTrue(p.sample_pit_safe([initial,self.pit_event(1071,False)],1085,self.boundary,self.clock))
    def test_future_pit_transition_does_not_change_sample_projection(self):
        initial=self.pit_event(600,False)
        self.assertTrue(p.sample_pit_safe([initial,self.pit_event(1101,True)],1089,self.boundary,self.clock))

    def test_utc_is_explicit_and_timezone_independent(self):
        self.assertEqual(p.utc('2024-06-30T13:00:00'),p.utc('2024-06-30T13:00:00Z'))
        self.assertEqual(p.utc('2024-06-30T15:00:00+02:00'),p.utc('2024-06-30T13:00:00Z'))
    def test_protected_scope_guard_precedes_file_access(self):
        with patch.object(d,'require_development',side_effect=ValueError('protected')),patch.object(Path,'read_text',side_effect=AssertionError('read')):
            with self.assertRaisesRegex(ValueError,'protected'):p.load_source('race','Position.z')

class PositionEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence,cls.rs,cls.clock=p.verify()
    def test_proven_prior_geometry_and_synchronized_cohort(self):
        e=self.evidence;g=e['geometry']
        self.assertEqual(e['scope']['session_key'],9550)
        self.assertEqual(e['shared_clock_evidence']['roster_count'],20)
        self.assertLess(g['prior_evidence_last_modified_utc'],g['available_before'])
        self.assertLess(g['closure_ratio'],.015)
        self.assertGreater(e['native_registration']['prior_trace_matches'],100)
        d.verify_artifact(g);d.verify_artifact(e)
    def test_candidate_cannot_be_released(self):
        with self.assertRaisesRegex(ValueError,'Independent authority'):p.export(self.evidence,self.rs,self.clock,approved=True)
    def test_base_prediction_bytes_unchanged_and_frame_joins(self):
        base=(p.ROOT/'explorer/public/development.json').read_bytes();before=hashlib.sha256(base).hexdigest()
        bundle=p.export(self.evidence,self.rs,self.clock)
        self.assertEqual(bundle['baseBundleSha256'],before)
        self.assertEqual(hashlib.sha256((p.ROOT/'explorer/public/development.json').read_bytes()).hexdigest(),before)
        parent=json.loads(base)
        self.assertEqual([(f['time'],f['order']) for f in bundle['frames']],[(f['time'],f['order']) for f in parent['frames']])
        self.assertGreater(sum(bool(f['points']) for f in bundle['frames']),1000)
        for frame in bundle['frames']:
            s=frame['sample']
            if s:
                self.assertLess(s['publicationPrefix']+5,frame['boundaryPrefix']-5)
                self.assertLessEqual(frame['time']+5-s['time'],20)
                self.assertEqual(len({point['driver'] for point in frame['points']}),len(frame['points']))
        self.assertTrue(any(f['sample'] is None for f in bundle['frames']))
