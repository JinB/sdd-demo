const fs = require("fs");
const path = require("path");

const postsFile = path.join(process.cwd(), "posts.json");
const blogDir = path.join(process.cwd(), "docusaurus", "blog");

const WP_UPLOADS_RE = /https?:\/\/[^/]+\/wp-content\/uploads\//g;
const MEDIA_BASE = "https://docu.4eng.online/media/";

function extractImage(post) {
  const featured = post._embedded?.["wp:featuredmedia"]?.[0]?.source_url;
  if (featured) return featured.replace(WP_UPLOADS_RE, MEDIA_BASE);
  const match = post.content.rendered.match(/<img[^>]+src="([^"]+)"/i);
  if (match) return match[1].replace(WP_UPLOADS_RE, MEDIA_BASE);
  return null;
}

const posts = JSON.parse(fs.readFileSync(postsFile, "utf-8"));

fs.readdirSync(blogDir)
  .filter((f) => f.endsWith(".md") || f.endsWith(".mdx"))
  .forEach((f) => fs.unlinkSync(path.join(blogDir, f)));

posts.forEach((post) => {
  const termArrays = post._embedded?.["wp:term"] ?? [];
  const tags = termArrays.slice(1).flat().map((t) => t.name);
  const image = extractImage(post);

  const slug = post.slug;
  const title = post.title.rendered.replace(/"/g, '\\"');
  const description = post.excerpt.rendered
    .replace(/<[^>]+>/g, "")
    .trim()
    .slice(0, 200)
    .replace(/"/g, '\\"');
  const date = post.date.split("T")[0];
  const body = post.content.rendered
    .replace(WP_UPLOADS_RE, MEDIA_BASE)
    .replace(/<[^>]+>/g, "")
    .trim();

  const fields = [
    `title: "${title}"`,
    `date: ${date}`,
    `tags: [${tags.map((t) => JSON.stringify(t)).join(", ")}]`,
    `description: "${description}"`,
    image && `image: "${image}"`,
  ].filter(Boolean).join("\n");

  const imageMarkdown = image ? `![${title}](${image})\n\n` : "";
  const md = `---\n${fields}\n---\n\n<!-- truncate -->\n\n${imageMarkdown}${body}\n`;

  fs.writeFileSync(path.join(blogDir, `${date}-${slug}.md`), md);
});

console.log(`Generated ${posts.length} blog files in ${blogDir}`);
