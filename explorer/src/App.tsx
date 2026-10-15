import { useState, useEffect, useRef } from "react";
import type { Bundle, Attempt, Row } from "./model";
import {
  loadBundle,
  latest,
  atTime,
  toggle,
  difference,
  percent,
  windowLabel,
  outcomeText,
  overlap,
} from "./model";
import "./style.css";
import DriverPortrait from "./DriverPortrait";
import { loadPositions, positionAt } from "./positions";
import type { PositionBundle, PositionFrame } from "./positions";
const base = import.meta.env.BASE_URL,
  asset = (s: string) => base + "assets/" + s;
function Modal({
  title,
  close,
  children,
}: {
  title: string;
  close: () => void;
  children: React.ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const focus = document.activeElement as HTMLElement;
    ref.current!.showModal();
    return () => focus?.focus();
  }, []);
  return (
    <dialog
      ref={ref}
      onCancel={(e) => {
        e.preventDefault();
        close();
      }}
    >
      <header>
        <h2>{title}</h2>
        <button onClick={close}>Close</button>
      </header>
      {children}
    </dialog>
  );
}
const fmt = (v: number | null, s = false) =>
  v === null ? <span className="unavailable" aria-label="Not available" title="Not available">—</span> : `${s && v > 0 ? "+" : ""}${v.toFixed(3)}`;
export default function App() {
  const [b, setB] = useState<Bundle>();
  const [positions, setPositions] = useState<PositionBundle>();
  const [positionError, setPositionError] = useState("");
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const [open, setOpen] = useState(false);
  const [subject, setSubject] = useState("1");
  const [time, setTime] = useState(0);
  const [order, setOrder] = useState(0);
  const [selection, setSelection] = useState<string[]>([]);
  const [actual, setActual] = useState(false);
  const [history, setHistory] = useState(false);
  const [modal, setModal] = useState("");
  const [tab, setTab] = useState("Race");
  const [mobile, setMobile] = useState("Race timing");
  const [context, setContext] = useState(true);
  useEffect(() => {
    loadBundle(base)
      .then((b) => {
        setB(b);
      })
      .catch((e) => setError(e.message));
  }, [retry]);
  useEffect(() => {
    if (!b || b.kind !== "development") return;
    let active = true;
    setPositions(undefined);
    setPositionError("");
    loadPositions(base, b).then(p => { if (active) setPositions(p); })
      .catch(e => { if (active) setPositionError(e.message); });
    return () => { active = false; };
  }, [b]);
  useEffect(() => {
    if (!b) return;
    function restore() {
      const p = new URLSearchParams(location.hash.slice(1));
      setActual(false);
      if (!p.has("race")) {
        setOpen(false);
        return;
      }
      const id = p.get("driver")!;
      const a = b!.attempts.find(
        (a) => a.driver === id && a.lap === Number(p.get("lap")),
      );
      const t = Number(p.get("time") ?? a?.time);
      const ordinal = Number(p.get("order") ?? a?.order ?? 0);
      if (
        p.get("race") !== b!.id ||
        !b!.drivers.some((d) => d.id === id) ||
        !b!.frames.some((f) => f.time === t && (f.order ?? 0) === ordinal) ||
        (p.get("lap") === "none"
          ? !!latest(b!, id, t, ordinal)
          : !a || latest(b!, id, t, ordinal)?.id !== a.id)
      ) {
        setError("This race, driver or lap is not available.");
        return;
      }
      setSubject(id);
      setTime(t);
      setOrder(ordinal);
      setOpen(true);
    }
    restore();
    window.addEventListener("hashchange", restore);
    return () => window.removeEventListener("hashchange", restore);
  }, [b]);
  const a = b ? latest(b, subject, time, order) : undefined,
    d = b?.drivers.find((d) => d.id === subject),
    attempts =
      b?.attempts
        .filter((x) => x.driver === subject)
        .sort((a, b) => a.time - b.time) || [],
    index = attempts.findIndex((x) => x.id === a?.id),
    frame = b ? atTime(b, time, order) : undefined,
    ref =
      selection.length === 1
        ? frame?.rows.find((r) => r.driver === selection[0])
        : undefined;
  function save(id: string, t: number, ordinal = order) {
    const a = latest(b!, id, t, ordinal);
    location.hash = new URLSearchParams({
      race: b!.id,
      driver: id,
      lap: a ? String(a.lap) : "none",
      time: String(t),
      order: String(ordinal),
    }).toString();
  }
  function choose(x: Attempt) {
    setTime(x.time);
    setOrder(x.order ?? 0);
    setActual(false);
    save(subject, x.time, x.order ?? 0);
  }
  function driver(id: string) {
    setSubject(id);
    setActual(false);
    save(id, time);
  }
  function compare(id: string) {
    setSelection(toggle(selection, id));
  }
  function val(raw: number | null, r: number | null, lapTime = false) {
    if (!ref && lapTime && raw !== null) {
      const ms = Math.round(raw * 1000);
      return `${Math.floor(ms / 60000)}:${((ms % 60000) / 1000).toFixed(3).padStart(6, "0")}`;
    }
    return fmt(ref ? difference(raw, r) : raw, !!ref);
  }
  function fastest(row: Row, v: number | null, get: (r: Row) => number | null) {
    const vs = frame!.rows
      .filter((r) => selection.includes(r.driver))
      .map(get)
      .filter((x): x is number => x !== null);
    return (
      selection.length > 1 &&
      selection.includes(row.driver) &&
      v !== null &&
      vs.length > 1 &&
      v === Math.min(...vs)
    );
  }
  return (
    <main>
      <header className="app-header">
        <a
          href="#"
          onClick={() => {
            setOpen(false);
            setActual(false);
            setSelection([]);
          }}
        >
          Replay Explorer
        </a>
        <span className="muted small">{b?.kind === "development" ? "Historical preview" : "Synthetic preview"}</span>
        <button onClick={() => setModal("about")}>About</button>
      </header>
      {error ? (
        <section role="alert">
          <h1>{error}</h1>
          <button
            onClick={() => {
              location.hash = "";
              setError("");
              setRetry((x) => x + 1);
            }}
          >
            Back to races / Retry
          </button>
        </section>
      ) : !b ? (
        <p role="status">Loading replay…</p>
      ) : !open ? (
        <section className="catalogue">
          <div className="title-row">
            <h1>Races</h1>
            <label>
              Season{" "}
              <select>
                <option>2024</option>
              </select>
            </label>
          </div>
          <article className="race-row">
            <img
              className="outline"
              src={asset(b.raceMetadata?.circuitAsset ?? "circuit.svg")}
              alt={(b.raceMetadata?.circuit ?? "Circuit de Barcelona-Catalunya") + " outline"}
            />
            <div>
              <h2>
                <img className="flag" src={asset(b.raceMetadata?.flag ?? "flag.svg")} alt={b.raceMetadata?.country ?? "Spain"} />{" "}
                {b.race}
              </h2>
              <p>{b.date}</p>
            </div>
            <button
              className="primary"
              onClick={() => {
                setOpen(true);
                setSubject(b.drivers[0].id);
                setTime(0);
                setOrder(b.frames[0].order ?? 0);
                setActual(false);
                setSelection([]);
                save(b.drivers[0].id, 0, b.frames[0].order ?? 0);
              }}
            >
              Open replay
            </button>
          </article>
          <p className="caption">{b.kind === "development" ? "Historical timing and saved forecasts." : "Illustrative timing and forecasts."}</p>
        </section>
      ) : (
        <>
          <div className="title-row">
            <div>
              <button
                className="text-action"
                onClick={() => {
                  setOpen(false);
                  setActual(false);
                  setSelection([]);
                  location.hash = "";
                }}
              >
                Back to races
              </button>
              <h1>
                <img className="flag" src={asset(b.raceMetadata?.flag ?? "flag.svg")} alt={b.raceMetadata?.country ?? "Spain"} />{" "}
                {b.race} <span className="muted">2024</span>
              </h1>
            </div>
            <label>
              Prediction for{" "}
              <select value={subject} onChange={(e) => driver(e.target.value)}>
                {b.drivers.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <section className="prediction">
            <div className="identity">
              <DriverPortrait key={d!.id} src={asset(d!.code + ".png")} code={d!.code} name={d!.name} />
              <div>
                <strong>{d!.name}</strong>
                <p className="muted small">{d!.team}</p>
                {a && a.context.compound && (
                  <span className="tyre">
                    <img
                      src={asset(a.context.compound.toLowerCase() + ".svg")}
                      alt=""
                    />
                    {a.context.compound}, {a.context.age === null ? "age not available" : a.context.age + " laps"}
                  </span>
                )}
              </div>
            </div>
            <div>
              <div className="navigation">
                <button
                  disabled={index <= 0}
                  onClick={() => choose(attempts[index - 1])}
                >
                  Previous
                </button>
                <label>
                  Prediction lap{" "}
                  <select
                    value={a?.lap ?? ""}
                    onChange={(e) =>
                      choose(
                        attempts.find((a) => a.lap === Number(e.target.value))!,
                      )
                    }
                  >
                    {!a && <option value="">Not available yet</option>}
                    {attempts.map((a) => (
                      <option key={a.id} value={a.lap}>
                        {a.lap === 0 ? "Race start" : a.lap}
                      </option>
                    ))}
                  </select>
                </label>
                <button
                  disabled={index >= attempts.length - 1}
                  onClick={() => choose(attempts[index + 1])}
                >
                  Next
                </button>
                <span className="clock">
                  {a?.boundaryAvailable === false ? "Race time uncertain; recorded at " : "Race time "} {Math.floor(time / 60)}:
                  {String(Math.floor(time % 60)).padStart(2, "0")}
                </span>
              </div>
              <input
                aria-label="Prediction lap slider"
                type="range"
                min="0"
                max={attempts.length - 1}
                value={Math.max(0, index)}
                onChange={(e) => choose(attempts[Number(e.target.value)])}
              />
              {a && (a.time < time || a.time === time && (a.order ?? 0) < order) && (
                <p className="notice">
                  Prediction from lap {a.lap}.{" "}
                  <button onClick={() => choose(a)}>
                    Go to prediction lap
                  </button>
                </p>
              )}
              {!a ? (
                <h2>No prediction available yet</h2>
              ) : a.state === "failed" ? (
                <>
                  <h2>No prediction for this lap</h2>
                  <p>
                    {a.reason === "The historical baseline has insufficient training evidence for this lap."
                      ? "This preview was trained on one earlier race. It lacks support for the full remaining race at this lap."
                      : a.reason}{" "}
                    <button onClick={() => setModal("forecast")}>
                      Why unavailable
                    </button>
                  </p>
                </>
              ) : (
                <>
                  <div className="muted small">Next pit stop</div>
                  <div className="window">{windowLabel(a)}</div>
                  <div className="masses">
                    {a.window ? (
                      <>
                        <span>
                          Before lap {a.lap + a.window.a + 1}
                          <b>{percent(a.window.before)}</b>
                        </span>
                        <span>
                          {windowLabel(a)}
                          <b>{percent(a.window.inside)}</b>
                        </span>
                        <span>
                          After{" "}
                          {a.window.b === a.p!.length - 1
                            ? "this window"
                            : "lap " + (a.lap + a.window.b + 1)}
                          <b>{percent(a.window.after)}</b>
                        </span>
                      </>
                    ) : (
                      <>
                        <span>
                          Before window<b>0%</b>
                        </span>
                        <span>
                          In window<b>0%</b>
                        </span>
                        <span>
                          After window<b>0%</b>
                        </span>
                      </>
                    )}
                    <span>
                      No more stops<b>{percent(a.q!)}</b>
                    </span>
                  </div>
                  <button
                    className="text-action"
                    onClick={() => setModal("forecast")}
                  >
                    Full forecast
                  </button>
                </>
              )}
              <div className="secondary">
                <button
                  className="text-action"
                  aria-expanded={history}
                  onClick={() => setHistory(!history)}
                >
                  Earlier predictions
                </button>
                <label>
                  <input
                    type="checkbox"
                    checked={actual}
                    onChange={(e) => setActual(e.target.checked)}
                  />{" "}
                  Show actual stop
                </label>
              </div>
              {actual && a && (
                <div className="actual">
                  <strong>{outcomeText(a)}</strong>
                  <p>{overlap(a)}</p>
                </div>
              )}
              {history && (
                <div className="history">
                  {attempts
                    .filter((x) => x.time < (a?.time ?? 0) || x.time === a?.time && (x.order ?? 0) <= (a?.order ?? 0))
                    .map((x) => (
                      <button key={x.id} onClick={() => choose(x)}>
                        {" "}
                        {x.lap === 0 ? "Race start" : "Lap " + x.lap}
                        <span>
                          {x.state === "failed"
                            ? "No prediction"
                            : windowLabel(x)}
                        </span>
                        {actual && <small>{outcomeText(x)}</small>}
                      </button>
                    ))}
                </div>
              )}
            </div>
          </section>
          <div className="context-control">
            <button
              aria-expanded={context}
              onClick={() => setContext(!context)}
            >
              {context ? "Hide race context" : "Show race context"}
            </button>
            {selection.length > 0 && (
              <button onClick={() => setSelection([])}>Clear selection</button>
            )}
          </div>
          {context && (
            <>
              <div className="mobile-switch">
                {["Race timing", "Track map"].map((x) => (
                  <button
                    key={x}
                    className={mobile === x ? "active" : ""}
                    onClick={() => setMobile(x)}
                  >
                    {x}
                  </button>
                ))}
              </div>
              <div className="race-context">
                <section
                  className={
                    "tower-panel " +
                    (mobile === "Race timing" ? "mobile-visible" : "")
                  }
                >
                  <header className="timing-heading">
                    <h2>Race timing</h2>
                    <span className="caption">{ref ? `Relative to ${b.drivers.find(d => d.id === ref.driver)!.code}` : selection.length > 1 ? `${selection.length} drivers compared` : "Absolute timing"}</span>
                  </header>
                  <div className="tabs" role="tablist" aria-label="Timing view">
                    {[
                      "Race",
                      "Laps",
                      "Last sectors",
                      "Best sectors",
                      "Minis",
                    ].map((x) => (
                      <button
                        role="tab"
                        aria-selected={tab === x}
                        key={x}
                        className={tab === x ? "active" : ""}
                        onClick={() => setTab(x)}
                      >
                        {x}
                      </button>
                    ))}
                  </div>
                  <div className="table-scroll">
                    <table className="timing-table" data-view={tab}>
                      <caption className="sr-only">
                        {tab} at race time {time} seconds
                      </caption>
                      <thead>
                        <tr>
                          <th scope="col">Pos</th>
                          <th scope="col">Driver</th>
                          {(tab === "Race"
                            ? ["Interval", "Gap", "Tyre", "Last lap", "Lap"]
                            : tab === "Laps"
                              ? ["Last lap", "Best lap"]
                              : tab === "Minis"
                                ? ["Performance"]
                                : [
                                    "S1",
                                    "S2",
                                    "S3",
                                    tab === "Last sectors"
                                      ? "Lap"
                                      : "Theoretical",
                                  ]
                          ).map((c) => (
                            <th scope="col" key={c}>{c}</th>
                          ))}
                          <th>
                            <span>Forecast</span>
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {frame?.rows.map((r) => {
                          const d = b.drivers.find((d) => d.id === r.driver)!;
                          const sectors =
                            tab === "Last sectors" ? r.sectors : r.bestSectors;
                          const refSectors = ref
                            ? tab === "Last sectors"
                              ? ref.sectors
                              : ref.bestSectors
                            : [];
                          return (
                            <tr
                              key={r.driver}
                              className={
                                (selection.includes(r.driver) ? "selected " : "") + (subject === r.driver ? "prediction-subject" : "")
                              }
                            >
                              <td>{r.position ?? fmt(null)}</td>
                              <td>
                                <button
                                  className="driver-toggle"
                                  style={{ borderLeftColor: d.color }}
                                  title={`${d.name}: toggle comparison`}
                                  aria-pressed={selection.includes(r.driver)}
                                  onClick={() => compare(r.driver)}
                                >
                                  {d.code}
                                  {r.pit && <span className="pit-marker">Pit</span>}
                                </button>
                              </td>
                              {tab === "Race" ? (
                                <>
                                  <td>{ref ? <span aria-label="Interval not shown in relative mode">—</span> : r.position === 1 ? <span aria-label="No car ahead">—</span> : r.intervalText ?? fmt(r.interval, true)}</td>
                                  <td>{ref ? val(r.gap, ref.gap) : r.position === 1 ? "Leader" : r.gapText ?? fmt(r.gap, true)}</td>
                                  <td>
                                    <span className="tyre">
                                      {r.compound && <img
                                        src={asset(
                                          (r.compound ?? "unavailable").toLowerCase() + ".svg",
                                        )}
                                        alt={r.compound ?? "Tyre not available"}
                                      />}
                                      {r.age === null || (ref && ref.age === null) ? fmt(null) : ref
                                        ? (r.age! - ref.age! > 0 ? "+" : "") +
                                          String(r.age! - ref.age!)
                                        : r.age}
                                    </span>
                                  </td>
                                  <td
                                    className={
                                      fastest(r, r.last, (x) => x.last)
                                        ? "fastest"
                                        : ""
                                    }
                                  >
                                    {val(r.last, ref?.last ?? null, true)}
                                  </td>
                                  <td>{r.completed ?? fmt(null)}</td>
                                </>
                              ) : tab === "Laps" ? (
                                <>
                                  {(["last", "best"] as const).map((k) => (
                                    <td
                                      key={k}
                                      className={
                                        fastest(r, r[k], (x) => x[k])
                                          ? "fastest"
                                          : ""
                                      }
                                    >
                                      {val(r[k], ref?.[k] ?? null, true)}
                                    </td>
                                  ))}
                                </>
                              ) : tab === "Minis" ? (
                                <td>
                                  <span className="mini-strip">
                                    {r.mini.map((s, i) => (
                                      <span
                                        key={i}
                                        className={"mini " + s}
                                        title={
                                          s === "best"
                                            ? "Session best"
                                            : s === "personal"
                                              ? "Personal best"
                                              : s
                                        }
                                        aria-label={`Mini sector ${i + 1}: ${s === "best" ? "session best" : s === "personal" ? "personal best" : s}`}
                                      >
                                        {i + 1}
                                      </span>
                                    ))}
                                  </span>
                                </td>
                              ) : (
                                <>
                                  {sectors.map((v, i) => (
                                    <td
                                      key={i}
                                      className={
                                        fastest(
                                          r,
                                          v,
                                          (x) =>
                                            (tab === "Last sectors"
                                              ? x.sectors
                                              : x.bestSectors)[i],
                                        )
                                          ? "fastest"
                                          : ""
                                      }
                                    >
                                      {val(v, refSectors[i] ?? null)}
                                    </td>
                                  ))}
                                  <td
                                    className={
                                      tab === "Best sectors" &&
                                      fastest(
                                        r,
                                        r.bestSectors.some((v) => v === null)
                                          ? null
                                          : r.bestSectors.reduce<number>(
                                              (s, v) => s + v!,
                                              0,
                                            ),
                                        (x) =>
                                          x.bestSectors.some((v) => v === null)
                                            ? null
                                            : x.bestSectors.reduce<number>(
                                                (s, v) => s + v!,
                                                0,
                                              ),
                                      )
                                        ? "fastest"
                                        : ""
                                    }
                                  >
                                    {tab === "Last sectors"
                                      ? val(r.last, ref?.last ?? null, true)
                                      : val(
                                          sectors.some((v) => v === null)
                                            ? null
                                            : sectors.reduce<number>(
                                                (s, v) => s + v!,
                                                0,
                                              ),
                                          refSectors.some((v) => v === null)
                                            ? null
                                            : refSectors.reduce<number>(
                                                (s, v) => s + v!,
                                                0,
                                              ),
                                          true,
                                        )}
                                  </td>
                                </>
                              )}
                              <td>
                                <button
                                  className="view-prediction"
                                  aria-label={`View prediction for ${d.name}`}
                                  title={`View prediction for ${d.name}`}
                                  aria-current={subject === r.driver ? "true" : undefined}
                                  onClick={() => driver(r.driver)}
                                >
                                  <span aria-hidden="true">↗</span>
                                </button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </section>
                <section
                  className={
                    "map-panel " +
                    (mobile === "Track map" ? "mobile-visible" : "")
                  }
                >
                  <TrackMap
                    b={b}
                    rows={frame?.rows || []}
                    selection={selection}
                    compare={compare}
                    positions={positions}
                    positionFrame={positionAt(positions, time, order)}
                    positionError={positionError}
                  />
                </section>
              </div>
            </>
          )}
        </>
      )}
      {modal && (
        <Modal
          title={modal === "about" ? "About the prediction" : "Full forecast"}
          close={() => setModal("")}
        >
          {modal === "about" ? (
            <>
              <p>
                The forecast estimates when a driver may next enter the pits for
                a tyre change. The highlighted window contains most of the
                chance of a stop; earlier and later stops remain possible. No
                more stops means no further tyre-change stop before the driver
                finishes.
              </p>
              <p>
                {b?.kind === "development" ? "These saved forecasts use a simple historical baseline fitted on the preceding Spanish race. Position samples can be older than the selected race time. Sector comparisons are unavailable. Historical timing is reconstructed with conservative availability bounds." : "This preview uses illustrative timing and forecasts."} Race information can be incomplete, and a prediction can be wrong.
              </p>
              <h3>Image credits</h3>
              <p>
                Driver portraits: Formula 1, cached in{" "}
                <a href="https://github.com/Nelson-Jnrnd/F1_Telemetry_Charts">
                  F1 Telemetry Charts
                </a>
                . Circuit: Jules Roy /{" "}
                <a href="https://github.com/f1db/f1db">F1DB</a>, CC BY 4.0.
                Flag: flag-icons, MIT.
              </p>
            </>
          ) : a?.state === "ok" ? (
            <>
              <p>
                {d!.name}, {a.lap === 0 ? "race start" : "lap " + a.lap}
              </p>
              <p>
                Each value is a chance out of all possible outcomes. The
                highlighted window contains most of the chance of a stop.
              </p>
              <div
                className="distribution"
                role="img"
                aria-label="Full forecast. Exact values in the table below."
              >
                {a.p!.map((p, i) => (
                  <div
                    key={i}
                    style={{ height: `${p * 250}px` }}
                    className={
                      a.window && i >= a.window.a && i <= a.window.b
                        ? "inside"
                        : ""
                    }
                    title={`Lap ${a.lap + i + 1}${i === a.p!.length - 1 ? " or later" : ""}: ${percent(p)}`}
                  />
                ))}
              </div>
              <p>
                Pit-entry laps {a.lap + 1} to {a.lap + a.p!.length} or later
              </p>
              <p>No more stops: {percent(a.q!)}</p>
              {actual && <p>{outcomeText(a)}</p>}
              <details>
                <summary>All lap values</summary>
                <table>
                  <thead>
                    <tr>
                      <th>Pit-entry lap</th>
                      <th>Chance of a stop</th>
                      {actual && <th>Actual stop</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {a.p!.map((p, i) => (
                      <tr key={i}>
                        <td>
                          {a.lap + i + 1}
                          {i === a.p!.length - 1 ? " or later" : ""}
                        </td>
                        <td>{percent(p)}</td>
                        {actual && (
                          <td>
                            {a.outcome.start !== undefined &&
                            a.lap + i + 1 <= a.outcome.end! &&
                            (i === a.p!.length - 1 ||
                              a.lap + i + 1 >= a.outcome.start)
                              ? a.outcome.kind === "bounded"
                                ? "Possible stop"
                                : "Actual stop"
                              : ""}
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </details>
            </>
          ) : (
            <p>{a?.reason ?? "No prediction available yet."}</p>
          )}
        </Modal>
      )}
    </main>
  );
}
function TrackMap({
  b,
  rows,
  selection,
  compare,
  positions,
  positionFrame,
  positionError,
}: {
  b: Bundle;
  rows: Row[];
  selection: string[];
  compare: (id: string) => void;
  positions?: PositionBundle;
  positionFrame?: PositionFrame;
  positionError?: string;
}) {
  const [path, setPath] = useState(""),
    [zoom, setZoom] = useState(1),
    [rotation, setRotation] = useState(0),
    [pan, setPan] = useState({ x: 0, y: 0 }),
    [points, setPoints] = useState<{ id: string; x: number; y: number }[]>([]);
  const ref = useRef<SVGPathElement>(null),
    drag = useRef<{ x: number; y: number } | null>(null);
  useEffect(() => {
    fetch(asset(b.raceMetadata?.circuitAsset ?? "circuit.svg"))
      .then((r) => r.text())
      .then((s) =>
        setPath(
          new DOMParser()
            .parseFromString(s, "image/svg+xml")
            .querySelector("path")
            ?.getAttribute("d") || "",
        ),
      )
      .catch(() => setPath(""));
  }, []);
  useEffect(() => {
    if (!ref.current || !path) return;
    const length = ref.current.getTotalLength();
    setPoints(
      rows
        .filter((r) => r.progress !== null)
        .map((r) => {
          const p = ref.current!.getPointAtLength(r.progress! * length);
          return { id: r.driver, x: p.x, y: p.y };
        }),
    );
  }, [path, rows]);
  const displayPath = positions ? positions.geometry.map((p, i) => `${i ? "L" : "M"}${p[0]} ${p[1]}`).join(" ") + " Z" : path;
  const displayPoints = b.kind === "development" ? positionFrame?.points.map(p => ({ id: p.driver, x: p.x, y: p.y })) ?? [] : points;
  return (
    <>
      <div className="map-controls">
        <h2>Track map</h2>
        <button
          aria-label="Zoom in"
          onClick={() => setZoom((z) => Math.min(3, z + 0.2))}
        >
          +
        </button>
        <button
          aria-label="Zoom out"
          onClick={() => setZoom((z) => Math.max(0.6, z - 0.2))}
        >
          −
        </button>
        <button onClick={() => setRotation((r) => r + 15)}>Rotate</button>
        <button
          onClick={() => {
            setZoom(1);
            setRotation(0);
            setPan({ x: 0, y: 0 });
          }}
        >
          Fit
        </button>
      </div>
      <svg
        className="track"
        viewBox="0 0 540 540"
        aria-label="Circuit map at selected race time. Drag to pan; select drivers to compare."
        onPointerDown={(e) => {
          if (!(e.target as Element).closest('[role="button"]')) {
            drag.current = { x: e.clientX, y: e.clientY };
            e.currentTarget.setPointerCapture(e.pointerId);
          }
        }}
        onPointerMove={(e) => {
          if (drag.current) {
            const s = 540 / e.currentTarget.getBoundingClientRect().width;
            const dx = (e.clientX - drag.current.x) * s;
            const dy = (e.clientY - drag.current.y) * s;
            drag.current = { x: e.clientX, y: e.clientY };
            setPan((p) => ({ x: p.x + dx, y: p.y + dy }));
          }
        }}
        onPointerUp={() => (drag.current = null)}
        onPointerCancel={() => (drag.current = null)}
      >
        <rect width="540" height="540" fill="transparent" pointerEvents="all" aria-hidden="true" />
        <g
          transform={`translate(${pan.x + 20} ${pan.y + 20}) translate(250 250) rotate(${rotation}) scale(${zoom}) translate(-250 -250)`}
        >
          <path ref={ref} d={displayPath} className="circuit" />
          {selection.length === 1 &&
            rows
              .find((r) => r.driver === selection[0])
              ?.mini.filter(state => state !== "unavailable").map((state, i) => (
                <path
                  key={i}
                  d={path}
                  pathLength={6}
                  fill="none"
                  stroke={
                    state === "best"
                      ? "#984ab5"
                      : state === "personal"
                        ? "#269460"
                        : state === "slower"
                          ? "#a59145"
                          : "#8b8b8b"
                  }
                  strokeWidth={7}
                  strokeDasharray="1 6"
                  strokeDashoffset={-i}
                />
              ))}
          {displayPoints.map((p) => {
            const d = b.drivers.find((d) => d.id === p.id)!;
            return (
              <g
                role="button"
                tabIndex={0}
                key={p.id}
                aria-label={`Compare ${d.name}`}
                aria-pressed={selection.includes(p.id)}
                onClick={() => compare(p.id)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    compare(p.id);
                  }
                }}
              >
                <circle
                  cx={p.x}
                  cy={p.y}
                  r={12}
                  fill={d.color}
                  stroke={
                    selection.includes(p.id) ? "var(--ink)" : "var(--paper)"
                  }
                  strokeWidth={selection.includes(p.id) ? 3 : 2}
                />
                <text x={p.x + 17} y={p.y + 4}>
                  {d.code}
                </text>
              </g>
            );
          })}
        </g>
      </svg>
      {!displayPath && <p>Track map unavailable</p>}
      {positionError && <p role="status">{positionError}</p>}
      {positionFrame?.sample && <p className="caption">Positions recorded approximately {Math.round(positionFrame.time - positionFrame.sample.time)} seconds earlier.</p>}
      {(b.kind === "development" ? displayPoints.length < rows.length : rows.some((r) => r.progress === null)) && (
        <p className="caption">
          {b.kind === "development" && !displayPoints.length ? "Positions unavailable. All drivers remain in race timing." : "Some positions unavailable. All drivers remain in race timing."}
        </p>
      )}
      <div className="map-driver-chooser" aria-label="Drivers on track">
        {(b.kind === "development" ? displayPoints.map(p => p.id) : rows.filter(r => r.progress !== null).map(r => r.driver))
          .map((id) => (
            <button
              key={id}
              aria-pressed={selection.includes(id)}
              onClick={() => compare(id)}
            >
              {b.drivers.find((d) => d.id === id)!.code}
            </button>
          ))}
      </div>
      <p className="caption">
        {b.kind === "development" ? positions ? "Track geometry from the preceding qualifying session." : "Car positions unavailable. The circuit outline identifies the layout." : "Illustrative positions on the matching circuit outline."}
        {b.kind === "development" && selection.length > 0
          ? " Sector comparisons unavailable."
          : selection.length > 1
          ? " Sector comparisons unavailable."
          : selection.length === 1
            ? " Purple: session best; green: personal best; yellow: slower; grey: unavailable."
            : ""}
      </p>
    </>
  );
}
