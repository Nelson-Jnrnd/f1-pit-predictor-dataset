import copy
import gzip
import hashlib
import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np
from pipeline import development as d
from pipeline import comparison_data as data
from pipeline import comparison_models as m
from pipeline import comparison as c


def observation(lap=2):
    return dict(semantic_observation_key=['2025-R1-R','1',lap],selected_driver_completed_laps=lap,
                canonical_state=dict(timing={'1':{}},tyres={'1':{}},distance={'TotalLaps':20}))


class DataTests(unittest.TestCase):
    def test_final_source_refused_before_read(self):
        with patch.object(Path,'read_bytes',side_effect=AssertionError('Forbidden read')):
            with self.assertRaisesRegex(ValueError,'Protected'):
                data.acquire_race(dict(season=2026,round=1),Path('/missing'))
            with self.assertRaisesRegex(ValueError,'Protected'):
                data.reconstruct_race(dict(season=2026,round=1),Path('/missing'),Path('/missing'))
    def test_final_target_refused_before_read_or_ledger(self):
        with patch.object(Path,'read_bytes',side_effect=AssertionError('Forbidden read')):
            with self.assertRaisesRegex(ValueError,'Protected'):
                c.open_race(Path('/missing'),dict(season=2026,round=1),Path('/missing/ledger'),'DEVELOPMENT_JOIN',1)
    def test_cutoff_before_read(self):
        with patch.object(Path,'read_bytes',side_effect=AssertionError('Read after cutoff')):
            with self.assertRaisesRegex(ValueError,'cutoff'):
                c.open_race(Path('/missing'),dict(season=2025,round=1,date='2025-03-16'),Path('/missing'),'DEVELOPMENT_JOIN',1,'2025-03-16')
    def test_endpoint_resume_uses_existing_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); folder=root/'2025-01'; folder.mkdir()
            for feed in d.FEEDS:
                raw=b'frozen'; (folder/(feed+'.jsonStream.gz')).write_bytes(gzip.compress(raw))
                data.write_json(folder/(feed+'.metadata.json'),dict(sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw)))
            with patch.object(data,'fetch',side_effect=AssertionError('Redownload')),patch.object(d,'read_source'):
                result=data.acquire_race(dict(season=2025,round=1,path='2025/path/'),root)
            self.assertEqual(result['status'],'FROZEN')
    def test_corrupt_resume_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); folder=root/'2025-01';folder.mkdir()
            feed=sorted(d.FEEDS)[0]
            (folder/(feed+'.jsonStream.gz')).write_bytes(gzip.compress(b'changed'))
            data.write_json(folder/(feed+'.metadata.json'),dict(sha256='wrong',bytes=7))
            with self.assertRaisesRegex(ValueError,'hash'):
                data.acquire_race(dict(season=2025,round=1,path='unused'),root)
    def test_network_attempts_bounded(self):
        with patch('urllib.request.urlopen',side_effect=TimeoutError()),patch.object(data.time,'sleep') as sleep:
            with self.assertRaises(TimeoutError): data.fetch('https://example.test',timeout=2,attempts=3)
            self.assertEqual(sleep.call_count,2)
    def test_restart_stopped_is_not_terminal(self):
        def r(feed,n,p,payload):return dict(stream=feed,ordinal=n,prefix=p,payload=payload,ref=f'{feed}:{n}')
        records={'TimingData':[r('TimingData',0,1100,{'Lines':{'1':{'NumberOfLaps':1}}}),
                               r('TimingData',1,1400,{'Lines':{'1':{'Stopped':True}}})],
                 'SessionStatus':[r('SessionStatus',0,1000,{'Status':'Started'}),r('SessionStatus',1,1600,{'Status':'Started'}),r('SessionStatus',2,2000,{'Status':'Finished'})],
                 'TimingAppData':[r('TimingAppData',0,900,{'Lines':{}})]}
        catalog=d.retrospective_catalog(records,dict(start=1000,end=2000,unhealthy=[]),dict(artifact_id='source'),allow_restarts=True)
        self.assertIsNone(catalog['terminal']['1'])
    def test_tyre_fallback_uses_causal_entry_and_update(self):
        o=observation(); tyre=o['canonical_state']['tyres']['1']
        tyre.update(Stints={'0':{'Compound':'SOFT','TotalLaps':4}},_last_stint_update={'prefix':100,'ref':'tyre'})
        self.assertEqual(data.tyre_view(o)['age'],4)
        o['canonical_state']['timing']['1']['_last_pit_entry']={'prefix':101,'ref':'pit'}
        self.assertIn('fallback',data.tyre_view(o))
        tyre['_last_stint_update']['prefix']=120
        self.assertNotIn('fallback',data.tyre_view(o))
        tyre['Stints']['0']['TyresNotChanged']='1'
        self.assertEqual(data.tyre_view(o)['fallback'],'TYRES_NOT_CHANGED')
    def test_future_tyres_do_not_enter_reducer(self):
        def r(n,p,a): return dict(stream='TimingAppData',ordinal=n,prefix=p,ref=f'tyre:{n}',payload={'Lines':{'1':{'Stints':{'0':{'TotalLaps':a,'Compound':'SOFT'}}}}})
        reducer=data.TyreReducer([r(0,1050,2),r(1,1150,10)],dict(start=1000,end=2000,unhealthy=[]),True)
        state,_=reducer.at(dict(stream='TimingData',prefix=1100,ordinal=9))
        self.assertEqual(state['1']['Stints']['0']['TotalLaps'],2)
        self.assertEqual(state['1']['_last_stint_update']['prefix'],1050)


class ModelTests(unittest.TestCase):
    def test_percentage_width_changes_per_lap_rate(self):
        model=dict(id='PERCENT_AHEAD',rates=[2.]*10,q_open=.5,floor=0.)
        a=m.predict(model,dict(L=0,N_T=50,K_T=50),{},None)
        b=m.predict(model,dict(L=0,N_T=100,K_T=100),{},None)
        self.assertAlmostEqual(a['event_region_probabilities'][0],1-np.exp(-2/50))
        self.assertAlmostEqual(b['event_region_probabilities'][0],1-np.exp(-2/100))
    def test_boundary_overlap_integrates_both_bins(self):
        widths=m.exposure(dict(L=0,N_T=17),1)
        self.assertAlmostEqual(sum(widths),1/17)
        self.assertGreater(widths[0],0);self.assertGreater(widths[1],0)
    def test_progress_uses_completed_laps(self):
        g=dict(L=50,N_T=100,K_T=50)
        self.assertEqual(np.argmax(m.exposure(g,0,False)),0)
        self.assertEqual(np.argmax(m.exposure(g,0,True)),5)
    def test_complete_floor_and_open_final_region(self):
        for g in (dict(L=0,N_T=100,K_T=100),dict(L=100,N_T=100,K_T=1)):
            out=m.canonical([.03]*(g['K_T']-1),1.,g)
            values=out['event_region_probabilities']+[out['terminal_no_event_probability']]
            self.assertAlmostEqual(sum(values),1.);self.assertTrue(all(v>=1e-6 for v in values))
    def test_missing_percentage_support_and_b0_support(self):
        g=dict(L=0,N_T=100,K_T=100)
        with self.assertRaisesRegex(ValueError,'exposure'):
            m.predict(dict(id='PERCENT_AHEAD',rates=[None]*10,q_open=1.,floor=1e-6),g,{},None)
        with self.assertRaisesRegex(ValueError,'support'):
            m.predict(dict(id='B0',hazards=[None]*41,q_open=1.,floor=1e-6),g,{},None)
    def test_b1_fallback_does_not_impute(self):
        b0=dict(id='B0',hazards=[.1]*41,q_open=.5,floor=1e-6)
        g=dict(L=5,N_T=10,K_T=5)
        self.assertEqual(m.predict(dict(id='B1',fit_failure='no fit'),g,{'fallback':'STINT_MISSING'},b0),m.predict(b0,g,{},b0))
    def test_logistic_fit_and_separated_fit_policy(self):
        beta,_=m.logistic_fit([[1],[1],[1],[1]],[0,0,0,1])
        self.assertAlmostEqual(float(1/(1+np.exp(-beta[0]))),.25,places=6)
        with self.assertRaisesRegex(ValueError,'separated'):
            m.logistic_fit([[1,0],[1,1]],[0,1])
        with self.assertRaisesRegex(ValueError,'both outcome'):
            m.logistic_fit([[1],[1]],[1,1])
    def test_inference_does_not_accept_outcomes(self):
        import inspect
        self.assertEqual(list(inspect.signature(m.predict).parameters),['model','grid','tyre','b0'])
        self.assertNotIn('labels',inspect.signature(c.forecasts).parameters)
    def test_forecast_cutoff_and_failed_attempt_retained(self):
        row=dict(key=['2025-R1-R','1',0],observation_ref='obs',attempt_status='VALID',eligibility='ELIGIBLE',episode_ref='ep',initialization_run_ref='init',target_episode_key=['obs','target'],
                 grid=dict(L=0,N_T=100,K_T=100),tyre=dict(fallback='missing'))
        models={name:dict(id=name,artifact_id=name,cutoff='2025-03-16',hazards=[None]*41,q_open=1,floor=1e-6,fit_failure='unsupported',k_terciles=[10,20]) for name in m.IDS}
        self.assertTrue(all(r['category']=='A4' for r in c.forecasts([row],models,'2025-03-16','run')))
        with self.assertRaisesRegex(ValueError,'cutoff'):c.forecasts([row],models,'2025-03-15','run')
    def test_secondary_intersection_reports_unmatched(self):
        rows=[]
        for name in m.IDS:
            rows.append(dict(model=name,key=['race','1',0],phase='0',category='A4',failure='missing'))
        result=c.comparison_summary(rows)
        self.assertIsNone(result['selected']);self.assertEqual(result['pairs']['B0 vs B1']['analysis_class'],'SECONDARY')
    def test_cluster_uncertainty_is_deterministic(self):
        values=[('a',1.),('a',2.),('b',3.),('b',4.)]
        self.assertEqual(c.uncertainty(values),c.uncertainty(values))
        self.assertTrue(c.uncertainty(values)['descriptive_only'])
        self.assertAlmostEqual(c.uncertainty(values)['mean'],2.5)


class ReviewRegressionTests(unittest.TestCase):
    def fixture(self):
        row=dict(key=['2025-R1-R','1',0],observation_ref='obs',attempt_status='VALID',eligibility='ELIGIBLE',episode_ref='ep',
                 initialization_run_ref='init',target_episode_key=['obs','target'],grid=dict(L=0,N_T=3,K_T=3),tyre={'fallback':'missing'})
        models={name:dict(id='B0',artifact_id=name,cutoff='2025-03-16',hazards=[.1]*41,q_open=.5,floor=1e-6,k_terciles=[2,5]) for name in m.IDS}
        labels={tuple(row['key']):dict(observation_ref='obs',episode_ref='ep',initialization_run_ref='init',target_episode_key=['obs','target'],
                                     resolution_run_ref='resolution',outcome=dict(kind='REALIZED_NO_EVENT'),reasons=[])}
        return c.forecasts([row],models,'2025-03-16','run'),labels
    def test_common_missing_resolvable_unit_blocks_selection(self):
        forecasts,labels=self.fixture(); scored=c.join_scores(forecasts,labels,'resolution')
        for name in m.IDS:
            scored.append(dict(key=['2025-R1-R','1',1],model=name,phase='0',category='A4',failure='unsupported',
                               label_kind='REALIZED_REGION',expected_cohort=True))
        result=c.comparison_summary(scored)
        self.assertIsNone(result['selected'])
        self.assertTrue(all(p['analysis_class']=='SECONDARY' and p['expected_cohort']==2 for p in result['pairs'].values()))
    def test_wrong_episode_run_and_target_key_are_linkage_defects(self):
        forecasts,labels=self.fixture()
        for field in ('episode_ref','initialization_run_ref','target_episode_key','resolution_run_ref'):
            bad=copy.deepcopy(labels);bad[next(iter(bad))][field]='wrong'
            rows=c.join_scores(forecasts,bad,'resolution')
            self.assertTrue(all(r['category']=='A0' and 'score' not in r for r in rows),field)
    def test_missing_declared_resolution_run_is_not_scored(self):
        forecasts,labels=self.fixture()
        self.assertTrue(all(r['category']=='A0' for r in c.join_scores(forecasts,labels)))
    def test_no_event_and_event_diagnostics_cover_both(self):
        forecasts,labels=self.fixture()
        noevent=c.join_scores(forecasts,labels,'resolution')
        labels[next(iter(labels))]['outcome']=dict(kind='REALIZED_REGION',j=1)
        event=c.join_scores(forecasts,labels,'resolution')
        for row in event: row['key']=['2025-R1-R','2',0]
        for row in noevent: row['key']=['2025-R1-R','1',0]
        result=c.comparison_summary(noevent+event)
        for summary in result['models'].values():
            self.assertEqual(summary['event_only_randomized_pit']['n'],1)
            self.assertEqual(sum(summary['event_only_randomized_pit']['counts']),1)
            self.assertEqual(summary['truncation']['overall']['n'],2)
    def test_truncation_weighting_and_empty_stratum_reported(self):
        rows=[dict(category='A9',key=['race','1',0],phase='0',k_tercile=0,score=2.),
              dict(category='A6',key=['race','2',0],phase='0',k_tercile=0),
              dict(category='A6',key=['race','3',0],phase='1',k_tercile=1)]
        out=c.truncation_diagnostics(rows)
        self.assertEqual(out['overall']['share'],2/3)
        self.assertEqual(out['inverse_resolvable_share']['mean_log_score'],2.)
        self.assertEqual(out['inverse_resolvable_share']['empty_strata'],[['race',1]])
    def test_quasi_separation_is_refused(self):
        with self.assertRaisesRegex(ValueError,'separated'):
            m.logistic_fit([[1,0],[1,0],[1,1]],[0,1,1])

class PackingTests(unittest.TestCase):
    def test_lossless_packing_and_resume_hash_checks(self):
        from pipeline.comparison_pack import pack_race
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);src=root/'source';out=root/'output';folder=src/'2025-01';folder.mkdir(parents=True)
            race=dict(season=2025,round=1,session='R')
            ep=d.artifact('TargetEpisodeInitialization',target_episode_key=['obs','target'])
            init=d.artifact('TargetInitializationRun',records=[dict(observation_artifact_ref='obs',initialization=ep)])
            resolution=d.artifact('ResolutionRun',target_initialization_run_ref=init['artifact_id'],records=[d.artifact('TargetResolutionArtifact',observation_artifact_ref='obs',target_episode_key=['obs','target'])])
            values=dict(initializations=init,resolutions=resolution,observations={'immutable':'same bytes'},
                        checkpoints=[dict(observation_ref='obs')],labels=[dict(observation_ref='obs')])
            hashes={}
            for name,value in values.items():
                filename=name+'.json.gz';data.write_json(folder/filename,value,True);hashes[filename]=hashlib.sha256((folder/filename).read_bytes()).hexdigest()
            data.write_json(folder/'manifest.json',dict(race=race,status='RECONSTRUCTED',hashes=hashes))
            result=pack_race(race,src,out)
            self.assertEqual(data.read_json(out/'2025-01/observations.json.xz',True),values['observations'])
            self.assertEqual(pack_race(race,src,out),result)
            (out/'2025-01/labels.json.gz').write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError,'corrupted'):pack_race(race,src,out)

class ValidityTests(unittest.TestCase):
    fixture = ReviewRegressionTests.fixture
    def test_any_slot_mapping_defect_blocks_primary_pair(self):
        forecasts,labels=self.fixture();rows=c.join_scores(forecasts,labels,'resolution')
        rows.append(dict(key=['2025-R1-R','1',1],model='B1',phase='0',category='A8'))
        result=c.comparison_summary(rows)
        self.assertIsNone(result['selected'])
        self.assertTrue(all(v['analysis_class']=='SECONDARY' for v in result['pairs'].values()))

if __name__=='__main__':unittest.main()
