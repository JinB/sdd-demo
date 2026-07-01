import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "About — Eugenio Next.js",
};

export default function AboutPage() {
  return (
    <main className="container">
      <article className="about-page">
        <h1>About</h1>
        <p className="about-teaser">
          Eugenio is a highly skilled software engineer known for his intelligence, creativity, and passion for innovation.
        </p>

        <section className="about-section">
          <h2>Eugenio&apos;s recent backend GitLab commits:</h2>
          <p className="about-tech">Java, Go, Liquibase, Terraform</p>
          <img
            src="https://next.4eng.online/media/2026/06/gitlab-BE-1.png"
            alt="Backend GitLab commits"
            className="about-img"
          />
        </section>

        <section className="about-section">
          <h2>Eugenio&apos;s recent frontend GitLab commits:</h2>
          <p className="about-tech">React, MobX, MUI, Axios</p>
          <img
            src="https://next.4eng.online/media/2026/06/gitlab-FE-1.png"
            alt="Frontend GitLab commits"
            className="about-img"
          />
        </section>
      </article>
    </main>
  );
}
