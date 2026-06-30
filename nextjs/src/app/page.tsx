import { getPosts } from "@/lib/posts";
import CategoryFilter from "@/components/CategoryFilter";

export default function HomePage() {
  const posts = getPosts();
  return (
    <main className="container">
      <div className="page-header">
        <h2>Latest posts</h2>
        <p>
          {posts.length} article{posts.length !== 1 ? "s" : ""}
        </p>
      </div>
      <CategoryFilter posts={posts} />
    </main>
  );
}
