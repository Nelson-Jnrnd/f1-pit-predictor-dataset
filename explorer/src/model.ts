export type Driver = {
  id: string;
  code: string;
  name: string;
  team: string;
  color: string;
};
export type Window = {
  a: number;
  b: number;
  before: number;
  inside: number;
  after: number;
};
export type Outcome = {
  kind: "exact" | "bounded" | "none" | "uncertain" | "unavailable";
  start?: number;
  end?: number;
};
export type Attempt = {
  id: string;
  driver: string;
  lap: number;
  time: number;
  episode: string;
  context: { compound: string; age: number };
  state: "ok" | "failed";
  reason?: string;
  p?: number[];
  q?: number;
  window?: Window | null;
  outcome: Outcome;
};
export type Row = {
  driver: string;
  position: number | null;
  gap: number | null;
  interval: number | null;
  completed: number;
  compound: string;
  age: number;
  last: number | null;
  best: number | null;
  sectors: (number | null)[];
  bestSectors: (number | null)[];
  mini: string[];
  progress: number | null;
  pit: boolean;
};
export type Frame = { time: number; rows: Row[] };
export type Bundle = {
  schema: number;
  id: string;
  kind: "synthetic";
  race: string;
  season: number;
  date: string;
  distance: number;
  drivers: Driver[];
  attempts: Attempt[];
  frames: Frame[];
};
export const latest = (bundle: Bundle, driver: string, time: number) =>
  bundle.attempts
    .filter((a) => a.driver === driver && a.time <= time)
    .sort((a, b) => b.time - a.time)[0];
export const atTime = (bundle: Bundle, time: number) =>
  bundle.frames.find((f) => f.time === time);
export function toggle(ids: string[], id: string) {
  return ids.includes(id) ? ids.filter((x) => x !== id) : [...ids, id];
}
export function difference(value: number | null, ref: number | null) {
  return value === null || ref === null ? null : value - ref;
}
export function outcomeText(a: Attempt) {
  const o = a.outcome;
  if (o.kind === "none") return "Did not stop again";
  if (o.kind === "uncertain") return "Actual stop uncertain";
  if (o.kind === "unavailable") return "Actual stop unavailable";
  return `Actual stop: ${o.start === o.end ? "lap " + o.start : "laps " + o.start + "–" + o.end}`;
}
export function overlap(a: Attempt) {
  if (!a.window || !["exact", "bounded"].includes(a.outcome.kind)) return "";
  const lo = a.lap + a.window.a + 1,
    hi = a.window.b === a.p!.length - 1 ? Infinity : a.lap + a.window.b + 1;
  const { start, end } = a.outcome;
  if (start! >= lo && end! <= hi) return "Fully inside the window";
  if (end! < lo || start! > hi) return "Fully outside the window";
  return "The actual stop may have been inside or outside this window.";
}
export function validate(value: unknown): Bundle {
  const fail = () => {
    throw Error("This replay cannot be opened.");
  };
  const b = value as Bundle;
  const finite = (v: unknown): v is number =>
    typeof v === "number" && Number.isFinite(v);
  const integer = (v: unknown) => finite(v) && Number.isInteger(v);
  const text = (v: unknown) => typeof v === "string" && v.length > 0;
  const nums = (v: unknown) =>
    Array.isArray(v) &&
    v.length === 3 &&
    v.every((x) => x === null || (finite(x) && x >= 0));
  if (
    !b ||
    b.schema !== 1 ||
    b.kind !== "synthetic" ||
    !text(b.id) ||
    !text(b.race) ||
    !text(b.date) ||
    !integer(b.season) ||
    !integer(b.distance) ||
    b.distance <= 0 ||
    !Array.isArray(b.drivers) ||
    !b.drivers.length ||
    !Array.isArray(b.attempts) ||
    !Array.isArray(b.frames)
  )
    fail();
  const ids = new Set(b.drivers.map((d) => d.id));
  if (
    ids.size !== b.drivers.length ||
    b.drivers.some((d) => ![d.id, d.code, d.name, d.team, d.color].every(text))
  )
    fail();
  const frames = new Set<number>();
  for (const f of b.frames) {
    if (
      !finite(f.time) ||
      f.time < 0 ||
      frames.has(f.time) ||
      !Array.isArray(f.rows) ||
      f.rows.length !== ids.size ||
      new Set(f.rows.map((r) => r.driver)).size !== ids.size
    )
      fail();
    frames.add(f.time);
    for (const r of f.rows) {
      if (
        !ids.has(r.driver) ||
        (r.position !== null && (!integer(r.position) || r.position < 1)) ||
        ![r.gap, r.interval, r.last, r.best].every(
          (v) => v === null || (finite(v) && v >= 0),
        ) ||
        !integer(r.completed) ||
        r.completed < 0 ||
        !integer(r.age) ||
        r.age < 0 ||
        !["Medium", "Soft", "Hard"].includes(r.compound) ||
        !nums(r.sectors) ||
        !nums(r.bestSectors) ||
        !Array.isArray(r.mini) ||
        r.mini.length !== 6 ||
        r.mini.some(
          (v) => !["best", "personal", "slower", "unavailable"].includes(v),
        ) ||
        typeof r.pit !== "boolean" ||
        (r.progress !== null &&
          (!finite(r.progress) || r.progress < 0 || r.progress > 1))
      )
        fail();
    }
  }
  const keys = new Set<string>(),
    attemptIds = new Set<string>();
  for (const a of b.attempts) {
    const key = a.driver + ":" + a.lap;
    if (
      !ids.has(a.driver) ||
      !text(a.id) ||
      attemptIds.has(a.id) ||
      keys.has(key) ||
      !text(a.episode) ||
      !finite(a.time) ||
      a.time < 0 ||
      !frames.has(a.time) ||
      !integer(a.lap) ||
      a.lap < 0 ||
      a.lap > b.distance ||
      !a.context ||
      !["Medium", "Soft", "Hard"].includes(a.context.compound) ||
      !integer(a.context.age) ||
      a.context.age < 0
    )
      fail();
    keys.add(key);
    attemptIds.add(a.id);
    if (
      !a.outcome ||
      !["exact", "bounded", "none", "uncertain", "unavailable"].includes(
        a.outcome.kind,
      )
    )
      fail();
    if (
      ["exact", "bounded"].includes(a.outcome.kind) &&
      (!integer(a.outcome.start) ||
        !integer(a.outcome.end) ||
        a.outcome.start! <= a.lap ||
        a.outcome.end! < a.outcome.start! ||
        (a.outcome.kind === "exact" && a.outcome.start !== a.outcome.end))
    )
      fail();
    if (a.state === "failed") {
      if (
        !text(a.reason) ||
        a.p !== undefined ||
        a.q !== undefined ||
        a.window !== undefined
      )
        fail();
      continue;
    }
    if (a.state !== "ok" || a.lap === b.distance) fail();
    const p = a.p!,
      q = a.q!;
    if (
      !Array.isArray(p) ||
      p.length !== Math.max(1, b.distance - a.lap) ||
      ![...p, q].every((v) => finite(v) && v >= 0 && v <= 1) ||
      Math.abs(p.reduce((s, v) => s + v, 0) + q - 1) > 1e-9
    )
      fail();
    const w = a.window;
    if (q === 1) {
      if (w !== null || p.some((v) => v !== 0)) fail();
      continue;
    }
    if (
      !w ||
      !integer(w.a) ||
      !integer(w.b) ||
      w.a < 0 ||
      w.b >= p.length ||
      w.a > w.b ||
      ![w.before, w.inside, w.after].every((v) => finite(v) && v >= 0 && v <= 1)
    )
      fail();
    const sum = (from: number, to: number) =>
      p.slice(from, to).reduce((s, v) => s + v, 0);
    if (
      Math.abs(w!.before - sum(0, w!.a)) > 1e-9 ||
      Math.abs(w!.inside - sum(w!.a, w!.b + 1)) > 1e-9 ||
      Math.abs(w!.after - sum(w!.b + 1, p.length)) > 1e-9
    )
      fail();
    // Conformance check only. The displayed summary remains the exported one.
    let best: { a: number; b: number; mass: number } | undefined;
    const target = 0.8 * sum(0, p.length);
    for (let i = 0; i < p.length; i++) {
      let mass = 0;
      for (let j = i; j < p.length; j++) {
        mass += p[j];
        if (
          mass >= target - 1e-12 &&
          (!best ||
            j - i < best.b - best.a ||
            (j - i === best.b - best.a &&
              (mass > best.mass || (mass === best.mass && i < best.a))))
        )
          best = { a: i, b: j, mass };
      }
    }
    if (best?.a !== w!.a || best?.b !== w!.b) fail();
  }
  for (const id of ids) {
    const xs = b.attempts
      .filter((a) => a.driver === id)
      .sort((a, b) => a.lap - b.lap);
    if (xs.some((a, i) => i > 0 && a.time <= xs[i - 1].time)) fail();
  }
  return b;
}
export const percent = (n: number) =>
  `${(n * 100).toFixed(1).replace(/\.0$/, "")}%`;
export function windowLabel(a: Attempt) {
  if (!a.window) return "No further stop predicted";
  const start = a.lap + a.window.a + 1,
    end = a.lap + a.window.b + 1;
  return a.window.b === a.p!.length - 1
    ? `Lap ${start} to ${end} or later`
    : `Laps ${start}–${end}`;
}
