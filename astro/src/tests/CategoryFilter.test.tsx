import { render, screen, fireEvent } from "@testing-library/react";
import CategoryFilter from "../components/CategoryFilter";

const posts = [
  { title: "Basketball finals", category: "Sport" as const, slug: "bball", excerpt: "Sport post" },
  { title: "React hooks guide", category: "Software" as const, slug: "react", excerpt: "Software post" },
  { title: "Soccer match", category: "Sport" as const, slug: "soccer", excerpt: "Another sport" },
];

test("shows all posts by default", () => {
  render(<CategoryFilter posts={posts} />);
  expect(screen.getByText("Basketball finals")).toBeInTheDocument();
  expect(screen.getByText("React hooks guide")).toBeInTheDocument();
  expect(screen.getByText("Soccer match")).toBeInTheDocument();
});

test("All button is active by default", () => {
  render(<CategoryFilter posts={posts} />);
  expect(screen.getByRole("button", { name: "All" })).toHaveAttribute("aria-pressed", "true");
});

test("filters to Sport only", () => {
  render(<CategoryFilter posts={posts} />);
  fireEvent.click(screen.getByRole("button", { name: "Sport" }));
  expect(screen.getByText("Basketball finals")).toBeInTheDocument();
  expect(screen.getByText("Soccer match")).toBeInTheDocument();
  expect(screen.queryByText("React hooks guide")).not.toBeInTheDocument();
});

test("filters to Software only", () => {
  render(<CategoryFilter posts={posts} />);
  fireEvent.click(screen.getByRole("button", { name: "Software" }));
  expect(screen.getByText("React hooks guide")).toBeInTheDocument();
  expect(screen.queryByText("Basketball finals")).not.toBeInTheDocument();
});

test("All button restores full list", () => {
  render(<CategoryFilter posts={posts} />);
  fireEvent.click(screen.getByRole("button", { name: "Sport" }));
  fireEvent.click(screen.getByRole("button", { name: "All" }));
  expect(screen.getByText("React hooks guide")).toBeInTheDocument();
});
