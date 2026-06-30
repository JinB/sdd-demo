import { useState } from "react";

type Category = "All" | "Sport" | "Travel" | "Uncategorized";

interface Post {
  title: string;
  category: "Sport" | "Travel" | "Uncategorized";
  slug: string;
  excerpt: string;
  date?: string;
}

interface Props {
  posts: Post[];
}

export default function CategoryFilter({ posts }: Props) {
  const [active, setActive] = useState<Category>("All");

  const filtered =
    active === "All" ? posts : posts.filter((p) => p.category === active);

  return (
    <div>
      <nav className="filter-bar" aria-label="Category filter">
        {(["All", "Sport", "Travel", "Uncategorized"] as Category[]).map((cat) => (
          <button
            key={cat}
            className="filter-btn"
            onClick={() => setActive(cat)}
            aria-pressed={active === cat}
          >
            {cat}
          </button>
        ))}
      </nav>

      <div className="post-grid">
        {filtered.map((post) => (
          <div key={post.slug} className="post-card">
            <div className="post-card-meta">
              <span className={`badge badge-${post.category}`}>{post.category}</span>
              {post.date && <time className="post-date">{post.date}</time>}
            </div>
            <a href={`/blog/${post.slug}`} className="post-title">{post.title}</a>
            <p className="post-excerpt">{post.excerpt}</p>
            <a href={`/blog/${post.slug}`} className="read-more">Read more →</a>
          </div>
        ))}
      </div>
    </div>
  );
}
