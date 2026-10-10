"""Support-matrix probe for the F1 live-timing static archive (Issue #35).

Verification tooling, not production code. For each requested race session it
downloads selected jsonStream endpoints into a local cache, records SHA-256 and
HTTP metadata, and computes evidence metrics for:

  (A) availability authority: prefix contemporaneity against embedded Utc
      (Heartbeat, RaceControlMessages), recording-outage windows, regeneration
      evidence (Last-Modified);
  (B) target capabilities: pit-entry transitions (TimingData InPit), lap-count
      progression, stint changes (TimingAppData), compared with Jolpica pit stops;
  (C) scheduled race distance (LapCount TotalLaps).

Usage:
  python -I lt_probe.py --cache DIR --out evidence.json YEAR:ROUND|auto:PATH ...
  python -I lt_probe.py --cache DIR --out new.json --verify old.json   # re-fetch the sessions
      listed in old.json and report any SHA-256 / Last-Modified difference
"""
import argparse, collections, datetime as dt, hashlib, json, re, statistics, urllib.parse, urllib.request, os

BASE = "https://livetiming.formula1.com/static/"
JOLPICA = "https://api.jolpi.ca/ergast/f1/{y}/{r}/pitstops.json?limit=200"
FEEDS = ["Heartbeat", "SessionStatus", "TimingData", "TimingAppData", "LapCount",
         "RaceControlMessages", "DriverList", "SessionInfo"]


def fetch(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": "f1-v2-verification"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
        meta = {"status": r.status, "last_modified": r.headers.get("Last-Modified"),
                "etag": r.headers.get("ETag")}
    with open(path, "wb") as f:
        f.write(data)
    meta["sha256"] = hashlib.sha256(data).hexdigest()
    meta["bytes"] = len(data)
    return meta


def records(path):
    with open(path, encoding="utf-8-sig") as f:
        for ln in f:
            ln = ln.rstrip("\r\n")
            if len(ln) < 13 or ln[2] != ":":
                continue
            h, m, s = ln[:12].split(":")
            yield int(h) * 3600 + int(m) * 60 + float(s), ln[12:]


def utc(s):
    s = s.rstrip("Z")
    if "." in s:
        a, b = s.split(".")
        s = a + "." + b[:6]
    return dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc).timestamp()


def merge(dst, src):
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            merge(dst[k], v)
        else:
            dst[k] = v


def jolpica_cached(path, cache):
    """Fetch a Jolpica API path once, store the raw response under CACHE/jolpica/ and return
    (parsed_json, sha256). Re-runs read the stored copy, so evidence is frozen and hashable."""
    d = os.path.join(cache, "jolpica"); os.makedirs(d, exist_ok=True)
    fn = os.path.join(d, re.sub(r"[^A-Za-z0-9]+", "_", path) + ".json")
    if not os.path.exists(fn):
        req = urllib.request.Request("https://api.jolpi.ca/ergast/f1/" + path, headers={"User-Agent": "f1-v2-verification"})
        data = urllib.request.urlopen(req, timeout=60).read()
        with open(fn, "wb") as f:
            f.write(data)
    raw = open(fn, "rb").read()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def resolve_round(year, session_path, cache):
    """Map a session path to its official round via the Jolpica calendar: race date, or the
    session date +/- 1 day (local-date vs UTC-date differences, e.g. Saturday-night races)."""
    date = dt.date.fromisoformat(session_path.strip("/").split("/")[-1][:10])
    races = jolpica_cached(f"{year}.json?limit=100", cache)[0]["MRData"]["RaceTable"]["Races"]
    for delta in (0, -1, 1):
        for race in races:
            if race["date"] == (date + dt.timedelta(days=delta)).isoformat():
                return race["round"]
    return None


def probe(session_path, cache, year, rnd):
    if rnd == "auto":
        rnd = resolve_round(year, session_path, cache)
    d = os.path.join(cache, session_path.strip("/").replace("/", "__"))
    os.makedirs(d, exist_ok=True)
    out = {"session": session_path, "round": rnd, "files": {}}
    for feed in FEEDS:
        p = os.path.join(d, feed + ".jsonStream")
        try:
            out["files"][feed] = fetch(BASE + urllib.parse.quote(session_path) + feed + ".jsonStream", p)
        except Exception as e:  # missing feed is evidence too
            out["files"][feed] = {"error": str(e)}

    def path(feed):
        p = os.path.join(d, feed + ".jsonStream")
        return p if "error" not in out["files"][feed] else None

    # (A) Heartbeat contemporaneity
    hb = [(t, utc(m.group(1))) for t, j in records(path("Heartbeat")) for m in re.finditer(r'"Utc":"([^"]+)"', j)] if path("Heartbeat") else []
    if hb:
        offs = [u - t for t, u in hb]
        base = statistics.median(offs)
        dev = [o - base for o in offs]
        within = sum(1 for x in dev if abs(x) <= 5) / len(dev)
        # outage windows: heartbeat records whose prefix lags their Utc by > 30 s
        late = [(t, u) for (t, u), x in zip(hb, dev) if x < -30]
        windows = collections.Counter(round(t, 3) for t, _ in late)
        out["heartbeat"] = {"n": len(hb), "base_epoch": base, "frac_within_5s": round(within, 4),
                            "late_records": len(late), "late_burst_prefixes": len(windows),
                            "max_lag_s": round(-min(dev), 1)}
    else:
        base = None
    # RaceControlMessages Utc (whole seconds) relative to heartbeat base
    if path("RaceControlMessages") and base is not None:
        rd = [utc(m.group(1)) - t - base for t, j in records(path("RaceControlMessages")) for m in re.finditer(r'"Utc":"([^"]+)"', j)]
        if rd:
            out["rcm"] = {"n": len(rd), "median_dev_s": round(statistics.median(rd), 2),
                          "max_abs_dev_s": round(max(abs(x) for x in rd), 2),
                          "frac_within_5s": round(sum(1 for x in rd if abs(x) <= 5) / len(rd), 4)}
    # SessionStatus
    status = [(t, json.loads(j).get("Status")) for t, j in records(path("SessionStatus"))] if path("SessionStatus") else []
    started = next((t for t, s in status if s == "Started"), None)
    out["session_status"] = status
    # (C) LapCount TotalLaps
    if path("LapCount"):
        tl = [(t, json.loads(j).get("TotalLaps")) for t, j in records(path("LapCount")) if "TotalLaps" in j]
        out["lapcount_total_laps"] = [(round(t, 3), v) for t, v in tl]
    # (B) TimingData: lap progression and InPit transitions
    laps = collections.defaultdict(list); inpit = collections.defaultdict(list)
    if path("TimingData"):
        for t, j in records(path("TimingData")):
            try:
                lines = json.loads(j).get("Lines", {})
            except ValueError:
                continue
            if not isinstance(lines, dict):
                continue
            for drv, v in lines.items():
                if not isinstance(v, dict):
                    continue
                if "NumberOfLaps" in v:
                    laps[drv].append((t, v["NumberOfLaps"]))
                if "InPit" in v:
                    inpit[drv].append((t, v["InPit"]))
    lapstats = {}
    for drv, seq in laps.items():
        vals = [n for _, n in seq]
        jumps = sum(1 for a, b in zip(vals, vals[1:]) if b > a + 1)
        regress = sum(1 for a, b in zip(vals, vals[1:]) if b < a)
        lapstats[drv] = {"final": vals[-1], "updates": len(vals), "jumps": jumps, "regressions": regress}
    out["lap_progression"] = {"drivers": len(lapstats),
                              "drivers_with_jumps": sum(1 for s in lapstats.values() if s["jumps"]),
                              "drivers_with_regressions": sum(1 for s in lapstats.values() if s["regressions"]),
                              "per_driver": lapstats}
    entries = {}
    for drv, seq in inpit.items():
        state, n = False, 0
        for t, v in seq:
            if v and not state and started is not None and t > started:
                n += 1
            state = bool(v)
        entries[drv] = n
    out["inpit_entries_after_start"] = entries
    # Jolpica pit stops (independent public record)
    if rnd:
        try:
            js, sha = jolpica_cached(f"{year}/{rnd}/pitstops.json?limit=200", cache)
            out["jolpica_pitstops_sha256"] = sha
            races = js["MRData"]["RaceTable"]["Races"]
            stops = collections.Counter()
            for s in (races[0]["PitStops"] if races else []):
                stops[s["driverId"]] += 1
            out["jolpica_pitstops_total"] = sum(stops.values())
        except Exception as e:
            out["jolpica_error"] = str(e)
    out["inpit_entries_total"] = sum(entries.values())
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--verify", help="previous evidence JSON: re-fetch its sessions and diff hashes")
    ap.add_argument("sessions", nargs="*", help="YEAR:ROUND|auto:path/ (path relative to static/)")
    a = ap.parse_args()
    import sys
    res = {"retrieved_at": dt.datetime.now(dt.timezone.utc).isoformat(), "argv": sys.argv, "results": []}
    specs = a.sessions
    old = None
    if a.verify:
        old = {r["session"]: r for r in json.load(open(a.verify))["results"]}
        specs = [f"{k[:4]}:{v.get('round') or 'auto'}:{k}" for k, v in old.items()]
    for spec in specs:
        y, r, p = spec.split(":", 2)
        res["results"].append(probe(p, a.cache, y, r))
    if old:
        diffs = []
        for r in res["results"]:
            for feed, meta in r["files"].items():
                o = old.get(r["session"], {}).get("files", {}).get(feed, {})
                for key in ("sha256", "last_modified"):
                    if o.get(key) != meta.get(key):
                        diffs.append([r["session"], feed, key, o.get(key), meta.get(key)])
        res["verify_against"] = a.verify
        res["verify_differences"] = diffs
        print(f"verify: {len(diffs)} differences")
    with open(a.out, "w") as f:
        json.dump(res, f, indent=1, default=str)
