"""Archive-clock fixtures for the availability-authority error model (Issue #35).

Verification tooling, not production code. Per cached race session, within the race
window [first SessionStatus 'Started', last 'Finished']:

  (1) Lap-time fixture (TimingData, dense, relative clock). For every driver lap L
      whose NumberOfLaps advance record carries (in the same or a <1 s neighbouring
      record) the official LastLapTime of lap L, the residual
          r = (P(advance to L) - P(advance to L-1)) - LastLapTime(L)
      compares archive-prefix elapsed time with trackside-loop timing, which is
      independent of the recorder. Also reports the gaps between consecutive
      fixture checks (any driver), i.e. how long the clock goes unchecked.
  (2) RaceControlMessages fixture (sparse, absolute clock). dev = Utc - P - base,
      base = median(Utc - P) over the race window; Utc is whole seconds.
  (3) Heartbeat deviation (reported for completeness; shown NOT to be a reliable
      reference for the shared prefix clock).

Usage: python -I lt_clock_fixture.py --out clock.json CACHE_SESSION_DIR [...]
"""
import argparse, json, os, re, statistics, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # works under python -I
from lt_probe import records, utc


def laptime(s):
    try:
        m, x = s.split(":")
        return int(m) * 60 + float(x)
    except (ValueError, AttributeError):
        return None


def q(v, p):
    v = sorted(v)
    return round(v[int(p * (len(v) - 1))], 3) if v else None


def session(d):
    st = [(t, json.loads(j).get("Status")) for t, j in records(os.path.join(d, "SessionStatus.jsonStream"))]
    starts = [t for t, s in st if s == "Started"]; fins = [t for t, s in st if s == "Finished"]
    if not starts or not fins:
        return {"session": os.path.basename(d), "error": "no Started/Finished", "status": st}
    lo, hi = starts[0], fins[-1]
    adv, lastlt, res = {}, {}, []
    for t, j in records(os.path.join(d, "TimingData.jsonStream")):
        try:
            L = json.loads(j).get("Lines", {})
        except ValueError:
            continue
        for k, v in (L.items() if isinstance(L, dict) else []):
            if not isinstance(v, dict):
                continue
            ll = v.get("LastLapTime")
            if isinstance(ll, dict) and ll.get("Value"):
                lastlt[k] = (t, laptime(ll["Value"]))
            if isinstance(v.get("NumberOfLaps"), int):
                n = v["NumberOfLaps"]
                if (lo <= t <= hi and k in adv and n == adv[k][1] + 1 and k in lastlt
                        and lastlt[k][1] and abs(lastlt[k][0] - t) < 1.0):
                    res.append((t, (t - adv[k][0]) - lastlt[k][1]))
                adv[k] = (t, n)
    r = [x for _, x in res]
    ts = sorted(t for t, _ in res)
    gaps = [b - a for a, b in zip([lo] + ts, ts + [hi])]
    out = {"session": os.path.basename(d), "window": [lo, hi], "status_segments": [s for t, s in st if lo <= t <= hi],
           "lap_fixture_n": len(r), "lap_resid_q001": q(r, .001), "lap_resid_q01": q(r, .01), "lap_resid_q99": q(r, .99),
           "lap_resid_q999": q(r, .999), "lap_resid_max_abs": round(max(abs(x) for x in r), 3) if r else None,
           "lap_resid_n_abs_gt_1s": sum(1 for x in r if abs(x) > 1.0),
           "check_gap_q50": q(gaps, .5), "check_gap_q99": q(gaps, .99), "check_gap_max": round(max(gaps), 1) if gaps else None,
           "check_gaps_gt_30s": [[round(a, 1), round(b - a, 1)] for a, b in zip([lo] + ts, ts + [hi]) if b - a > 30]}
    rc = [(t, utc(m.group(1))) for t, j in records(os.path.join(d, "RaceControlMessages.jsonStream"))
          for m in re.finditer(r'"Utc":"([^"]+)"', j) if lo <= t <= hi]
    if rc:
        base = statistics.median(u - t for t, u in rc)
        dv = [u - t - base for t, u in rc]
        out.update({"rcm_n": len(rc), "rcm_base_epoch": base, "rcm_dev_min": round(min(dv), 2), "rcm_dev_max": round(max(dv), 2)})
        hb = [(t, utc(m.group(1))) for t, j in records(os.path.join(d, "Heartbeat.jsonStream"))
              for m in re.finditer(r'"Utc":"([^"]+)"', j) if lo <= t <= hi]
        if hb:
            hd = [u - t - base for t, u in hb]
            out.update({"hb_dev_vs_rcm_base_min": round(min(hd), 2), "hb_dev_vs_rcm_base_max": round(max(hd), 2)})
    out["common_mode_windows"] = common_mode_windows(d)
    # supporting cross-stream evidence for endpoints without their own UTC (shared-clock assumption)
    entries, inpit = {}, {}
    for t, j in records(os.path.join(d, "TimingData.jsonStream")):
        try:
            L = json.loads(j).get("Lines", {})
        except ValueError:
            continue
        for k, v in (L.items() if isinstance(L, dict) else []):
            if isinstance(v, dict) and "InPit" in v:
                if v["InPit"] and not inpit.get(k) and lo <= t <= hi:
                    entries.setdefault(k, []).append(t)
                inpit[k] = bool(v["InPit"])
    stint = {}
    for t, j in records(os.path.join(d, "TimingAppData.jsonStream")):
        try:
            L = json.loads(j).get("Lines", {})
        except ValueError:
            continue
        for k, v in (L.items() if isinstance(L, dict) else []):
            if isinstance(v, dict) and isinstance(v.get("Stints"), (dict, list)) and lo <= t <= hi:
                stint.setdefault(k, []).append(t)
    lags = []
    for k, ev in entries.items():
        for e in ev:
            nxt = [s for s in stint.get(k, []) if s >= e]
            if nxt and nxt[0] - e < 120:
                lags.append(nxt[0] - e)
    out["entry_to_first_stint_update_s"] = {"n": len(lags), "q01": q(lags, .01), "q50": q(lags, .5), "q99": q(lags, .99),
                                            "min": round(min(lags), 3) if lags else None}
    return out


def common_mode_windows(d, threshold=1.0):
    """Clock-anomaly windows: lap-fixture residuals with |r| > threshold for >= 2 drivers whose
    flagged laps overlap in time (common mode). Single-driver paired residuals are per-driver
    publication delays, not clock anomalies. Returns [(start, end, n_drivers, max_abs_r)]."""
    adv, lastlt, flagged = {}, {}, []
    for t, j in records(os.path.join(d, "TimingData.jsonStream")):
        try:
            L = json.loads(j).get("Lines", {})
        except ValueError:
            continue
        for k, v in (L.items() if isinstance(L, dict) else []):
            if not isinstance(v, dict):
                continue
            ll = v.get("LastLapTime")
            if isinstance(ll, dict) and ll.get("Value"):
                lastlt[k] = (t, laptime(ll["Value"]))
            if isinstance(v.get("NumberOfLaps"), int):
                n = v["NumberOfLaps"]
                if k in adv and n == adv[k][1] + 1 and k in lastlt and lastlt[k][1] and abs(lastlt[k][0] - t) < 1.0:
                    r = (t - adv[k][0]) - lastlt[k][1]
                    if abs(r) > threshold:
                        flagged.append((adv[k][0], t, k, abs(r)))
                adv[k] = (t, n)
    wins = []
    for a, b, k, r in sorted(flagged):
        if wins and a <= wins[-1][1]:
            w = wins[-1]; w[1] = max(w[1], b); w[2].add(k); w[3] = max(w[3], r)
        else:
            wins.append([a, b, {k}, r])
    return [(round(a, 1), round(b, 1), len(ks), round(r, 2)) for a, b, ks, r in wins if len(ks) >= 2]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True); ap.add_argument("dirs", nargs="+")
    a = ap.parse_args()
    out = []
    for d in a.dirs:
        try:
            out.append(session(d))
        except Exception as e:
            out.append({"session": os.path.basename(d), "error": repr(e)})
    json.dump({"argv": sys.argv, "results": out}, open(a.out, "w"), indent=1)

