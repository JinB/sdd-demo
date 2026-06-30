import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";

const blog = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/blog" }),
  schema: z.object({
    title: z.string(),
    category: z.enum(["Sport", "Travel", "Uncategorized"]),
    date: z.string(),
    excerpt: z.string(),
    wpId: z.number(),
  }),
});

export const collections = { blog };
