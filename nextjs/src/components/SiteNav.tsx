export default function SiteNav() {
  return (
    <nav className="site-nav">
      <div className="container">
        <a href="https://wp.4eng.online/wp-admin/" target="_blank" rel="noopener" className="site-nav-link">WP Admin ↗</a>
        <a href="https://wp.4eng.online/wp-admin/post-new.php" target="_blank" rel="noopener" className="site-nav-link">Add Post ↗</a>
        <span className="site-nav-sep" />
        <a href="https://astro.4eng.online" className="site-nav-link">Astro</a>
        <a href="https://docu.4eng.online" className="site-nav-link">Docusaurus</a>
        <span className="site-nav-link active">Next.js</span>
      </div>
    </nav>
  );
}
