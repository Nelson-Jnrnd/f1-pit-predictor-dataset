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
    return out


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
