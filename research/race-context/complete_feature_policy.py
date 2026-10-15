"""Attach the independently reviewed interpretation to outcome-free audit metadata."""
import hashlib
from pipeline import race_features as f, comparison_data as data, comparison_models as m
root=f.ROOT
path=root/'features/audit.json'
audit=data.read_json(path)
audit['feature_authorization']=dict(
    registration_sha256=hashlib.sha256((root/'REGISTRATION.md').read_bytes()).hexdigest(),
    original_quality='Retained unchanged by immutable observation_ref and parent observations_hash; broad omitted_domains is not general admission',
    whitelist=['TimingData.LastLapTime.Value with completed-lap guard','TimingData.BestLapTime.Value with explicit Lap<=L',
        'TimingData.Position','TimingData.GapToLeader','TimingData.IntervalToPositionAhead.Value'],
    extension='Only timing-tower rank, numeric gaps and completed pace are authorized despite old broad positions/telemetry omissions; no coordinates, sectors, speed, track status or weather',
    assumptions_by_source_scope={'39 race-day sessions':'RA1-4','94 older rewritten sessions':'RA1-3/5/6'},
    feature_origin='Exactly one selected CanonicalObservation; no source values are fed to estimator')
data.write_json(path,audit)
print('Feature policy metadata attached; numeric feature payloads unchanged')
