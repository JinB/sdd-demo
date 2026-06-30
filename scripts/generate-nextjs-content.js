const fs = require("fs");
const path = require("path");

const postsFile = path.join(process.cwd(), "posts.json");
const outputFile = path.join(process.cwd(), "nextjs", "src", "data", "posts.json");

const WP_UPLOADS_RE = /https?:\/\/[^/]+\/wp-content\/uploads\//g;
const MEDIA_BASE = "https://next.4eng.online/media/";

function extractImage(post) {
  const featured = post._embedded?.["wp:featuredmedia"]?.[0]?.source_url;
  if (featured) return featured.replace(WP_UPLOADS_RE, MEDIA_BASE);
  const match = post.content.rendered.match(/<img[^>]+src="([^"]+)"/i);
  if (match) return match[1].replace(WP_UPLOADS_RE, MEDIA_BASE);
  return undefined;
}

const raw = JSON.parse(fs.readFileSync(postsFile, "utf-8"));

const posts = raw
  .map((post) => {
    const termArrays = post._embedded?.["wp:term"] ?? [];
    const wpCategories = termArrays[0] ?? [];
    const wpTags = termArrays.slice(1).flat();

    const category = wpCategories[0]?.name ?? "Uncategorized";
    const tags = wpTags.map((t) => t.name);
    const image = extractImage(post);

    const body = post.content.rendered
      .replace(WP_UPLOADS_RE, MEDIA_BASE)
      .replace(/<[^>]+>/g, "")
      .trim();

    const excerpt = post.excerpt.rendered
      .replace(/<[^>]+>/g, "")
      .trim()
      .slice(0, 200);

    return {
      slug: post.slug,
      title: post.title.rendered,
      category,
      tags,
      date: post.date.split("T")[0],
      excerpt,
      ...(image && { image }),
      body,
    };
  })
  .sort((a, b) => b.date.localeCompare(a.date));

fs.writeFileSync(outputFile, JSON.stringify(posts, null, 2));
console.log(`Generated ${posts.length} posts in ${outputFile}`);
