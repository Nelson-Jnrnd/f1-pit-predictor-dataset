"""Target-reconstruction capability checks on cached archive streams (Issue #35).

Verification tooling, not production code. Reads the cache written by
lt_probe.py and, per race, compares with the Jolpica public record:

  1. lap-at-entry: for each in-race InPit False->True transition in TimingData,
     c(E) = the driver's lap-count value at that point in stream order (number
     of lap advances already seen). Jolpica's pit-stop `lap` is the in-lap, so a
     match means c(E) + 1 == jolpica_lap.
  2. stint increments: whether TimingAppData opens a new stint for the driver
     between that entry and the next entry (tyre-service evidence candidate),
     split by entries that do / do not match a Jolpica stop.
  3. cross-stream lap consistency: lag from the leader's TimingData lap advance
     to the LapCount CurrentLap increment.
  4. visit segmentation: in-race entries with a following InPit False exit.
  5. negative tyre-service candidates: entries without a Jolpica stop, classified as
     (a) penalty: a DRIVE THROUGH / STOP-AND-GO penalty for the same car was issued
         before the entry and a matching "PENALTY SERVED" message exists (stewards
         publish SERVED late, so its timing is not constrained; retrospective use);
     (b) retirement: no further lap advance for the driver after the entry;
     (c) unexplained.
  6. stint detail: share of opened stints carrying Compound and New fields.
  7. participation: drivers flagged Retired/Stopped in TimingData versus
     Jolpica non-classified/retired status.

Usage: python -I lt_capabilities.py --cache DIR --probe probe.json --out caps.json
"""
import argparse, collections, json, os, statistics, urllib.request
from lt_probe import records, merge

UA = {"User-Agent": "f1-v2-verification"}


def jolpica(path):
    return json.load(urllib.request.urlopen(urllib.request.Request("https://api.jolpi.ca/ergast/f1/" + path, headers=UA), timeout=60))


def analyse(cache, sess, year, rnd, started):
    d = os.path.join(cache, sess.strip("/").replace("/", "__"))
    res = jolpica(f"{year}/{rnd}/results.json?limit=100")["MRData"]["RaceTable"]["Races"]
    stops = jolpica(f"{year}/{rnd}/pitstops.json?limit=200")["MRData"]["RaceTable"]["Races"]
    num_of = {r["Driver"]["driverId"]: r["number"] for r in (res[0]["Results"] if res else [])}
    jl = collections.defaultdict(list)
    for s in (stops[0]["PitStops"] if stops else []):
        jl[num_of.get(s["driverId"])].append(int(s["lap"]))
    # TimingData stream-order events
    laps = {}; inpit = {}; entries = collections.defaultdict(list); lead_adv = []
    exits = collections.defaultdict(list); retired = set(); advances = collections.defaultdict(list)
    for t, j in records(os.path.join(d, "TimingData.jsonStream")):
        try:
            lines = json.loads(j).get("Lines", {})
        except ValueError:
            continue
        if not isinstance(lines, dict):
            continue
        for drv, v in lines.items():
            if not isinstance(v, dict):
                continue
            if "NumberOfLaps" in v and isinstance(v["NumberOfLaps"], int):
                prev = laps.get(drv, 0)
                if v["NumberOfLaps"] > prev:
                    advances[drv].append(t)
                if v["NumberOfLaps"] > max([0] + list(laps.values())):
                    lead_adv.append((t, v["NumberOfLaps"]))
                laps[drv] = v["NumberOfLaps"]
            if "InPit" in v:
                if v["InPit"] and not inpit.get(drv) and started is not None and t > started:
                    entries[drv].append((t, laps.get(drv, 0)))
                if not v["InPit"] and inpit.get(drv):
                    exits[drv].append(t)
                inpit[drv] = bool(v["InPit"])
            if v.get("Retired") is True or v.get("Stopped") is True:
                retired.add(drv)
    # TimingAppData stint openings (stream order)
    stint_open = collections.defaultdict(list); seen = collections.defaultdict(set); detailed = opened = 0
    for t, j in records(os.path.join(d, "TimingAppData.jsonStream")):
        try:
            lines = json.loads(j).get("Lines", {})
        except ValueError:
            continue
        for drv, v in (lines.items() if isinstance(lines, dict) else []):
            st = v.get("Stints") if isinstance(v, dict) else None
            keys = st.keys() if isinstance(st, dict) else range(len(st)) if isinstance(st, list) else []
            for k in keys:
                k = int(k)
                if k not in seen[drv]:
                    seen[drv].add(k)
                    if k > 0:
                        stint_open[drv].append(t)
                        body = st[str(k)] if isinstance(st, dict) else st[k]
                        opened += 1
                        detailed += isinstance(body, dict) and "Compound" in body and "New" in body
    # RaceControlMessages served drive-through / stop-and-go per car
    issued = collections.defaultdict(list); served = set(); lap_adv = collections.defaultdict(list)
    pat = r'"Message":"([^"]*?(PENALTY SERVED - )?(?:DRIVE THROUGH|STOP-AND-GO|STOP AND GO|STOP/GO) PENALTY FOR CAR (\d+)[^"]*)"'
    for t, j in records(os.path.join(d, "RaceControlMessages.jsonStream")):
        for m in __import__("re").finditer(pat, j):
            if m.group(2):
                served.add(m.group(3))
            else:
                issued[m.group(3)].append(t)
    # 1 + 2
    explained = 0; with_exit = 0; retire_entries = 0; unexplained = []
    matched = unmatched_lt = 0; stint_m = stint_u = 0; jol_total = sum(len(v) for v in jl.values()); jol_hit = 0
    for drv, ev in entries.items():
        jlaps = list(jl.get(drv, []))
        for i, (t, c) in enumerate(ev):
            nxt = ev[i + 1][0] if i + 1 < len(ev) else float("inf")
            has_stint = any(t <= s < nxt for s in stint_open.get(drv, []))
            with_exit += any(t < x <= nxt for x in exits.get(drv, []))
            if c + 1 in jlaps:
                jlaps.remove(c + 1); matched += 1; stint_m += has_stint
            else:
                unmatched_lt += 1; stint_u += has_stint
                if drv in served and any(i < t for i in issued.get(drv, [])):
                    explained += 1
                elif not any(a > t for a in advances.get(drv, [])):
                    retire_entries += 1
                else:
                    unexplained.append([drv, round(t, 1), c])
        jol_hit += len(jl.get(drv, [])) - len(jlaps)
    # 3 LapCount lag
    lc = [(t, json.loads(j)["CurrentLap"]) for t, j in records(os.path.join(d, "LapCount.jsonStream")) if '"CurrentLap"' in j]
    lead_t = {}
    for t, n in lead_adv:
        lead_t.setdefault(n, t)
    lags = [t - lead_t[n - 1] for t, n in lc if (n - 1) in lead_t]
    return {"session": sess, "lt_entries": sum(len(v) for v in entries.values()), "jolpica_stops": jol_total,
            "entries_matching_jolpica_lap": matched, "jolpica_stops_matched": jol_hit,
            "lt_entries_without_jolpica_stop": unmatched_lt,
            "stint_opened_after_matched_entry": stint_m, "stint_opened_after_unmatched_entry": stint_u,
            "unmatched_entries_explained_by_served_penalty": explained,
            "unmatched_entries_followed_by_no_further_lap": retire_entries,
            "unmatched_entries_unexplained": unexplained,
            "entries_with_exit": with_exit, "stints_opened": opened, "stints_with_compound_and_new": detailed,
            "drivers_flagged_retired_or_stopped": sorted(retired),
            "jolpica_not_finished": sorted(r["number"] for r in (res[0]["Results"] if res else [])
                                           if not (r["status"] in ("Finished", "Lapped") or r["status"].startswith("+"))),
            "lapcount_lag_s": {"n": len(lags), "median": round(statistics.median(lags), 2) if lags else None,
                               "min": round(min(lags), 2) if lags else None, "max": round(max(lags), 2) if lags else None}}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True); ap.add_argument("--probe", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = []
    for r in json.load(open(a.probe))["results"]:
        if "error" in r["files"].get("TimingData", {}) or not r.get("round"):
            continue
        started = next((t for t, s in r["session_status"] if s == "Started"), None)
        try:
            out.append(analyse(a.cache, r["session"], r["session"][:4], r["round"], started))
        except Exception as e:
            out.append({"session": r["session"], "error": repr(e)})
    json.dump(out, open(a.out, "w"), indent=1)
