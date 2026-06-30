const fs = require("fs");
const path = require("path");

const postsFile = path.join(process.cwd(), "posts.json");
const contentDir = path.join(process.cwd(), "astro", "src", "content", "blog");

const WP_UPLOADS_RE = /https?:\/\/[^/]+\/wp-content\/uploads\//g;
const MEDIA_BASE = "https://astro.4eng.online/media/";

function extractImage(post) {
  const featured = post._embedded?.["wp:featuredmedia"]?.[0]?.source_url;
  if (featured) return featured.replace(WP_UPLOADS_RE, MEDIA_BASE);
  const match = post.content.rendered.match(/<img[^>]+src="([^"]+)"/i);
  if (match) return match[1].replace(WP_UPLOADS_RE, MEDIA_BASE);
  return null;
}

const posts = JSON.parse(fs.readFileSync(postsFile, "utf-8"));

fs.readdirSync(contentDir)
  .filter((f) => f.endsWith(".md"))
  .forEach((f) => fs.unlinkSync(path.join(contentDir, f)));

posts.forEach((post) => {
  const termArrays = post._embedded?.["wp:term"] ?? [];
  const wpCategories = termArrays[0] ?? [];
  const wpTags = termArrays.slice(1).flat();

  const catName = wpCategories[0]?.name ?? "Uncategorized";
  const tags = wpTags.map((t) => t.name);
  const image = extractImage(post);

  const slug = post.slug;
  const title = post.title.rendered.replace(/"/g, '\\"');
  const rawExcerpt = post.excerpt.rendered.replace(/<[^>]+>/g, "").trim();
  const excerpt = rawExcerpt.slice(0, 200).replace(/"/g, '\\"');
  const date = post.date.split("T")[0];
  const body = post.content.rendered
    .replace(WP_UPLOADS_RE, MEDIA_BASE)
    .replace(/<[^>]+>/g, "")
    .trim();

  const fields = [
    `title: "${title}"`,
    `category: "${catName}"`,
    `tags: [${tags.map((t) => JSON.stringify(t)).join(", ")}]`,
    `date: "${date}"`,
    `excerpt: "${excerpt}"`,
    `wpId: ${post.id}`,
    image && `image: "${image}"`,
  ].filter(Boolean).join("\n");

  const md = `---\n${fields}\n---\n\n${body}\n`;

  fs.writeFileSync(path.join(contentDir, `${slug}.md`), md);
});

console.log(`Generated ${posts.length} content files in ${contentDir}`);
