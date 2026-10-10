"""Target-reconstruction capability checks on cached archive streams (Issue #35).

Verification tooling, not production code. Reads the stream cache written by
lt_probe.py (and freezes every Jolpica response under CACHE/jolpica/, recording
its SHA-256). Per race session, within the race window
[first SessionStatus 'Started', last 'Finished'] unless stated otherwise:

  1. pit entries: TimingData InPit False->True; entries after the last
     'Finished' are counted separately (post-finish movements, outside race
     participation per #19).
  2. lap at entry c(E): the driver's NumberOfLaps value at the entry record in
     stream order; matched to Jolpica pit stops when c(E) + 1 == Jolpica lap.
  3. exits: InPit True->False following an entry (visit segmentation).
  4. lap progression: per-driver jumps (> +1) and regressions in NumberOfLaps.
  5. terminal: drivers with TimingData Retired:true (Retired only) versus
     Jolpica results whose status is not Finished / Lapped / "+N Lap(s)" and is
     not a disqualification; Stopped:true is reported separately.
  6. tyre service (TimingAppData): for each in-race visit, the LAST stint update
     carrying TyresNotChanged in [entry, next entry) gives POS ("0"), NEG ("1"),
     or NONE (no update). POS internal consistency: that update also shows
     New:"true", a compound different from the previous stint, or StartLaps 0.
  7. visit-specific penalty test set: the first in-race entry of a car after a
     RaceControlMessages DRIVE THROUGH / STOP-AND-GO penalty for that car is
     issued, where a matching "PENALTY SERVED" message exists. No tyre work is
     permitted while serving these penalties, so these visits are an independent
     negative test set.

Usage: python -I lt_capabilities.py --cache DIR --probe probe.json --out caps.json
"""
import argparse, collections, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # works under python -I
from lt_probe import records, jolpica_cached

PEN = re.compile(r'"Message":"[^"]*?(PENALTY SERVED - )?(DRIVE THROUGH|STOP-AND-GO|STOP AND GO|STOP/GO) PENALTY FOR CAR (\d+)')
FINISHED = re.compile(r"^(Finished|Lapped|\+\d+ Laps?)$")


def lines_of(j):
    try:
        lines = json.loads(j).get("Lines", {})
    except ValueError:
        return {}
    return lines if isinstance(lines, dict) else {}


def analyse(cache, sess, year, rnd, status):
    d = os.path.join(cache, sess.strip("/").replace("/", "__"))
    res, sha_r = jolpica_cached(f"{year}/{rnd}/results.json?limit=100", cache)
    stops, sha_p = jolpica_cached(f"{year}/{rnd}/pitstops.json?limit=200", cache)
    res = res["MRData"]["RaceTable"]["Races"]; stops = stops["MRData"]["RaceTable"]["Races"]
    results = res[0]["Results"] if res else []
    num_of = {r["Driver"]["driverId"]: r["number"] for r in results}
    jl = collections.defaultdict(list)
    for s in (stops[0]["PitStops"] if stops else []):
        jl[num_of.get(s["driverId"])].append(int(s["lap"]))
    started = next((t for t, s in status if s == "Started"), None)
    finished = max((t for t, s in status if s == "Finished"), default=None)

    laps, inpit = {}, {}
    entries, post_finish, exits = collections.defaultdict(list), collections.defaultdict(list), collections.defaultdict(list)
    seq = collections.defaultdict(list); retired, stopped = set(), set()
    for t, j in records(os.path.join(d, "TimingData.jsonStream")):
        for drv, v in lines_of(j).items():
            if not isinstance(v, dict):
                continue
            if isinstance(v.get("NumberOfLaps"), int):
                laps[drv] = v["NumberOfLaps"]; seq[drv].append(v["NumberOfLaps"])
            if "InPit" in v:
                if v["InPit"] and not inpit.get(drv) and started is not None and t > started:
                    (post_finish if finished is not None and t > finished else entries)[drv].append((t, laps.get(drv, 0)))
                if not v["InPit"] and inpit.get(drv):
                    exits[drv].append(t)
                inpit[drv] = bool(v["InPit"])
            if v.get("Retired") is True:
                retired.add(drv)
            if v.get("Stopped") is True:
                stopped.add(drv)

    stint_upd = collections.defaultdict(list); last_compound = {}
    for t, j in records(os.path.join(d, "TimingAppData.jsonStream")):
        for drv, v in lines_of(j).items():
            st = v.get("Stints") if isinstance(v, dict) else None
            items = st.items() if isinstance(st, dict) else enumerate(st) if isinstance(st, list) else []
            for k, b in items:
                if not isinstance(b, dict):
                    continue
                k = int(k)
                if k > 0 and "TyresNotChanged" in b:
                    stint_upd[drv].append((t, k, b, last_compound.get((drv, k - 1))))
                if "Compound" in b:
                    last_compound[(drv, k)] = b["Compound"]

    issued, served = collections.defaultdict(list), set()
    for t, j in records(os.path.join(d, "RaceControlMessages.jsonStream")):
        for m in PEN.finditer(j):
            (served.add(m.group(3)) if m.group(1) else issued[m.group(3)].append(t))

    out = {"session": sess, "round": rnd, "jolpica_results_sha256": sha_r, "jolpica_pitstops_sha256": sha_p,
           "jolpica_stops": sum(len(v) for v in jl.values()),
           "entries_in_race": sum(len(v) for v in entries.values()),
           "entries_post_finish": sum(len(v) for v in post_finish.values())}
    # lap matching, exits, tyre classes, penalty test set
    matched = 0; extra = []; with_exit = 0
    classes = collections.Counter(); pos_consistent = 0; penalty_set = []
    for drv, ev in entries.items():
        jlaps = list(jl.get(drv, []))
        pen_times = sorted(issued.get(drv, [])) if drv in served else []
        used_pen = set()
        for i, (t, c) in enumerate(ev):
            nxt = ev[i + 1][0] if i + 1 < len(ev) else float("inf")
            with_exit += any(t < x <= nxt for x in exits.get(drv, []))
            if c + 1 in jlaps:
                jlaps.remove(c + 1); matched += 1
            else:
                extra.append([drv, round(t, 1), c + 1, not any(n > c for n in seq[drv][-1:])])
            win = [u for u in stint_upd.get(drv, []) if t <= u[0] < nxt]
            if not win:
                cls = "NONE"
            else:
                _, k, b, prev_comp = win[-1]
                cls = "NEG" if str(b["TyresNotChanged"]) == "1" else "POS"
                if cls == "POS" and (str(b.get("New")) == "true" or b.get("StartLaps") == 0 or
                                     (b.get("Compound") and prev_comp and b["Compound"] != prev_comp)):
                    pos_consistent += 1
            classes[cls] += 1
            # first entry after an issued (and later served) drive-through / stop-and-go penalty
            for pt in pen_times:
                if pt < t and pt not in used_pen and not any(pt < e < t for e, _ in ev[:i]):
                    used_pen.add(pt); penalty_set.append({"drv": drv, "t": round(t, 1), "lap": c + 1, "class": cls}); break
        out.setdefault("jolpica_unmatched", 0); out["jolpica_unmatched"] += len(jlaps)
    out.update({"entries_matching_jolpica_lap": matched, "entries_without_jolpica_stop": len(extra),
                "extra_entries": extra, "entries_with_exit": with_exit,
                "tyre_classes": dict(classes), "pos_with_consistent_fields": pos_consistent,
                "penalty_test_set": penalty_set})
    # lap progression
    out["lap_jumps"] = sum(1 for s in seq.values() for a, b in zip(s, s[1:]) if b > a + 1)
    out["lap_regressions"] = sum(1 for s in seq.values() for a, b in zip(s, s[1:]) if b < a)
    # terminal (Retired only; disqualifications excluded from Jolpica set)
    jol_term = {r["number"] for r in results if not FINISHED.match(r["status"]) and "isqualified" not in r["status"]}
    jol_dsq = {r["number"] for r in results if "isqualified" in r["status"]}
    out.update({"retired_flag": sorted(retired), "stopped_flag_only": sorted(stopped - retired),
                "jolpica_terminal": sorted(jol_term), "jolpica_dsq": sorted(jol_dsq),
                "terminal_agree": len(retired & jol_term), "terminal_flag_only": sorted(retired - jol_term),
                "terminal_jolpica_only": sorted(jol_term - retired)})
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True); ap.add_argument("--probe", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = []
    for r in json.load(open(a.probe))["results"]:
        if "error" in r["files"].get("TimingData", {}) or not r.get("round"):
            out.append({"session": r["session"], "skipped": "no TimingData or no Jolpica round"}); continue
        try:
            out.append(analyse(a.cache, r["session"], r["session"][:4], r["round"], r["session_status"]))
        except Exception as e:
            out.append({"session": r["session"], "error": repr(e)})
    json.dump({"argv": sys.argv, "results": out}, open(a.out, "w"), indent=1)
