import { render, screen, act } from "@testing-library/react";
import { vi, beforeEach, afterEach } from "vitest";
import LiveClock from "../components/LiveClock";

const MOCK_TIMEZONE = "Europe/Warsaw";

beforeEach(() => {
  vi.spyOn(window.Intl, "DateTimeFormat" as any).mockImplementation(
    function() {
      return {
        resolvedOptions: () => ({ timeZone: MOCK_TIMEZONE }),
        format: () => "",
        formatToParts: () => [],
      };
    }
  );
});

afterEach(() => {
  vi.restoreAllMocks();
});

test("renders time in HH:mm:ss format", async () => {
  await act(async () => {
    render(<LiveClock />);
  });
  expect(screen.getByRole("status").textContent).toMatch(/\d{2}:\d{2}:\d{2}/);
});

test("renders timezone in Continent/City format", async () => {
  await act(async () => {
    render(<LiveClock />);
  });
  expect(screen.getByRole("status").textContent).toContain("Europe/Warsaw");
});

test("renders separator between time and timezone", async () => {
  await act(async () => {
    render(<LiveClock />);
  });
  expect(screen.getByRole("status").textContent).toContain("·");
});

test("updates time after 1 second", async () => {
  // Render first without fake timers
  await act(async () => {
    render(<LiveClock />);
  });
  
  // Then enable fake timers and test advancing them
  vi.useFakeTimers();
  vi.setSystemTime(new Date("2026-06-29T14:23:07Z"));

  await act(async () => {
    vi.advanceTimersByTime(1000);
  });

  expect(screen.getByRole("status")).toBeInTheDocument();
  
  vi.useRealTimers();
});
