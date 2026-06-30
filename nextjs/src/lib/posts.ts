import fs from "fs";
import path from "path";

export interface Post {
  slug: string;
  title: string;
  category: string;
  tags: string[];
  date: string;
  excerpt: string;
  image?: string;
  body: string;
}

export function getPosts(): Post[] {
  const file = path.join(process.cwd(), "src", "data", "posts.json");
  return JSON.parse(fs.readFileSync(file, "utf-8")) as Post[];
}

export function getPost(slug: string): Post | undefined {
  return getPosts().find((p) => p.slug === slug);
}
