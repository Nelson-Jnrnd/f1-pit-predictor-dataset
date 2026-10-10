"""Tyre-service qualification evidence check (Issue #35). Verification tooling only.

For every in-race pit entry (TimingData InPit False->True after SessionStatus
Started), collect TimingAppData stint updates for the same driver between that
entry and the next entry (stint keys may be opened and later overwritten), and
classify the visit from the LAST stint update carrying TyresNotChanged in that window
(stints are typically opened provisionally at pit entry and updated once tyres are fitted):

  POS  TyresNotChanged == "0"  (tyre change asserted)
  NEG  TyresNotChanged == "1"  (no tyre change asserted)
  NONE no stint update with TyresNotChanged in the window

Independent cross-checks (retrospective):
  - Jolpica pit-stop duration for the matching in-lap (c(E)+1);
  - RaceControlMessages drive-through / stop-and-go penalty issued for the car
    before the entry.
A NEG visit is "corroborated" if a penalty was issued before it or its Jolpica
duration is below the race's minimum POS duration. A POS visit is "contradicted"
if a penalty was issued before it and its duration is below the minimum POS duration.

Usage: python -I lt_tyre_service.py --cache DIR --probe probe.json --out tyre.json
"""
import argparse, collections, json, os, re, statistics, urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))  # works under python -I
from lt_probe import records

UA = {"User-Agent": "f1-v2-verification"}
PEN = re.compile(r'"Message":"[^"]*?(PENALTY SERVED - )?(?:DRIVE THROUGH|STOP-AND-GO|STOP AND GO|STOP/GO) PENALTY FOR CAR (\d+)')


def jolpica(path):
    return json.load(urllib.request.urlopen(urllib.request.Request("https://api.jolpi.ca/ergast/f1/" + path, headers=UA), timeout=60))


def secs(x):
    try:
        if ":" in x:
            m, s = x.split(":")
            return int(m) * 60 + float(s)
        return float(x)
    except ValueError:
        return None


def analyse(d, year, rnd, started):
    res = jolpica(f"{year}/{rnd}/results.json?limit=100")["MRData"]["RaceTable"]["Races"]
    stops = jolpica(f"{year}/{rnd}/pitstops.json?limit=200")["MRData"]["RaceTable"]["Races"]
    num_of = {r["Driver"]["driverId"]: r["number"] for r in (res[0]["Results"] if res else [])}
    dur = {}
    for s in (stops[0]["PitStops"] if stops else []):
        dur[(num_of.get(s["driverId"]), int(s["lap"]))] = secs(s["duration"])
    laps, inpit, entries = {}, {}, collections.defaultdict(list)
    for t, j in records(os.path.join(d, "TimingData.jsonStream")):
        try:
            lines = json.loads(j).get("Lines", {})
        except ValueError:
            continue
        for drv, v in (lines.items() if isinstance(lines, dict) else []):
            if not isinstance(v, dict):
                continue
            if isinstance(v.get("NumberOfLaps"), int):
                laps[drv] = v["NumberOfLaps"]
            if "InPit" in v:
                if v["InPit"] and not inpit.get(drv) and started is not None and t > started:
                    entries[drv].append((t, laps.get(drv, 0)))
                inpit[drv] = bool(v["InPit"])
    upd = collections.defaultdict(list)
    for t, j in records(os.path.join(d, "TimingAppData.jsonStream")):
        try:
            lines = json.loads(j).get("Lines", {})
        except ValueError:
            continue
        for drv, v in (lines.items() if isinstance(lines, dict) else []):
            st = v.get("Stints") if isinstance(v, dict) else None
            items = st.items() if isinstance(st, dict) else enumerate(st) if isinstance(st, list) else []
            for k, b in items:
                if int(k) > 0 and isinstance(b, dict) and "TyresNotChanged" in b:
                    upd[drv].append((t, b))
    issued = collections.defaultdict(list)
    for t, j in records(os.path.join(d, "RaceControlMessages.jsonStream")):
        for m in PEN.finditer(j):
            if not m.group(1):
                issued[m.group(2)].append(t)
    visits = []
    for drv, ev in entries.items():
        for i, (t, c) in enumerate(ev):
            nxt = ev[i + 1][0] if i + 1 < len(ev) else float("inf")
            win = [b for s, b in upd.get(drv, []) if t <= s < nxt]
            u = win[-1] if win else None
            first = win[0] if win else None
            cls = "NONE" if u is None else ("NEG" if str(u["TyresNotChanged"]) == "1" else "POS")
            visits.append({"drv": drv, "t": round(t, 1), "lap": c + 1, "cls": cls,
                           "first_cls": None if first is None else ("NEG" if str(first["TyresNotChanged"]) == "1" else "POS"),
                           "dur": dur.get((drv, c + 1)), "penalty_before": any(x < t for x in issued.get(drv, []))})
    pos_d = [v["dur"] for v in visits if v["cls"] == "POS" and v["dur"]]
    mpos = min(pos_d) if pos_d else None
    cnt = collections.Counter(v["cls"] for v in visits)
    neg = [v for v in visits if v["cls"] == "NEG"]
    neg_corr = sum(1 for v in neg if v["penalty_before"] or (v["dur"] and mpos and v["dur"] < mpos))
    pos_contra = sum(1 for v in visits if v["cls"] == "POS" and v["penalty_before"] and v["dur"] and mpos and v["dur"] <= mpos)
    pen_vis = [v for v in visits if v["penalty_before"]]
    return {"counts": dict(cnt), "neg": len(neg), "neg_corroborated": neg_corr, "pos_contradicted": pos_contra,
            "min_pos_duration": mpos, "neg_visits": neg, "none_visits": [v for v in visits if v["cls"] == "NONE"],
            "penalty_visits": pen_vis}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True); ap.add_argument("--probe", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = []
    for r in json.load(open(a.probe))["results"]:
        if "error" in r["files"].get("TimingData", {}) or not r.get("round"):
            continue
        started = next((t for t, s in r["session_status"] if s == "Started"), None)
        d = os.path.join(a.cache, r["session"].strip("/").replace("/", "__"))
        try:
            x = analyse(d, r["session"][:4], r["round"], started); x["session"] = r["session"]; out.append(x)
        except Exception as e:
            out.append({"session": r["session"], "error": repr(e)})
    json.dump(out, open(a.out, "w"), indent=1)
