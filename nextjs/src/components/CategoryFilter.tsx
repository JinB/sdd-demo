"use client";
import { useState } from "react";
import type { Post } from "@/lib/posts";

const BADGE_CLASS: Record<string, string> = {
  Sport: "badge-Sport",
  Travel: "badge-Travel",
};

export default function CategoryFilter({ posts }: { posts: Post[] }) {
  const [active, setActive] = useState("All");

  const categories = [
    "All",
    ...Array.from(new Set(posts.map((p) => p.category))).sort(),
  ];

  const filtered =
    active === "All" ? posts : posts.filter((p) => p.category === active);

  return (
    <div>
      <nav className="filter-bar" aria-label="Category filter">
        {categories.map((cat) => (
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
            {post.image && (
              <a href={`/blog/${post.slug}/`}>
                <img
                  src={post.image}
                  alt={post.title}
                  className="post-card-img"
                  loading="lazy"
                />
              </a>
            )}
            <div className="post-card-body">
              <div className="post-card-meta">
                <span className={`badge ${BADGE_CLASS[post.category] ?? "badge-Uncategorized"}`}>
                  {post.category}
                </span>
                <time className="post-date">{post.date}</time>
              </div>
              <a href={`/blog/${post.slug}/`} className="post-title">
                {post.title}
              </a>
              <p className="post-excerpt">{post.excerpt}</p>
              <a href={`/blog/${post.slug}/`} className="read-more">
                Read more →
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
