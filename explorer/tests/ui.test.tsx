// @vitest-environment jsdom
import {
  render,
  screen,
  fireEvent,
  waitFor,
  cleanup,
  within,
} from "@testing-library/react";
import { afterEach, beforeEach, it, expect, vi } from "vitest";
import App from "../src/App";
import fixture from "../public/synthetic.json";
beforeEach(() => {
  location.hash = "";
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(structuredClone(fixture)),
        text: () => Promise.resolve('<svg><path d="M0 0L500 500"/></svg>'),
      }),
    ),
  );
  HTMLDialogElement.prototype.showModal = function () {
    this.setAttribute("open", "");
  };
  Object.defineProperty(SVGElement.prototype, "getTotalLength", {
    configurable: true,
    value: () => 100,
  });
  Object.defineProperty(SVGElement.prototype, "getPointAtLength", {
    configurable: true,
    value: (n: number) => ({ x: n, y: n }),
  });
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
async function open() {
  render(<App />);
  fireEvent.click(await screen.findByRole("button", { name: "Open replay" }));
  await screen.findByText("Race time 0:00");
}
it("keeps comparison selection independent, shared with map, and changes relative mode", async () => {
  await open();
  fireEvent.click(
    within(screen.getByRole("table")).getByRole("button", {
      name: "VER",
      exact: true,
    }),
  );
  expect(screen.getByText("Relative to VER")).toBeTruthy();
  expect(
    screen
      .getByRole("button", { name: "Compare Max Verstappen" })
      .getAttribute("aria-pressed"),
  ).toBe("true");
  expect(
    (screen.getByLabelText("Prediction for") as HTMLSelectElement).value,
  ).toBe("1");
  fireEvent.click(
    within(screen.getByRole("table")).getByRole("button", {
      name: "NOR",
      exact: true,
    }),
  );
  expect(screen.getByText("2 drivers compared")).toBeTruthy();
  fireEvent.click(
    screen.getByRole("button", { name: "Compare Max Verstappen" }),
  );
  expect(screen.getByText("Relative to NOR")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Clear selection" }));
  expect(screen.queryByText("Relative to NOR")).toBeNull();
});
it("preserves fixed clock for older failed prediction and explicitly moves back on request", async () => {
  await open();
  fireEvent.change(screen.getByLabelText("Prediction lap"), {
    target: { value: "20" },
  });
  await screen.findByText("Race time 26:40");
  fireEvent.click(
    screen.getByRole("button", { name: "View prediction for Lando Norris" }),
  );
  await screen.findByText(/Prediction from lap 18/);
  expect(screen.getByText("Race time 26:40")).toBeTruthy();
  expect(screen.getByText("No prediction for this lap")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Go to prediction lap" }));
  await screen.findByText("Race time 24:12");
});
it("restores hash navigation and missing-attempt states without fabricating lap zero", async () => {
  await open();
  fireEvent.change(screen.getByLabelText("Prediction for"), {
    target: { value: "44" },
  });
  await screen.findByText("No prediction available yet");
  expect(location.hash).toContain("lap=none");
  location.hash = "race=synthetic-spain-2024-v1&driver=1&lap=20&time=1600";
  window.dispatchEvent(new HashChangeEvent("hashchange"));
  await screen.findByText("Race time 26:40");
  expect(
    (screen.getByLabelText("Prediction for") as HTMLSelectElement).value,
  ).toBe("1");
  location.hash = "";
  window.dispatchEvent(new HashChangeEvent("hashchange"));
  await screen.findByRole("button", { name: "Open replay" });
});
it("outcome toggles do not change forecast or clock and zero probabilities stay zero", async () => {
  await open();
  fireEvent.change(screen.getByLabelText("Prediction lap"), {
    target: { value: "20" },
  });
  await screen.findByText("Race time 26:40");
  const window =
    screen.getByText("Next pit stop").nextElementSibling!.textContent;
  fireEvent.click(screen.getByLabelText("Show actual stop"));
  expect(screen.getByText("Actual stop: lap 26")).toBeTruthy();
  expect(
    screen.getByText("Next pit stop").nextElementSibling!.textContent,
  ).toBe(window);
  expect(screen.getByText("Race time 26:40")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Full forecast" }));
  expect(
    within(screen.getByRole("dialog")).getByText("Actual stop: lap 26"),
  ).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Close" }));
  fireEvent.change(screen.getByLabelText("Prediction lap"), {
    target: { value: "65" },
  });
  await screen.findByText("No further stop predicted");
  fireEvent.click(screen.getByRole("button", { name: "Full forecast" }));
  expect(
    document.querySelector<HTMLElement>(".distribution>div")!.style.height,
  ).toBe("0px");
});
it("replacement timing tabs keep only chosen columns and missing positions retain all rows", async () => {
  await open();
  fireEvent.change(screen.getByLabelText("Prediction lap"), {
    target: { value: "18" },
  });
  await screen.findByText(/Some positions unavailable/);
  expect(
    screen.getAllByRole("button", { name: /View prediction for/ }),
  ).toHaveLength(3);
  fireEvent.click(screen.getByRole("tab", { name: "Best sectors" }));
  expect(
    screen.getByRole("columnheader", { name: "Theoretical" }),
  ).toBeTruthy();
  expect(screen.queryByRole("columnheader", { name: "Interval" })).toBeNull();
  fireEvent.click(screen.getByRole("tab", { name: "Minis" }));
  expect(
    screen.getByRole("columnheader", { name: "Performance" }),
  ).toBeTruthy();
});

it("marks only intersecting outcome bins including the open-final boundary", async () => {
  await open();
  fireEvent.change(screen.getByLabelText("Prediction lap"), {
    target: { value: "20" },
  });
  await screen.findByText("Race time 26:40");
  fireEvent.click(screen.getByLabelText("Show actual stop"));
  fireEvent.click(screen.getByRole("button", { name: "Full forecast" }));
  fireEvent.click(screen.getByText("All lap values"));
  const table = within(screen.getByRole("dialog")).getByRole("table");
  const rows = within(table).getAllByRole("row");
  expect(
    rows.filter(
      (r) =>
        r.textContent?.includes("Actual stop") &&
        !r.textContent?.includes("Chance"),
    ),
  ).toHaveLength(1);
  expect(
    rows.find((r) => r.children[0]?.textContent === "26")?.children[2]
      .textContent,
  ).toBe("Actual stop");
  expect(rows.at(-1)?.children[2].textContent).toBe("");
});
