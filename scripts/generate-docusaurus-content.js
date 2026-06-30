const fs = require("fs");
const path = require("path");

const postsFile = path.join(process.cwd(), "posts.json");
const blogDir = path.join(process.cwd(), "docusaurus", "blog");

const posts = JSON.parse(fs.readFileSync(postsFile, "utf-8"));

fs.readdirSync(blogDir)
  .filter((f) => f.endsWith(".md") || f.endsWith(".mdx"))
  .forEach((f) => fs.unlinkSync(path.join(blogDir, f)));

posts.forEach((post) => {
  const termArrays = post._embedded?.["wp:term"] ?? [];
  const tags = termArrays.slice(1).flat().map((t) => t.name);

  const slug = post.slug;
  const title = post.title.rendered.replace(/"/g, '\\"');
  const description = post.excerpt.rendered
    .replace(/<[^>]+>/g, "")
    .trim()
    .slice(0, 200)
    .replace(/"/g, '\\"');
  const date = post.date.split("T")[0];
  const body = post.content.rendered
    .replace(/https?:\/\/wp\.4eng\.online\/wp-content\/uploads\//g, "/media/")
    .replace(/<[^>]+>/g, "")
    .trim();

  const md = `---
title: "${title}"
date: ${date}
tags: [${tags.map((t) => JSON.stringify(t)).join(", ")}]
description: "${description}"
---

<!-- truncate -->

${body}
`;

  fs.writeFileSync(path.join(blogDir, `${date}-${slug}.md`), md);
});

console.log(`Generated ${posts.length} blog files in ${blogDir}`);
