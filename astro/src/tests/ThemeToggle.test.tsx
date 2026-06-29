// astro/src/tests/ThemeToggle.test.tsx
import { render, screen, fireEvent } from "@testing-library/react";
import { vi, beforeEach, afterEach } from "vitest";
import ThemeToggle from "../components/ThemeToggle";

let originalMatchMedia: typeof window.matchMedia;

beforeEach(() => {
  localStorage.clear();
  document.documentElement.className = "";
  originalMatchMedia = window.matchMedia;
  Object.defineProperty(window, "matchMedia", {
    value: vi.fn((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
    writable: true,
    configurable: true,
  });
});

afterEach(() => {
  Object.defineProperty(window, "matchMedia", {
    value: originalMatchMedia,
    writable: true,
    configurable: true,
  });
});

test("renders a toggle button", () => {
  render(<ThemeToggle />);
  expect(screen.getByRole("button")).toBeInTheDocument();
});

test("defaults to light mode when no preference stored", () => {
  render(<ThemeToggle />);
  expect(document.documentElement.classList.contains("dark")).toBe(false);
});

test("clicking toggle switches to dark mode", () => {
  render(<ThemeToggle />);
  fireEvent.click(screen.getByRole("button"));
  expect(document.documentElement.classList.contains("dark")).toBe(true);
});

test("dark mode persists to localStorage", () => {
  render(<ThemeToggle />);
  fireEvent.click(screen.getByRole("button"));
  expect(localStorage.getItem("theme")).toBe("dark");
});

test("clicking twice returns to light mode", () => {
  render(<ThemeToggle />);
  fireEvent.click(screen.getByRole("button"));
  fireEvent.click(screen.getByRole("button"));
  expect(document.documentElement.classList.contains("dark")).toBe(false);
  expect(localStorage.getItem("theme")).toBe("light");
});

test("respects stored dark preference on mount", () => {
  localStorage.setItem("theme", "dark");
  render(<ThemeToggle />);
  expect(document.documentElement.classList.contains("dark")).toBe(true);
});
