import { describe, it, expect } from "vitest";
import fixture from "../public/synthetic.json";
import {
  validate,
  latest,
  atTime,
  toggle,
  difference,
  overlap,
  windowLabel,
} from "./model";
const b = validate(fixture);
describe("synthetic historical presentation", () => {
  it("rejects protected data and invalid probabilities without repair", () => {
    const x = structuredClone(fixture);
    x.kind = "final";
    expect(() => validate(x)).toThrow();
    const y = structuredClone(fixture);
    y.attempts[0].q = 0.7;
    expect(() => validate(y)).toThrow();
  });
  it("rejects missing grid bins, incorrect summary and duplicate attempts", () => {
    const x = structuredClone(fixture);
    x.attempts[0].p!.pop();
    expect(() => validate(x)).toThrow();
    const y = structuredClone(fixture);
    y.attempts[0].window!.inside = 0.9;
    expect(() => validate(y)).toThrow();
    const z = structuredClone(fixture);
    z.attempts.push(z.attempts[0]);
    expect(() => validate(z)).toThrow();
  });
  it("retains a failed latest attempt instead of older success", () => {
    expect(latest(b, "1", 1440)?.state).toBe("failed");
    expect(latest(b, "1", 1439)?.lap).toBe(16);
  });
  it("keeps a fixed whole-field clock and driver-relative older attempts", () => {
    expect(latest(b, "1", 1600)?.lap).toBe(20);
    expect(latest(b, "4", 1600)?.lap).toBe(18);
    expect(latest(b, "4", 1600)?.state).toBe("failed");
    expect(atTime(b, 1600)?.rows.find((r) => r.driver === "4")?.completed).toBe(
      19,
    );
    expect(atTime(b, 1600)?.time).toBe(1600);
  });
  it("retains missing positions in tower and supports valid no-event mass", () => {
    expect(atTime(b, 1440)?.rows).toHaveLength(3);
    expect(
      atTime(b, 1440)?.rows.find((r) => r.driver === "44")?.progress,
    ).toBeNull();
    const a = latest(b, "1", 5200)!;
    expect(a.q).toBe(1);
    expect(a.p!.every((v) => v === 0)).toBe(true);
    expect(windowLabel(a)).toBe("No further stop predicted");
  });
  it("preserves all probability mass and full open-final grids", () => {
    for (const a of b.attempts.filter((a) => a.state === "ok")) {
      expect(a.p!.reduce((s, v) => s + v, 0) + a.q!).toBeCloseTo(1, 10);
      expect(a.p!.length).toBe(Math.max(1, 66 - a.lap));
      if (a.window)
        expect(
          a.window.before + a.window.inside + a.window.after + a.q!,
        ).toBeCloseTo(1, 10);
    }
  });
  it("supports zero/one/multiple independent selection and missing comparisons", () => {
    expect(toggle(["1", "4"], "1")).toEqual(["4"]);
    expect(toggle(["1"], "4")).toEqual(["1", "4"]);
    expect(toggle(["1"], "1")).toEqual([]);
    expect(difference(null, 80)).toBeNull();
    expect(difference(80, 80)).toBe(0);
  });
  it("preserves prediction while showing uncertain partial outcome overlap", () => {
    const a = structuredClone(latest(b, "1", 1600)!);
    a.outcome = { kind: "bounded", start: 1, end: 66 };
    const before = JSON.stringify(a);
    expect(overlap(a)).toContain("may have been inside or outside");
    expect(JSON.stringify(a)).toBe(before);
  });
});

it("rejects malformed consumed timing, missing/NaN window masses and past outcomes", () => {
  for (const mutate of [
    (x: any) => delete x.attempts[0].window.inside,
    (x: any) => (x.attempts[0].window.a = 0.5),
    (x: any) => (x.attempts[0].window.after = NaN),
    (x: any) => (x.frames[0].rows[0].sectors = null),
    (x: any) => (x.attempts[0].outcome.start = 0),
    (x: any) => x.frames.push(x.frames[0]),
  ]) {
    const x = structuredClone(fixture);
    mutate(x);
    expect(() => validate(x)).toThrow();
  }
});
it("has no fabricated start attempt for an unavailable subject", () => {
  expect(latest(b, "44", 0)).toBeUndefined();
});
