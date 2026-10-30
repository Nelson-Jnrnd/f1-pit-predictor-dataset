import copy
import unittest
from pipeline.race_control_messages import variants, state_at, parent, replay
from pipeline._race_control_baseline import build_events, state_at as baseline_state_at

def inherited_checks():
 results=[]
 def check(n,v):assert v,n;results.append(dict(name=n,passed=True))
 C=dict(start=100.,end=600.);gaps=[dict(start=140,end=180,cause='sparse_lap_and_message_anchors')];T=dict(prefix=200.,ordinal=999,stream='TimingData')
 def msg(t,i,**m):
  m=dict(Utc=f'2000-01-01T00:{int(t)//60:02d}:{int(t)%60:02d}',**m)
  return dict(prefix=float(t),ordinal=i,stream='RaceControlMessages',ref=f'test:{i}',payload={'Messages':{str(i):m}})
 anchor=msg(110,0,Category='Other',Message='REFERENCE');dep=msg(130,1,Category='SafetyCar',Mode='SAFETY CAR',Status='DEPLOYED',Message='SAFETY CAR DEPLOYED');clear=msg(160,2,Category='Flag',Scope='Track',Flag='CLEAR',Message='TRACK CLEAR');end=msg(150,2,Category='SafetyCar',Mode='SAFETY CAR',Status='IN THIS LAP',Message='SAFETY CAR IN THIS LAP')
 E=lambda rs,life=[],cc=gaps:build_events(rs,life,C,cc)
 S=lambda rs,life=[],cc=gaps:baseline_state_at(T,E(rs,life,cc))
 base=S([anchor,dep])
 check('lap_gap_does_not_erase_report',base['state']=='SC_REPORTED')
 check('clearance_inside_lap_gap_processed',S([anchor,dep,clear])['state']=='CLEAR_REPORTED')
 check('ending_is_distinct',S([anchor,dep,end])['state']=='SC_ENDING_REPORTED')
 bad=copy.deepcopy(clear);bad['payload']['Messages']['2']['Utc']='2000-01-01T00:00:00'
 check('untrusted_clearance_invalidates',S([anchor,dep,bad])['state']=='UNKNOWN_MESSAGE_TIME')
 check('message_anchor_exclusion_preserved',S([anchor,dep,clear],cc=[dict(start=140,end=180,cause='legacy_out_of_band_message_anchor')])['state']=='UNKNOWN_MESSAGE_TIME')
 cold=msg(150,0,Category='SafetyCar',Mode='SAFETY CAR',Status='DEPLOYED',Message='SAFETY CAR DEPLOYED')
 check('no_anchor_cannot_rescue',S([cold])['state']=='UNKNOWN_MESSAGE_TIME')
 for name,delta in [('clearance',{'2':clear['payload']['Messages']['2']}),('ending',{'2':end['payload']['Messages']['2']}),('deletion',{'1':None}),('correction',{'1':{'Status':'CANCELLED'}})]:
  future=dict(prefix=250.,ordinal=2,stream='RaceControlMessages',ref='future:'+name,payload={'Messages':delta})
  check('future_'+name+'_state',S([anchor,dep,future])==base)
  check('future_'+name+'_earlier_gate',E([anchor,dep,future])[:2]==E([anchor,dep]))
 check('strict_margin_equal_excluded',baseline_state_at(dict(T,prefix=170.),E([anchor,dep,clear]))['state']=='SC_REPORTED')
 check('strict_margin_after_included',baseline_state_at(dict(T,prefix=170.001),E([anchor,dep,clear]))['state']=='CLEAR_REPORTED')
 pit=msg(160,2,Category='Flag',Scope='Track',Flag='GREEN',Message='GREEN LIGHT - PIT EXIT OPEN');local=msg(160,2,Category='Flag',Scope='Sector',Flag='CLEAR',Message='CLEAR IN TRACK SECTOR 2')
 check('pit_exit_does_not_clear',S([anchor,dep,pit])['state']=='SC_REPORTED')
 check('local_flag_does_not_clear',S([anchor,dep,local])['state']=='SC_REPORTED')
 reset=dict(prefix=150.,ordinal=0,stream='SessionStatus',ref='reset',payload={'Status':'Aborted'})
 check('session_reset_clears',S([anchor,dep],[reset])['state']=='UNKNOWN_SESSION_RESET')
 check('future_reset_unchanged',S([anchor,dep],[dict(reset,prefix=250.)])==base)
 idgap=msg(160,4,Category='Other',Message='OTHER')
 check('id_gap_invalidates_irrelevant_packet',S([anchor,dep,idgap])['state']=='UNKNOWN_MESSAGE_TIME')
 correction=dict(prefix=160.,ordinal=2,stream='RaceControlMessages',ref='corr',payload={'Messages':{'1':{'Status':'CANCELLED'}}});deletion=dict(correction,ref='del',payload={'Messages':{'1':None}})
 check('correction_invalidates',S([anchor,dep,correction])['projected']=='UNKNOWN')
 check('deletion_invalidates',S([anchor,dep,deletion])['projected']=='UNKNOWN')
 check('delayed_event_never_backdated',baseline_state_at(dict(T,prefix=150.),E([anchor,dep,bad]))['state']=='SC_REPORTED')
 worlds=[[anchor,dep],[anchor,dep,clear]];received=[[p for p in w if p['ref']!='test:2'] for w in worlds]
 check('distinct_loss_histories',worlds[0]!=worlds[1] and received[0]==received[1])
 check('lost_clearance_undetectable',S(received[0])==S(received[1]) and S(worlds[0])!=S(worlds[1]))
 check('no_completeness_claim',not S(received[1])['delivery_completeness_proven'])
 check('session_margin_equal_unknown',S([anchor,dep],[dict(reset,prefix=120.)])['state']=='UNKNOWN_MESSAGE_TIME')
 check('session_margin_inside_unknown',S([anchor,dep],[dict(reset,prefix=120.001)])['state']=='UNKNOWN_MESSAGE_TIME')
 check('session_margin_beyond_accepted',S([anchor,dep],[dict(reset,prefix=119.999)])['state']=='SC_REPORTED')
 check('correction_not_calibration',E([anchor,dep,correction])[-1]['time_quality']=='REVISION_PACKET')
 clear3=dict(clear,ordinal=3,payload={'Messages':{'3':clear['payload']['Messages']['2']}})
 check('rescued_not_calibration',E([anchor,dep,end,clear3])[-1]['earlier_anchor_refs']==['test:0','test:1'])
 vsc=msg(160,2,Category='SafetyCar',Mode='VIRTUAL SAFETY CAR',Status='DEPLOYED',Message='VIRTUAL SAFETY CAR DEPLOYED')
 check('mode_change_processed',S([anchor,dep,vsc])['state']=='VSC_REPORTED')
 check('future_utc_cannot_certify_past',E([anchor,dep,bad])[:2]==E([anchor,dep]))
 equal=msg(130,2,Category='Flag',Scope='Track',Flag='CLEAR',Message='TRACK CLEAR')
 check('equal_prefix_ordinal_order',S([anchor,dep,equal])['state']=='CLEAR_REPORTED')
 unseen=dict(correction,payload={'Messages':{'2':None}})
 check('unseen_deletion_invalidates_B',S([anchor,dep,unseen])['state']=='UNKNOWN_MESSAGE_TIME')
 check('unseen_deletion_invalidates_A',baseline_state_at(T,E([anchor,dep,unseen]),'A')['projected']=='UNKNOWN')
 partial=dict(correction,payload={'Messages':{'2':{'Status':'CANCELLED','Utc':'2000-01-01T00:02:40'}}})
 check('partial_new_identity_invalidates',S([anchor,dep,partial])['projected']=='UNKNOWN')
 return results

def run():
 inherited=inherited_checks();checks=[]
 def check(n,x):assert x,n;checks.append(dict(name=n,passed=True))
 C=dict(start=500.,end=1200.);gaps=[dict(start=640,end=680,cause='legacy_out_of_band_message_anchor')];T=dict(prefix=800.,ordinal=999,stream='TimingData')
 def msg(t,i,**x):
  v=dict(Utc=f'2000-01-01T00:{int(t)//60:02d}:{int(t)%60:02d}',**x);return dict(prefix=float(t),ordinal=i,stream='RaceControlMessages',ref=f'test:{i}',payload={'Messages':{str(i):v}})
 def life(t,status):return dict(prefix=float(t),ordinal=int(t),stream='SessionStatus',ref=f'life:{t}',payload={'Status':status})
 a=msg(110,0,Category='Other',Message='ANCHOR');b=msg(190,1,Category='Other',Message='ANCHOR');start=life(500,'Started');dep=msg(620,2,Category='SafetyCar',Mode='SAFETY CAR',Status='DEPLOYED',Message='SAFETY CAR DEPLOYED');clear=msg(660,3,Category='Flag',Scope='Track',Flag='CLEAR',Message='TRACK CLEAR');anchor=msg(710,4,Category='Other',Message='ANCHOR')
 E=lambda rs,ls=[start],cs=gaps:variants(rs,ls,C,cs)
 S=lambda rs,t=T,ls=[start],v='IT',cs=gaps:state_at(t,E(rs,ls,cs)[v],interpret=v in ('I','IT'),time_fixes=v in ('T','IT'))
 rows=[a,b,dep,clear,anchor]
 check('pending_clear_uncertain_before_anchor',S(rows,dict(T,prefix=700))['state']=='UNKNOWN_MESSAGE_TIME')
 check('release_waits_strict_margin',S(rows,dict(T,prefix=720))['state']=='UNKNOWN_MESSAGE_TIME')
 check('pending_clear_released_after_anchor',S(rows,dict(T,prefix=720.001))['state']=='CLEAR_REPORTED')
 check('release_records_later_availability',S(rows)['certificate']==dict(content_ref='test:3',availability_ref='test:4'))
 check('no_later_anchor_no_release',S(rows[:-1])['state']=='UNKNOWN_MESSAGE_TIME')
 check('future_anchor_cannot_rewrite_past',S(rows,dict(T,prefix=700))==S(rows[:-1],dict(T,prefix=700)))
 bad=copy.deepcopy(b);bad['payload']['Messages']['1']['Utc']='2000-01-01T00:00:00'
 cold=msg(550,2,Category='SafetyCar',Mode='SAFETY CAR',Status='DEPLOYED',Message='SAFETY CAR DEPLOYED');lap=[dict(start=540,end=580,cause='sparse_lap_and_message_anchors')]
 check('stable_prerace_seed_supports_early_deployment',S([a,b,cold],cs=lap)['state']=='SC_REPORTED')
 check('inconsistent_prerace_seed_refused',S([a,bad,cold],cs=lap)['state']=='UNKNOWN_MESSAGE_TIME')
 cold1=msg(550,1,Category='SafetyCar',Mode='SAFETY CAR',Status='DEPLOYED',Message='SAFETY CAR DEPLOYED')
 check('single_prerace_anchor_insufficient',S([a,cold1],cs=lap)['state']=='UNKNOWN_MESSAGE_TIME')
 check('prerace_seed_requires_300second_margin',S([msg(210,0,Category='Other',Message='LATE'),msg(220,1,Category='Other',Message='LATE'),cold],cs=lap)['state']=='UNKNOWN_MESSAGE_TIME')
 restart=msg(660,3,Category='Other',Message='SAFETY CAR WILL ENTER PITS: STANDING START')
 check('interpretation_recognises_restart',S([a,b,dep,restart],v='I',cs=[])['state']=='RESTART_INSTRUCTION_REPORTED')
 check('time_only_keeps_old_restart_meaning',S([a,b,dep,restart],v='T',cs=[])['state']=='UNKNOWN_RELEVANT_MESSAGE')
 check('restart_does_not_invent_normal_or_SC',S([a,b,dep,restart],cs=[])['projected']=='UNKNOWN' and not S([a,b,dep,restart],cs=[])['explicit_phase_report_available'])
 stopped=life(650,'Aborted');red=msg(651,3,Category='Flag',Scope='Track',Flag='RED',Message='RED FLAG')
 check('red_and_abort_compatible',S([a,b,dep,red],ls=[start,stopped],cs=[])['state']=='RED_REPORTED')
 check('compatible_requires_both_available',S([a,b,dep,red],dict(T,prefix=660),ls=[start,stopped],cs=[])['state']!='RED_REPORTED')
 redfirst=msg(649,3,Category='Flag',Scope='Track',Flag='RED',Message='RED FLAG')
 check('red_before_abort_preserved',S([a,b,dep,redfirst],ls=[start,stopped],cs=[])['state']=='RED_REPORTED')
 dep_near=msg(501,2,Category='SafetyCar',Mode='SAFETY CAR',Status='DEPLOYED',Message='SAFETY CAR DEPLOYED')
 check('deployment_started_tie_not_exempt',S([a,b,dep_near],cs=[])['state']=='UNKNOWN_MESSAGE_TIME')
 correction=dict(prefix=690.,ordinal=4,stream='RaceControlMessages',ref='corr',payload={'Messages':{'3':None}})
 fresh=msg(710,4,Category='Other',Message='FRESH')
 check('pending_deletion_barrier',S([a,b,dep,clear,correction,fresh])['state']!='CLEAR_REPORTED')
 check('session_barrier_discards_pending_clear',S(rows,ls=[start,life(690,'Aborted'),life(695,'Started')])['state']!='CLEAR_REPORTED')
 # Rebuilding a different source has no carried Python/global state.
 cold0=msg(550,0,Category='SafetyCar',Mode='SAFETY CAR',Status='DEPLOYED',Message='SAFETY CAR DEPLOYED')
 check('new_source_does_not_inherit_clock',S([cold0],cs=lap)['state']=='UNKNOWN_MESSAGE_TIME')
 for key in ['I','T','IT']:
  full=E(rows);cut=E(rows[:-1]);boundary=dict(T,prefix=700)
  check('future_anchor_'+key,state_at(boundary,full[key],key in ('I','IT'),key in ('T','IT'))==state_at(boundary,cut[key],key in ('I','IT'),key in ('T','IT')))
 partial=dict(prefix=660.,ordinal=3,stream='RaceControlMessages',ref='partial',payload={'Messages':{'3':{'Status':'CANCELLED','Utc':'2000-01-01T00:11:00'}}})
 for v in ['I','IT']:
  check('partial_identity_sentinel_'+v,S([a,b,dep,partial],v=v,cs=[])['projected']=='UNKNOWN')
 mixed=dict(prefix=110.,ordinal=0,stream='RaceControlMessages',ref='mixed',payload={'Messages':{'0':{'Category':'Other','Message':'A','Utc':'2000-01-01T00:01:40'},'1':{'Category':'Other','Message':'B','Utc':'2000-01-01T00:02:00'}}})
 second=msg(190,2,Category='Other',Message='C');early=msg(550,3,Category='SafetyCar',Mode='SAFETY CAR',Status='DEPLOYED',Message='SAFETY CAR DEPLOYED')
 check('all_seed_offsets_checked_not_packet_medians',S([mixed,second,early],cs=lap)['state']=='UNKNOWN_MESSAGE_TIME')
 return dict(inherited=inherited,added=checks)

class RaceControlTests(unittest.TestCase):
 def test_public_replay_delayed_release(self):
  def record(t, identity, message):
   return dict(prefix=float(t), ordinal=identity, stream="RaceControlMessages", ref=f"api:{identity}", payload={"Messages":{str(identity):dict(Utc=f"2000-01-01T00:{t//60:02d}:{t%60:02d}", **message)}})
  rows=[record(110,0,dict(Category="Other",Message="ANCHOR")), record(130,1,dict(Category="SafetyCar",Mode="SAFETY CAR",Status="DEPLOYED",Message="SAFETY CAR DEPLOYED")), record(160,2,dict(Category="Flag",Scope="Track",Flag="CLEAR",Message="TRACK CLEAR")),record(190,3,dict(Category="Other",Message="ANCHOR"))]
  clock=dict(start=100.,end=600.); causes=[dict(start=150,end=170,cause="legacy_out_of_band_message_anchor")]
  for prefix in (180.,200.,200.001):
   boundary=dict(prefix=prefix,ordinal=999,stream="TimingData")
   expected=state_at(boundary,variants(rows,[],clock,causes)["IT"],interpret=True,time_fixes=True)
   self.assertEqual(replay(boundary,rows,[],clock,causes),expected)
  self.assertEqual(replay(dict(prefix=200.,ordinal=999,stream="TimingData"),rows,[],clock,causes)["state"],"UNKNOWN_MESSAGE_TIME")
  released=replay(dict(prefix=200.001,ordinal=999,stream="TimingData"),rows,[],clock,causes)
  self.assertEqual(released["state"],"CLEAR_REPORTED")
  self.assertEqual(released["certificate"],dict(content_ref="api:2",availability_ref="api:3"))

 def test_registered_cases(self):
  result=run()
  self.assertEqual(len(result["inherited"]),38)
  self.assertEqual(len(result["added"]),26)

if __name__=="__main__": unittest.main()
