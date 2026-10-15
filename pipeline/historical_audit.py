"""Evidence-only legacy audit. No legacy row is admitted as a model observation."""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
from . import comparison_data as data
from . import development as d

VERSION = 'historical-audit/v1'
REQUIRED = ('LapNumber','DriverNumber','Compound','TyreLife','Stint','PitStatus','TotalLaps')
AUTHORITY_FIELDS = ('availability_timestamp','source_record_ref','TyresNotChanged','terminal_boundary_ref')


def require_pre2026(year):
    if not isinstance(year,int) or not 2018 <= year < 2026:
        raise ValueError('Protected or out-of-scope season refused before read')


def numeric(value):
    try:
        return float(value)
    except (ValueError,TypeError):
        return value


def audit_csv(path,year):
    require_pre2026(year)
    raw=Path(path).read_bytes()
    rows=list(csv.DictReader(raw.decode('utf-8-sig').splitlines()))
    headers=next(csv.reader(raw.decode('utf-8-sig').splitlines()))
    keys=[(r.get('Track'),r.get('DriverNumber'),numeric(r.get('LapNumber'))) for r in rows]
    years=sorted({r.get('Year') for r in rows if r.get('Year')})
    if any(numeric(y)!=year for y in years): raise ValueError('CSV season disagrees with directory')
    return dict(path=str(path),season=year,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),
        rows=len(rows),columns=headers,tracks=sorted({r.get('Track','') for r in rows}),
        year_values=years,duplicate_driver_lap_rows=len(keys)-len(set(keys)),
        missing_required=[k for k in REQUIRED if k not in headers],
        missing_authority=[k for k in AUTHORITY_FIELDS if k not in headers],
        missing_values={k:sum(not r.get(k) for r in rows) for k in REQUIRED},
        pit_status=dict(Counter(r.get('PitStatus') for r in rows)),
        compounds=dict(Counter(r.get('Compound') for r in rows)),
        max_lap=max((numeric(r.get('LapNumber')) for r in rows if r.get('LapNumber')),default=None),
        total_laps=sorted({numeric(r.get('TotalLaps')) for r in rows if r.get('TotalLaps')}),
        admission='REJECTED_LEGACY_DERIVED_ROWS',
        reasons=['No publication/correction history','No qualifying tyre-service target',
                 'Mixed lap-start/lap-end values','Final-derived race distance not causal'])


def season_overlap(folder,year):
    """Compare identifiers, not values: season exports may use a different schema."""
    require_pre2026(year)
    season=folder/'season.csv'
    if not season.exists(): return None
    def keys(p):
        with p.open() as f:
            return {(r.get('Track'),r.get('DriverNumber'),numeric(r.get('LapNumber'))) for r in csv.DictReader(f)}
    aggregate=keys(season); perrace=set()
    for p in sorted(folder.glob('*.csv')):
        if p.name!='season.csv': perrace.update(keys(p))
    return dict(season_keys=len(aggregate),race_file_keys=len(perrace),overlap_keys=len(aggregate&perrace),
                aggregate_only_keys=len(aggregate-perrace),rule='Never concatenate season.csv with race exports')


def audit(root):
    csvs=[]; seasons={}
    for year in range(2018,2024):
        folder=root/'data'/str(year)
        entries=[audit_csv(p,year) for p in sorted(folder.glob('*.csv'))]
        # Paths in durable report are relative, keeping reproduction portable.
        for entry in entries: entry['path']=str(Path(entry['path']).relative_to(root))
        csvs.extend(entries)
        seasons[str(year)]=dict(files=len(entries),race_files=sum(Path(e['path']).name!='season.csv' for e in entries),
            rows_including_season_exports=sum(e['rows'] for e in entries),overlap=season_overlap(folder,year))
    scan_path=root/'verification/evidence/headscan_v1.json'
    scan=json.loads(scan_path.read_bytes())
    # This artifact contains metadata only, never timing/pit/service outcomes.
    pre=[r for r in scan['rows'] if r['season']<2026]
    archives=[]
    for r in pre:
        require_pre2026(r['season'])
        authority=('VERIFIED_BOUNDED_TIME' if r['status']==200 and r['race_day_written'] else
                   'UNSUPPORTED' if r['status']!=200 or (r['season']==2018 and r['round'] in (2,12)) else 'UNVERIFIED_ARCHIVE')
        archives.append({**r,'authority':authority,'metadata_only':True})
    admitted=[]
    for year,rnd in data.PARTITION:
        folder=root/'research/model-comparison/sources'/f'{year}-{rnd:02d}'
        source,records=d.read_source(year,rnd,folder)
        admitted.append(dict(season=year,round=rnd,source_ref=source['artifact_id'],
            endpoints={feed:dict(sha256=meta['sha256'],bytes=meta['bytes'],last_modified=meta['last_modified'],
                                records=len(records[feed])) for feed,meta in source['files'].items()}))
    return dict(version=VERSION,csv_files=csvs,seasons=seasons,
        csv_file_count=len(csvs),race_file_count=sum(v['race_files'] for v in seasons.values()),
        historical_archive_metadata=archives,archive_metadata_source_hash=hashlib.sha256(scan_path.read_bytes()).hexdigest(),
        archive_metadata_retrieved_at=scan['retrieved_at'],
        archive_counts=dict(Counter(r['authority'] for r in archives)),admitted_sources=admitted,
        admitted_pre2026_races=len(admitted),csv_admitted=0,
        blocker='Older archive availability/revision authority requires owner decision or independent evidence',
        final_exposure='No 2026 source or outcome opened; headscan metadata filtered to pre-2026')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    data.write_json(args.output,audit(d.ROOT))
    print('Pre-2026 evidence audit complete; no CSV admitted and no protected outcome read.')

if __name__=='__main__':main()
