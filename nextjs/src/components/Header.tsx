import Link from "next/link";
import LiveClock from "./LiveClock";
import ThemeToggle from "./ThemeToggle";

export default function Header() {
  return (
    <header className="site-header">
      <div className="container">
        <Link href="/" className="site-title">
          Eugenio Next.js
        </Link>
        <div className="header-controls">
          <LiveClock />
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
