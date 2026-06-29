import { useState } from "react";

type Category = "All" | "Sport" | "Software";

interface Post {
  title: string;
  category: "Sport" | "Software";
  slug: string;
  excerpt: string;
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
      <nav aria-label="Category filter">
        {(["All", "Sport", "Software"] as Category[]).map((cat) => (
          <button
            key={cat}
            onClick={() => setActive(cat)}
            aria-pressed={active === cat}
          >
            {cat}
          </button>
        ))}
      </nav>
      <ul>
        {filtered.map((post) => (
          <li key={post.slug}>
            <a href={`/blog/${post.slug}`}>{post.title}</a>
            <p>{post.excerpt}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
