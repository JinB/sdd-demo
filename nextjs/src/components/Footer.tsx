export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="container">
        <p className="about">
          <strong>About Next.js</strong>
          Next.js is the most widely used React framework, supporting SSG, SSR, ISR, and full-stack
          API routes in a single toolchain. Pros: massive ecosystem, flexible rendering strategies,
          built-in image and font optimization, seamless Vercel deployment.
          Cons: App Router adds significant complexity, some advanced features are Vercel-dependent,
          larger bundle than purpose-built SSG tools, overkill for purely static content sites.
        </p>
      </div>
    </footer>
  );
}
