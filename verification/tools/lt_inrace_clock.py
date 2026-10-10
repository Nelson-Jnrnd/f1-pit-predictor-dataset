"""In-race clock check (Issue #35): Heartbeat/RCM Utc vs archive prefix restricted to
the window between SessionStatus 'Started' and the final 'Finished', with status
segments (e.g. Aborted/Suspended) reported. Verification tooling only.

Usage: python -I lt_inrace_clock.py CACHE_DIR [CACHE_DIR ...] > out.json
"""
import json, os, re, statistics, sys
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))  # works under python -I
from lt_probe import records, utc


def session(d):
    st = [(t, json.loads(j).get("Status")) for t, j in records(os.path.join(d, "SessionStatus.jsonStream"))]
    starts = [t for t, s in st if s == "Started"]
    fins = [t for t, s in st if s == "Finished"]
    if not starts or not fins:
        return {"session": os.path.basename(d), "status": st, "error": "no Started/Finished"}
    lo, hi = starts[0], fins[-1]
    hb = [(t, utc(m.group(1))) for t, j in records(os.path.join(d, "Heartbeat.jsonStream"))
          for m in re.finditer(r'"Utc":"([^"]+)"', j)]
    inr = [(t, u) for t, u in hb if lo <= t <= hi]
    base = statistics.median(u - t for t, u in inr)
    dev = sorted(u - t - base for t, u in inr)
    rcm = [utc(m.group(1)) - t - base for t, j in records(os.path.join(d, "RaceControlMessages.jsonStream"))
           for m in re.finditer(r'"Utc":"([^"]+)"', j) if lo <= t <= hi]
    q = lambda p: round(dev[int(p * (len(dev) - 1))], 2)
    return {"session": os.path.basename(d), "window": [lo, hi],
            "status_segments": [s for t, s in st if lo <= t <= hi],
            "hb_n": len(dev), "hb_dev_min": q(0), "hb_dev_p1": q(.01), "hb_dev_p99": q(.99), "hb_dev_max": q(1),
            "hb_frac_abs_le_5s": round(sum(1 for x in dev if abs(x) <= 5) / len(dev), 4),
            "rcm_n": len(rcm), "rcm_dev_min": round(min(rcm), 2) if rcm else None,
            "rcm_dev_max": round(max(rcm), 2) if rcm else None}


if __name__ == "__main__":
    out = []
    for d in sys.argv[1:]:
        try:
            out.append(session(d))
        except Exception as e:
            out.append({"session": os.path.basename(d), "error": repr(e)})
    json.dump(out, sys.stdout, indent=1)
