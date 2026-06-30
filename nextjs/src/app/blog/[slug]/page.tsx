import { getPosts, getPost } from "@/lib/posts";
import { notFound } from "next/navigation";

export function generateStaticParams() {
  return getPosts().map((p) => ({ slug: p.slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const post = getPost(slug);
  return {
    title: post ? `${post.title} — Eugenio Next.js` : "Not Found",
    description: post?.excerpt,
    openGraph: post?.image ? { images: [post.image] } : undefined,
  };
}

export default async function PostPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const post = getPost(slug);
  if (!post) notFound();

  return (
    <main className="container">
      <a href="/" className="article-back">
        ← All posts
      </a>
      <article className="post">
        {post.image && (
          <img src={post.image} alt={post.title} className="post-hero" />
        )}
        <h1>{post.title}</h1>
        <div className="post-card-meta">
          <span className={`badge badge-${post.category}`}>{post.category}</span>
          <time className="post-date">{post.date}</time>
        </div>
        {post.body
          .split("\n\n")
          .filter((p) => p.trim())
          .map((para, i) => (
            <p key={i}>{para}</p>
          ))}
      </article>
    </main>
  );
}
