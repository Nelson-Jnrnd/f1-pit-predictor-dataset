"""Finite diagnostic fixes. No edits to the sealed parent implementation."""
import copy
import statistics
from . import _race_control_baseline as parent
utc=parent.utc
LAP_CAUSES=parent.LAP_CAUSES
RESTART={'SAFETY CAR WILL ENTER PITS: STANDING START':'standing','SAFETY CAR WILL ENTER PITS: ROLLING START':'rolling','SAFETY CAR WILL ENTER PITS: ROLLING START PROCEDURE':'rolling'}
def meaning(m,explicit=False):
 if explicit and isinstance(m,dict) and m.get('Category')=='Other' and ' '.join(str(m.get('Message','')).split()) in RESTART:return 'RESTART_INSTRUCTION_REPORTED'
 return parent.meaning(m,explicit)

def build_time_events(rcm,lifecycle,clock,causes):
 sessions=[];last=object()
 for r in lifecycle:
  if 'Status' in r['payload'] and r['payload']['Status']!=last:sessions.append(r);last=r['payload']['Status']
 items=[(r['prefix'],0,r) for r in sessions]+[(r['prefix'],1,r) for r in rcm];items.sort(key=lambda x:(x[0],x[1],x[2]['ordinal']))
 anchors=[];cat={};nextid=0;episode=None;episode_prefix=None;events=[];pre=[]
 for p,kind,r in items:
  if kind==0:
   
   if p==clock['start'] and len({ref for ref,_ in pre})>=2 and max(v for _,v in pre)-min(v for _,v in pre)<=1.9:anchors=list(pre)
   episode=r['ref'];episode_prefix=p;events.append(dict(prefix=p,ordinal=r['ordinal'],stream=r['stream'],ref=r['ref'],kind='session',session_status=r['payload']['Status'],time_quality='SESSION_RESET_ONLY'));continue
  ms=r['payload'].get('Messages',{});ms={str(i):v for i,v in enumerate(ms)} if isinstance(ms,list) else ms
  malformed=not isinstance(ms,dict);gap=False;revision=False;changes=[];offsets=[]
  if not malformed:
   for identity,delta in ms.items():
    identity=str(identity);before=cat.get(identity);existed=identity in cat
    if not identity.isdigit():malformed=True;changes.append(dict(identity=identity,kind='invalid_identity',A='UNKNOWN',B='UNKNOWN'));continue
    if not existed:
     if int(identity)!=nextid:gap=True
     nextid=max(nextid,int(identity)+1)
    if delta is None:
     revision=True;cat[identity]=None
     if not existed or before is None:changes.append(dict(identity=identity,kind='unresolved_deletion',A='UNKNOWN',B='UNKNOWN'))
     elif parent.meaning(before) is not None or parent.meaning(before,True) is not None:changes.append(dict(identity=identity,kind='deletion',A='UNKNOWN',B='UNKNOWN',old_message=before))
     continue
    if not isinstance(delta,dict):malformed=True;cat[identity]=None;changes.append(dict(identity=identity,kind='malformed',A='UNKNOWN',B='UNKNOWN'));continue
    merged=dict(before) if isinstance(before,dict) else {};merged.update(delta);cat[identity]=merged;a=parent.meaning(merged);b=parent.meaning(merged,True)
    if existed:
     if merged!=before:
      revision=True
      if a is not None or b is not None or parent.meaning(before) is not None or parent.meaning(before,True) is not None:changes.append(dict(identity=identity,kind='correction',A='UNKNOWN',B='UNKNOWN',message=merged,old_message=before))
    elif a is not None or b is not None or 'Category' not in merged:changes.append(dict(identity=identity,kind='new',A=a if 'Category' in merged else 'UNKNOWN',B=b if 'Category' in merged else 'UNKNOWN',message=merged))
    if not existed:
     try:offsets.append(utc(merged['Utc'])-p)
     except (KeyError,ValueError,TypeError,AttributeError):offsets.append(None)
  cs=sorted({c['cause'] for c in causes if c['start']<=p<=c['end']});median=statistics.median([v for _,v in anchors]) if anchors else None
  if malformed:q='MALFORMED_PACKET'
  elif gap:q='MESSAGE_ID_GAP'
  elif episode_prefix is not None and p<=episode_prefix+10:q='SESSION_TIME_TIE'
  elif revision:q='REVISION_PACKET'
  elif not clock['start']<=p<=clock['end']:q='OUTSIDE_RACE'
  elif not offsets or any(o is None for o in offsets):q='MISSING_OR_BAD_UTC'
  elif not cs:q='ORIGINAL_HEALTHY'
  elif not set(cs)<=LAP_CAUSES:q='MESSAGE_ANCHOR_EXCLUDED'
  elif median is None:q='NO_EARLIER_TRUSTED_MESSAGE'
  elif all(-1.2<=o-median<=.7 for o in offsets):q='LAP_GAP_UTC_SUPPORTED'
  else:q='MESSAGE_UTC_DISAGREES'
  events.append(dict(prefix=p,ordinal=r['ordinal'],stream=r['stream'],ref=r['ref'],kind='message',changes=changes,time_quality=q,usable=q in ('ORIGINAL_HEALTHY','LAP_GAP_UTC_SUPPORTED'),source_causes=cs,prior_anchor_median=median,earlier_anchor_refs=[ref for ref,_ in anchors],message_offsets=offsets,offset_deviations=[None if median is None or o is None else o-median for o in offsets],episode_ref=episode,malformed=malformed,identity_gap=gap))
  if p+300<clock['start']-5 and not malformed and not gap and not revision and offsets and all(o is not None for o in offsets):pre.extend((r['ref'],value) for value in offsets)
  if q=='ORIGINAL_HEALTHY':anchors.append((r['ref'],statistics.median(offsets)))
  if malformed or gap:anchors=[]
 return events


def original_events(rcm,life,clock,causes):return parent.build_events(rcm,life,clock,causes)
def interpret_events(events):
 out=copy.deepcopy(events)
 for e in out:
  for c in e.get('changes',[]):
   if c['kind']=='new' and isinstance(c.get('message'),dict) and c['message'].get('Category')=='Other' and ' '.join(str(c['message'].get('Message','')).split()) in RESTART:c['B']='RESTART_INSTRUCTION_REPORTED'
 return out

def state_at(T,events,interpret=False,time_fixes=False):
 state='NO_STATUS_REPORTED';reason='no_status_message';certificate=None;last=None;pending=[];last_red=None;last_session=None;released=[]
 def apply(e,availability_ref=None):
  nonlocal state,reason,certificate,last,last_red
  acts=[c['B'] for c in e['changes'] if c['B'] is not None]
  if not acts and not e['malformed'] and not e['identity_gap']:return
  last=e['ref'];basis=availability_ref or e['ref']
  if len(set(acts))!=1:state='UNKNOWN_CONFLICT';reason='conflicting_packet';certificate=None;return
  a=acts[0]
  if a in ('SC_ANNOUNCED','VSC_ANNOUNCED'):
   state={'SC_ANNOUNCED':'SC_REPORTED','VSC_ANNOUNCED':'VSC_REPORTED'}[a];reason='deployment';certificate=dict(content_ref=e['ref'],availability_ref=basis)
  elif a in ('KEEP_SC','END_SC','END_VSC'):
   expected='VSC_ANNOUNCED' if a=='END_VSC' else 'SC_ANNOUNCED'
   if parent.project(state)==expected and certificate:
    if a.startswith('END_'):state='VSC_ENDING_REPORTED' if a=='END_VSC' else 'SC_ENDING_REPORTED'
    reason='ending_reported' if a.startswith('END_') else 'continuation_reported'
   else:state='UNKNOWN_UNMATCHED_MESSAGE';reason='ending_or_continuation_without_trusted_deployment';certificate=None
  elif a in ('CLEAR_REPORTED','RED_REPORTED','FINISH_REPORTED','RESTART_INSTRUCTION_REPORTED'):
   state=a;reason='restart_instruction_only' if a=='RESTART_INSTRUCTION_REPORTED' else 'direct_report';certificate=dict(content_ref=e['ref'],availability_ref=basis)
   if a=='RED_REPORTED':last_red=e
  else:state='UNKNOWN_RELEVANT_MESSAGE';reason='unsupported_or_corrected_relevant_message';certificate=None
 for e in events:
  if e['prefix']>T['prefix']:break
  if not parent.visible(e,T):continue
  if e['kind']=='session':
   compatible=time_fixes and e['session_status']=='Aborted' and state=='RED_REPORTED' and last_red is not None and abs(e['prefix']-last_red['prefix'])<=10
   pending=[];last_session=e
   if compatible:reason='red_and_abort_compatible';continue
   state='NO_STATUS_REPORTED' if e['session_status']=='Started' else 'UNKNOWN_SESSION_RESET';reason='session_transition';certificate=None;last=e['ref'];continue
  relevant=any(c['B'] is not None for c in e['changes']) or e['malformed'] or e['identity_gap']
  if time_fixes and e['usable']:
   for saved in pending:
    apply(saved,e['ref']);released.append(dict(content_ref=saved['ref'],availability_ref=e['ref']))
   pending=[]
  red=any(c['B']=='RED_REPORTED' for c in e['changes'])
  compatible=time_fixes and red and e['time_quality']=='SESSION_TIME_TIE' and last_session is not None and last_session['session_status']=='Aborted' and abs(e['prefix']-last_session['prefix'])<=10 and e['prior_anchor_median'] is not None and e['message_offsets'] and all(v is not None and -1.2<=v-e['prior_anchor_median']<=.7 for v in e['message_offsets'])
  if e['usable'] or compatible:
   apply(e)
   if compatible:reason='red_and_abort_compatible'
   continue
  if time_fixes and e['time_quality']=='REVISION_PACKET':pending=[]
  if not relevant:continue
  state='NO_STATUS_REPORTED' if e['time_quality']=='OUTSIDE_RACE' else 'UNKNOWN_MESSAGE_TIME';reason=e['time_quality'].lower();certificate=None;last=e['ref']
  if time_fixes:
   if e['malformed'] or e['identity_gap'] or any(c['kind']!='new' for c in e['changes']):pending=[]
   elif e['time_quality'] in ('MESSAGE_ANCHOR_EXCLUDED','MESSAGE_UTC_DISAGREES','NO_EARLIER_TRUSTED_MESSAGE'):pending.append(e)
 restart_mode=None
 if state=='RESTART_INSTRUCTION_REPORTED':
  for event in events:
   if event['ref']==last:
    for change in event.get('changes',[]):
     message=change.get('message',{});restart_mode=RESTART.get(' '.join(str(message.get('Message','')).split()),restart_mode)
 current_known=not state.startswith('UNKNOWN') and state not in ('NO_STATUS_REPORTED','RESTART_INSTRUCTION_REPORTED')
 return dict(state=state,projected=parent.project(state),reason=reason,certificate=certificate,restart_mode=restart_mode,supporting_session_ref=last_session['ref'] if reason=='red_and_abort_compatible' and last_session else None,last_relevant_ref=last,released=released,last_report_understood=not state.startswith('UNKNOWN'),explicit_phase_report_available=current_known,meaning='last_reported_information',delivery_completeness_proven=False)

def variants(rcm,life,clock,causes):
 old=original_events(rcm,life,clock,causes);timed=build_time_events(rcm,life,clock,causes)
 return dict(I=interpret_events(old),T=timed,IT=interpret_events(timed))


def replay(boundary, rcm, lifecycle, clock, causes):
 """Return last reported information, using the combined verified handler.

 Records must be ordered archived packets with prefix/ordinal/stream/ref/payload.
 The caller supplies admitted clock bounds and exclusion causes. No source
 acquisition, physical-status guarantee or model feature admission is implied.
 """
 return state_at(boundary, interpret_events(build_time_events(rcm, lifecycle, clock, causes)), interpret=True, time_fixes=True)
