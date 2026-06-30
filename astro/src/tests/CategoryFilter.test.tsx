import { render, screen, fireEvent } from "@testing-library/react";
import CategoryFilter from "../components/CategoryFilter";

const posts = [
  { title: "Basketball finals", category: "Sport", slug: "bball", excerpt: "Sport post" },
  { title: "Travel to Tokyo", category: "Travel", slug: "tokyo", excerpt: "Travel post" },
  { title: "General update", category: "Uncategorized", slug: "general", excerpt: "Misc post" },
];

test("shows all posts by default", () => {
  render(<CategoryFilter posts={posts} />);
  expect(screen.getByText("Basketball finals")).toBeInTheDocument();
  expect(screen.getByText("Travel to Tokyo")).toBeInTheDocument();
  expect(screen.getByText("General update")).toBeInTheDocument();
});

test("All button is active by default", () => {
  render(<CategoryFilter posts={posts} />);
  expect(screen.getByRole("button", { name: "All" })).toHaveAttribute("aria-pressed", "true");
});

test("filters to Sport only", () => {
  render(<CategoryFilter posts={posts} />);
  fireEvent.click(screen.getByRole("button", { name: "Sport" }));
  expect(screen.getByText("Basketball finals")).toBeInTheDocument();
  expect(screen.queryByText("Travel to Tokyo")).not.toBeInTheDocument();
  expect(screen.queryByText("General update")).not.toBeInTheDocument();
});

test("filters to Travel only", () => {
  render(<CategoryFilter posts={posts} />);
  fireEvent.click(screen.getByRole("button", { name: "Travel" }));
  expect(screen.getByText("Travel to Tokyo")).toBeInTheDocument();
  expect(screen.queryByText("Basketball finals")).not.toBeInTheDocument();
});

test("filters to Uncategorized only", () => {
  render(<CategoryFilter posts={posts} />);
  fireEvent.click(screen.getByRole("button", { name: "Uncategorized" }));
  expect(screen.getByText("General update")).toBeInTheDocument();
  expect(screen.queryByText("Basketball finals")).not.toBeInTheDocument();
});

test("All button restores full list", () => {
  render(<CategoryFilter posts={posts} />);
  fireEvent.click(screen.getByRole("button", { name: "Sport" }));
  fireEvent.click(screen.getByRole("button", { name: "All" }));
  expect(screen.getByText("Travel to Tokyo")).toBeInTheDocument();
  expect(screen.getByText("General update")).toBeInTheDocument();
});
