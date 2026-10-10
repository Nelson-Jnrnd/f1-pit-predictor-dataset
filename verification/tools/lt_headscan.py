"""Last-Modified census of race-session TimingData files (Issue #35, finding F-A1).

Verification tooling only. For every Jolpica-calendar race of the requested seasons,
locate the archive race-session path (season Index.json when listed, otherwise the
conventional path built from date and race name, which also covers sessions missing
from the index), issue an HTTP HEAD for TimingData.jsonStream, and record status,
Last-Modified, ETag and whether the path came from the index.

Usage: python -I lt_headscan.py --cache DIR --out headscan.json 2018 2019 ...
"""
import argparse, datetime as dt, json, os, sys, urllib.parse, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # works under python -I
from lt_probe import jolpica_cached

UA = {"User-Agent": "f1-v2-verification"}
BASE = "https://livetiming.formula1.com/static/"


def head(url):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=UA, method="HEAD"), timeout=30)
        return r.status, r.headers.get("Last-Modified"), r.headers.get("ETag")
    except urllib.error.HTTPError as e:
        return e.code, None, None
    except Exception as e:  # network error is evidence too
        return repr(e), None, None


def index_paths(year):
    try:
        raw = urllib.request.urlopen(urllib.request.Request(f"{BASE}{year}/Index.json", headers=UA), timeout=60).read()
    except Exception as e:
        return {}, repr(e)
    idx = json.loads(raw.decode("utf-8-sig"))
    paths = {}
    for m in idx["Meetings"]:
        for s in m["Sessions"]:
            if s.get("Name") == "Race" and s.get("Path"):
                paths[s["Path"].strip("/").split("/")[-1][:10]] = s["Path"]
    return paths, None


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True); ap.add_argument("--out", required=True); ap.add_argument("years", nargs="+")
    a = ap.parse_args()
    rows = []
    for y in a.years:
        paths, err = index_paths(y)
        races = jolpica_cached(f"{y}.json?limit=100", a.cache)[0]["MRData"]["RaceTable"]["Races"]
        for r in races:
            date = dt.date.fromisoformat(r["date"])
            p = next((paths[(date + dt.timedelta(days=k)).isoformat()] for k in (0, -1, 1)
                      if (date + dt.timedelta(days=k)).isoformat() in paths), None)
            src = "index" if p else "guess"
            if not p:
                p = f"{y}/{r['date']}_{r['raceName'].replace(' ', '_')}/{r['date']}_Race/"
            st, lm, et = head(BASE + urllib.parse.quote(p) + "TimingData.jsonStream")
            lm_date = dt.datetime.strptime(lm, "%a, %d %b %Y %H:%M:%S GMT").date().isoformat() if lm else None
            rows.append({"season": int(y), "round": int(r["round"]), "race_date": r["date"], "path": p, "path_source": src,
                         "index_error": err, "status": st, "last_modified": lm, "etag": et,
                         "race_day_written": bool(lm_date) and 0 <= (dt.date.fromisoformat(lm_date) - date).days <= 1})
    json.dump({"argv": sys.argv, "retrieved_at": dt.datetime.now(dt.timezone.utc).isoformat(), "rows": rows},
              open(a.out, "w"), indent=1)
