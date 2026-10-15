import copy
import gzip
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from pipeline import development as p

RUN = p.ROOT/'research/development-race/run-1'
def load(name):
    return json.loads(gzip.decompress((RUN/(name+'.json.gz')).read_bytes()))

class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.clock={'start':1000,'end':2000,'unhealthy':[[1500,1510]]}
        self.boundary={'stream':'TimingData','prefix':1100,'ordinal':5}
    def record(self,t,ordinal=1,stream='TimingAppData',payload=None):
        return dict(prefix=t,ordinal=ordinal,stream=stream,ref=f'{stream}:{ordinal}',payload=payload or {})
    def test_strict_cross_stream_bounds_and_ties(self):
        self.assertFalse(p.admitted(self.record(1090),self.boundary,self.clock))
        self.assertTrue(p.admitted(self.record(1089.999),self.boundary,self.clock))
        self.assertFalse(p.admitted(self.record(1100),self.boundary,self.clock))
        self.assertTrue(p.admitted(self.record(1100,5,'TimingData'),self.boundary,self.clock))
        self.assertFalse(p.admitted(self.record(1100,6,'TimingData'),self.boundary,self.clock))
    def test_prerace_and_clock_health(self):
        self.assertTrue(p.admitted(self.record(694.999),self.boundary,self.clock))
        self.assertFalse(p.admitted(self.record(695),self.boundary,self.clock))
        self.assertFalse(p.admitted(self.record(1505),self.record(1600,9,'TimingData'),self.clock))
    def test_later_correction_cannot_rewrite_observation(self):
        rs=[self.record(1050,1,'TimingData',{'Lines':{'1':{'Position':'2'}}}),
            self.record(1150,2,'TimingData',{'Lines':{'1':{'Position':'1'}}})]
        reducer=p.CausalReducer(rs,self.clock,True)
        first,_=reducer.at(self.boundary)
        second,_=reducer.at(self.record(1200,3,'TimingData'))
        self.assertEqual(first['1']['Position'],'2')
        self.assertEqual(second['1']['Position'],'1')
    def test_gap_invalidates_affected_fields_but_not_unaffected_or_future(self):
        rs=[self.record(1400,1,'TimingData',{'Lines':{'1':{'Position':'2','InPit':False,'BestLapTime':{'Value':'1:20.0'}}}}),
            self.record(1505,2,'TimingData',{'Lines':{'1':{'Position':'1','InPit':True}}}),
            self.record(1600,3,'TimingData',{'Lines':{'1':{'NumberOfLaps':4}}})]
        reducer=p.CausalReducer(rs,self.clock,True)
        before,_=reducer.at(self.record(1450,1,'TimingData'))
        after,_=reducer.at(self.record(1600,3,'TimingData'))
        self.assertEqual(before['1']['Position'],'2')
        self.assertNotIn('Position',after['1']);self.assertNotIn('InPit',after['1'])
        self.assertEqual(after['1']['BestLapTime']['Value'],'1:20.0')
        self.assertEqual(after['1']['NumberOfLaps'],4)
    def test_unknown_timing_is_not_lap_zero(self):
        driver={'id':'1'}
        self.assertIsNone(p.timing_rows({'timing':{},'tyres':{}},[driver])[0]['completed'])
        self.assertEqual(p.timing_rows({'timing':{},'tyres':{}},[driver],race_start=True)[0]['completed'],0)
    def test_protected_source_refused_before_path_read(self):
        with patch.object(Path,'read_text',side_effect=AssertionError('read protected file')):
            with self.assertRaisesRegex(ValueError,'Protected'):
                p.read_source(2026,1)
    def test_unverified_endpoints_are_not_admitted(self):
        self.assertNotIn('Position',p.FEEDS)
        self.assertNotIn('CarData',p.FEEDS)
    def test_full_distribution_floor_open_tail_and_missing_support(self):
        model={'hazards':[.1]*41,'q_open':.5,'floor':1e-6}
        dist=p.distribution(model,{'L':20,'N_T':71,'K_T':51})
        self.assertEqual(len(dist['event_region_probabilities']),51)
        self.assertAlmostEqual(sum(dist['event_region_probabilities'])+dist['terminal_no_event_probability'],1)
        self.assertTrue(all(v>=1e-6 for v in dist['event_region_probabilities']))
        model['hazards'][40]=None
        with self.assertRaisesRegex(ValueError,'no training support'):
            p.distribution(model,{'L':20,'N_T':71,'K_T':51})
    def test_grid_missing_distance_and_extensions(self):
        with self.assertRaisesRegex(ValueError,'REQUIRED_CONTEXT_MISSING'):
            p.grid({'canonical_state':{'distance':{}},'selected_driver_completed_laps':4})
        self.assertEqual(p.grid({'canonical_state':{'distance':{'TotalLaps':71}},'selected_driver_completed_laps':72})['K_T'],1)
    def test_missing_tyres_remain_missing(self):
        self.assertEqual(p.tyre_context({'tyres':{}},'1'),{'compound':None,'age':None})

class ArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.obs=load('11-observation');cls.replay=load('replay');cls.dev=load('development')
        cls.init=load('11-initialization');cls.retro=load('retrospective')
    def test_canonical_content_digests(self):
        for name in ('10-source','11-source','10-clock','11-clock','10-observation','11-observation',
                     'development','replay','retrospective','11-initialization','11-resolution'):
            p.verify_artifact(load(name))
    def test_replay_has_no_outcomes_and_deterministic_predictions(self):
        again=p.replay(self.obs,self.init,self.dev['model'],'2024-06-30','different-run')
        for a,b in zip(self.replay['records'],again['records'],strict=True):
            self.assertNotIn('resolution',a)
            if 'snapshot' in a:
                self.assertEqual(a['snapshot']['distribution'],b['snapshot']['distribution'])
                self.assertEqual(a['snapshot']['request_digest'],b['snapshot']['request_digest'])
                self.assertNotEqual(a['snapshot']['artifact_id'],b['snapshot']['artifact_id'])
    def test_cutoff_rejected_before_inference(self):
        with self.assertRaisesRegex(ValueError,'cutoff'):
            p.replay(self.obs,self.init,self.dev['model'],'2024-06-29','x')
    def test_export_verifies_lineage_and_rejects_mutation(self):
        source=load('11-source');clock=load('11-clock');ledger=load('ledger')
        bad=copy.deepcopy(self.replay);next(r for r in bad['records'] if 'snapshot' in r)['snapshot']['distribution']['terminal_no_event_probability']=.99
        with self.assertRaisesRegex(ValueError,'digest'):
            p.export(source,self.obs,bad,self.retro,self.dev['model'],clock,ledger)
        with self.assertRaisesRegex(ValueError,'opening'):
            p.export(source,self.obs,self.replay,self.retro,self.dev['model'],clock,[])
    def test_hashed_retrospective_join_mismatch_is_rejected(self):
        for mutation in ('snapshot','episode','duplicate','ledger'):
            retro=copy.deepcopy(self.retro);ledger=load('ledger')
            if mutation=='snapshot':retro['records'][0]['snapshot_ref']='different'
            if mutation=='episode':retro['records'][0]['target_episode_key']=['different']
            if mutation=='duplicate':retro['records'].append(copy.deepcopy(retro['records'][0]))
            if mutation=='ledger':ledger[-1]['resolution_run_ref']='different'
            retro['artifact_id']=p.digest({k:v for k,v in retro.items() if k!='artifact_id'})
            with self.assertRaises(ValueError,msg=mutation):
                p.export(load('11-source'),self.obs,self.replay,retro,self.dev['model'],load('11-clock'),ledger)
    def test_release_matches_artifacts_without_recomputing_predictions(self):
        bundle=json.loads((p.ROOT/'explorer/public/development.json').read_text())
        source=load('11-source');clock=load('11-clock');ledger=load('ledger')
        expected=p.export(source,self.obs,self.replay,self.retro,self.dev['model'],clock,ledger)
        self.assertEqual(expected,bundle)
        rows=[a for a in bundle['attempts'] if a['state']=='ok']
        self.assertGreater(len(rows),0)
        self.assertTrue(all(a['scheduledDistance']==71 and len(a['p'])==max(1,71-a['lap']) for a in rows))
        self.assertTrue(all(r['progress'] is None for f in bundle['frames'] for r in f['rows']))
        self.assertTrue(all(len(f['rows'])==20 for f in bundle['frames']))
        self.assertTrue(any(len({r['completed'] for r in f['rows'] if r['completed'] is not None})>1 for f in bundle['frames']))
        self.assertTrue(any(a['state']=='failed' for a in bundle['attempts']))
    def test_truth_changes_do_not_affect_eligibility_or_replay(self):
        before=p.encoded(self.obs)
        changed=copy.deepcopy(self.retro);changed['records'][0]['mapped']={'kind':'REALIZED_NO_EVENT'}
        self.assertEqual([r['eligibility_status'] for r in p.initialize(self.obs)['records']], [r['eligibility_status'] for r in self.init['records']])
        p.replay(self.obs,self.init,self.dev['model'],'2024-06-30','isolated')
        self.assertEqual(p.encoded(self.obs),before)
    def test_export_rejects_final_partition_even_with_forged_metadata(self):
        source=load('11-source');source['season']=2026
        with self.assertRaisesRegex(ValueError,'Protected'):
            p.export(source,self.obs,self.replay,self.retro,self.dev['model'],load('11-clock'),load('ledger'))

class TargetTests(unittest.TestCase):
    def fixture(self,entry=1200,service='CONFIRMED_TYRE_SERVICE',terminal=True,gaps=None):
        o={'artifact_id':'observation','prediction_boundary':{'prefix':1100,'stream':'TimingData','ordinal':2}}
        init={'artifact_id':'initializations','records':[{'eligibility_status':'ELIGIBLE','initialization':{'observation_artifact_ref':'observation','driver_entry_key':'1','target_episode_key':['observation','target']}}]}
        event=p.artifact('QualifyingPitEventArtifact',pit_visit_ref='visit')
        visit=dict(entry=entry,ordinal=3,service=service,completed=3,entry_ref='entry',qualifying_event=event)
        term=p.artifact('TerminalBoundary',bounds=[1300,1310],evidence_refs=['last-lap','stopped']) if terminal else None
        catalog=dict(artifact_id='catalog',source_snapshot_manifest_ref='source',coverage={'validated_capabilities':['pit-entry','terminal-bounds']},visits={'1':[visit]},terminal={'1':term})
        clock={'unhealthy':gaps or []}
        return p.resolve(init,[o],catalog,clock)['records'][0]
    def test_strict_entry_and_terminal_bounds(self):
        r=self.fixture();self.assertEqual(r['resolution_state'],'OBSERVED_EVENT')
        self.assertEqual(r['terminal_boundary']['evidence_refs'],['last-lap','stopped'])
        self.assertEqual(r['evidence_coverage']['status'],'COMPLETE')
        r=self.fixture(entry=1295)
        self.assertEqual(r['resolution_state'],'TRUNCATED_INDETERMINATE')
        self.assertIn('ENTRY_BOUNDARY_OVERLAP',r['truncation_reason_codes'])
    def test_missing_terminal_service_and_coverage_are_reasoned_truncations(self):
        for kw,reason in [({'terminal':False},'TERMINAL_EVIDENCE_MISSING'),
                          ({'service':'INDETERMINATE_TYRE_SERVICE'},'INDETERMINATE_TYRE_SERVICE'),
                          ({'gaps':[[1150,1160]]},'CLOCK_UNHEALTHY_COVERAGE_GAP')]:
            r=self.fixture(**kw);self.assertEqual(r['resolution_state'],'TRUNCATED_INDETERMINATE')
            self.assertIn(reason,r['truncation_reason_codes'])

if __name__=='__main__':
    unittest.main()
