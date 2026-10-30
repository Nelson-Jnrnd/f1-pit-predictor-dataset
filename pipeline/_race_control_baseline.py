"""Experimental last-reported status with message-specific timing checks."""
import statistics,copy
import datetime
PROCEDURES={'SAFETY CAR WILL ENTER PITS: STANDING START','SAFETY CAR WILL ENTER PITS: ROLLING START PROCEDURE','SAFETY CAR WILL ENTER PITS: ROLLING START','THE SAFETY CAR WILL STAY OUT FOR 2 LAPS','RACE WILL START BEHIND THE SAFETY CAR','FORMATION LAP WILL BE STARTED BEHIND THE SAFETY CAR','FORMATION LAPS WILL COMMENCE ON TIME AT 15:10 BEHIND THE SAFETY CAR'}
def action(message):
    """Return a claim/reset, or None for an irrelevant message."""
    if not isinstance(message,dict):return 'UNKNOWN'
    k=(message.get('Category'),message.get('Mode'),message.get('Status'),' '.join(str(message.get('Message','')).split()))
    if k==('SafetyCar','SAFETY CAR','THROUGH THE PIT LANE','SAFETY CAR THROUGH THE PIT LANE'):return 'KEEP_SC'
    if k==('SafetyCar','SAFETY CAR','IN THIS LAP','SAFETY CAR IN THIS LAP'):return 'END_SC'
    if k==('SafetyCar','VIRTUAL SAFETY CAR','ENDING','VIRTUAL SAFETY CAR ENDING'):return 'END_VSC'
    if k[0]=='Other' and k[3]=='THE SAFETY CAR WILL STAY OUT FOR 2 LAPS':return 'KEEP_SC'
    text=' '.join(str(message.get('Message','')).split())
    if message.get('Category')=='SafetyCar':
        if message.get('Status')=='DEPLOYED':
            if message.get('Mode')=='SAFETY CAR' and text=='SAFETY CAR DEPLOYED':return 'SC_ANNOUNCED'
            if message.get('Mode')=='VIRTUAL SAFETY CAR' and text=='VIRTUAL SAFETY CAR DEPLOYED':return 'VSC_ANNOUNCED'
        return 'UNKNOWN'
    if message.get('Category')=='Flag' and message.get('Scope')=='Track':
        if message.get('Flag') not in ('YELLOW','DOUBLE YELLOW'):return 'UNKNOWN'
    if text in PROCEDURES:return 'UNKNOWN'
    return None

def utc(s):
 return datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=datetime.timezone.utc).timestamp()
LAP_CAUSES={'sparse_lap_and_message_anchors','legacy_single_driver_lap_residual','multiple_driver_lap_residual'}
POS={'SC_REPORTED':'SC_ANNOUNCED','SC_ENDING_REPORTED':'SC_ANNOUNCED','VSC_REPORTED':'VSC_ANNOUNCED','VSC_ENDING_REPORTED':'VSC_ANNOUNCED'}
def meaning(m,explicit=False):
 if not isinstance(m,dict):return 'UNKNOWN'
 text=' '.join(str(m.get('Message','')).split());k=(m.get('Category'),m.get('Scope'),m.get('Flag'),text)
 if explicit:
  if k==('Flag','Track','GREEN','GREEN LIGHT - PIT EXIT OPEN'):return None
  if k==('Flag','Track','CLEAR','TRACK CLEAR'):return 'CLEAR_REPORTED'
  if k==('Flag','Track','RED','RED FLAG'):return 'RED_REPORTED'
  if k==('Flag','Track','CHEQUERED','CHEQUERED FLAG'):return 'FINISH_REPORTED'
 return action(m)
def build_events(rcm,lifecycle,clock,causes):
 sessions=[];last=object()
 for r in lifecycle:
  if 'Status' in r['payload'] and r['payload']['Status']!=last:sessions.append(r);last=r['payload']['Status']
 items=[(r['prefix'],0,r) for r in sessions]+[(r['prefix'],1,r) for r in rcm];items.sort(key=lambda x:(x[0],x[1],x[2]['ordinal']))
 anchors=[];cat={};nextid=0;episode=None;episode_prefix=None;events=[]
 for p,kind,r in items:
  if kind==0:
   anchors=[];episode=r['ref'];episode_prefix=p;events.append(dict(prefix=p,ordinal=r['ordinal'],stream=r['stream'],ref=r['ref'],kind='session',session_status=r['payload']['Status'],time_quality='SESSION_RESET_ONLY'));continue
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
     elif meaning(before) is not None or meaning(before,True) is not None:changes.append(dict(identity=identity,kind='deletion',A='UNKNOWN',B='UNKNOWN',old_message=before))
     continue
    if not isinstance(delta,dict):malformed=True;cat[identity]=None;changes.append(dict(identity=identity,kind='malformed',A='UNKNOWN',B='UNKNOWN'));continue
    merged=dict(before) if isinstance(before,dict) else {};merged.update(delta);cat[identity]=merged;a=meaning(merged);b=meaning(merged,True)
    if existed:
     if merged!=before:
      revision=True
      if a is not None or b is not None or meaning(before) is not None or meaning(before,True) is not None:changes.append(dict(identity=identity,kind='correction',A='UNKNOWN',B='UNKNOWN',message=merged,old_message=before))
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
  if q=='ORIGINAL_HEALTHY':anchors.append((r['ref'],statistics.median(offsets)))
  if malformed or gap:anchors=[]
 return events
def visible(e,T):
 if e['stream']==T['stream']:return e['prefix']<=T['prefix'] and e['ordinal']<=T['ordinal']
 return e['prefix']+10<T['prefix']
def project(state):return POS.get(state,state if state in ('SC_ANNOUNCED','VSC_ANNOUNCED') else 'UNKNOWN')
def state_at(T,events,variant='B',reference=False):
 state='NO_STATUS_REPORTED' if variant=='B' else 'UNKNOWN';reason='no_status_message';cert=None;last=None
 for e in events:
  if e['prefix']>T['prefix']:break
  if not reference and not visible(e,T):continue
  if e['kind']=='session':
   state=('NO_STATUS_REPORTED' if e['session_status']=='Started' else 'UNKNOWN_SESSION_RESET') if variant=='B' else 'UNKNOWN';reason='session_transition';cert=None;last=e['ref'];continue
  acts=[c[variant] for c in e['changes'] if c[variant] is not None]
  if not acts and not e['malformed'] and not e['identity_gap']:continue
  last=e['ref']
  if not e['usable']:
   state=('NO_STATUS_REPORTED' if e['time_quality']=='OUTSIDE_RACE' else 'UNKNOWN_MESSAGE_TIME') if variant=='B' else 'UNKNOWN';reason=e['time_quality'].lower();cert=None;continue
  if len(set(acts))!=1:state='UNKNOWN_CONFLICT' if variant=='B' else 'UNKNOWN';reason='conflicting_packet';cert=None;continue
  a=acts[0]
  if a in ('SC_ANNOUNCED','VSC_ANNOUNCED'):
   state={'SC_ANNOUNCED':'SC_REPORTED','VSC_ANNOUNCED':'VSC_REPORTED'}[a] if variant=='B' else a;reason='deployment';cert=e['ref']
  elif a in ('KEEP_SC','END_SC','END_VSC'):
   expected='VSC_ANNOUNCED' if a=='END_VSC' else 'SC_ANNOUNCED'
   if project(state)==expected and cert:
    if variant=='B' and a.startswith('END_'):state='VSC_ENDING_REPORTED' if a=='END_VSC' else 'SC_ENDING_REPORTED'
    reason='ending_reported' if a.startswith('END_') else 'continuation_reported'
   else:state='UNKNOWN_UNMATCHED_MESSAGE' if variant=='B' else 'UNKNOWN';reason='ending_or_continuation_without_trusted_deployment';cert=None
  elif a in ('CLEAR_REPORTED','RED_REPORTED','FINISH_REPORTED'):state=a;reason='direct_report';cert=e['ref']
  else:state='UNKNOWN_RELEVANT_MESSAGE' if variant=='B' else 'UNKNOWN';reason='unsupported_or_corrected_relevant_message';cert=None
 return dict(state=state,projected=project(state),reason=reason,certificate_ref=cert,last_relevant_ref=last,meaning='last_reported_information',delivery_completeness_proven=False)
def reference_events(events):
 out=copy.deepcopy(events);revised={c['identity'] for e in out for c in e.get('changes',[]) if c['kind'] in ('correction','deletion')}
 for e in out:
  e['reference_only']=True
  if e['kind']=='message':
   e['usable']=not e['malformed'] and not e['identity_gap'] and e['time_quality']!='SESSION_TIME_TIE'
   for c in e['changes']:
    if c.get('identity') in revised and c['kind']=='new':c['A']=c['B']='UNKNOWN';c['kind']='later_revision_reference_only'
 return out
