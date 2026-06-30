const fs = require("fs");
const path = require("path");

const postsFile = path.join(process.cwd(), "posts.json");
const contentDir = path.join(process.cwd(), "astro", "src", "content", "blog");

const posts = JSON.parse(fs.readFileSync(postsFile, "utf-8"));

// Clear existing markdown files
fs.readdirSync(contentDir)
  .filter((f) => f.endsWith(".md"))
  .forEach((f) => fs.unlinkSync(path.join(contentDir, f)));

const ALLOWED_CATEGORIES = new Set(["Sport", "Travel", "Uncategorized"]);

posts.forEach((post) => {
  const terms = post._embedded?.["wp:term"]?.[0] ?? [];
  const catName = terms.find((t) => ALLOWED_CATEGORIES.has(t.name))?.name ?? "Uncategorized";
  const slug = post.slug;
  const title = post.title.rendered.replace(/"/g, '\\"');
  const rawExcerpt = post.excerpt.rendered.replace(/<[^>]+>/g, "").trim();
  const excerpt = rawExcerpt.slice(0, 200).replace(/"/g, '\\"');
  const date = post.date.split("T")[0];
  const body = post.content.rendered
    .replace(/https?:\/\/wp\.4eng\.online\/wp-content\/uploads\//g, "/media/")
    .replace(/<[^>]+>/g, "")
    .trim();

  const md = `---
title: "${title}"
category: "${catName}"
date: "${date}"
excerpt: "${excerpt}"
wpId: ${post.id}
---

${body}
`;

  fs.writeFileSync(path.join(contentDir, `${slug}.md`), md);
});

console.log(`Generated ${posts.length} content files in ${contentDir}`);
