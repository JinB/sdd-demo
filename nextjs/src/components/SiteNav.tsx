export default function SiteNav() {
  return (
    <nav className="site-nav">
      <div className="container">
        <a href="/about" className="site-nav-link">About</a>
        <a href="https://astro.4eng.online" className="site-nav-link">Astro</a>
        <a href="https://docu.4eng.online" className="site-nav-link">Doc</a>
        <a href="/" className="site-nav-link active">Next.js</a>
        <a href="https://wp.4eng.online" className="site-nav-link">WP</a>
        <span className="site-nav-sep" />
        <a href="https://wp.4eng.online/wp-admin/edit.php" target="_blank" rel="noopener" className="site-nav-link">Admin ↗</a>
        <a href="https://github.com/JinB/sdd-demo" target="_blank" rel="noopener" className="site-nav-link">GitHub ↗</a>
      </div>
    </nav>
  );
}
