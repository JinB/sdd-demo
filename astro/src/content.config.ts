import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";

const blog = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/blog" }),
  schema: z.object({
    title: z.string(),
    category: z.string().default("Uncategorized"),
    tags: z.array(z.string()).default([]),
    date: z.string(),
    excerpt: z.string(),
    image: z.string().optional(),
    wpId: z.number(),
  }),
});

export const collections = { blog };
