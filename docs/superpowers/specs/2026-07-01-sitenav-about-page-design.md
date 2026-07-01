# SiteNav Rework + About Page — Design Spec

**Date:** 2026-07-01
**Status:** Approved

## 1. SiteNav Changes (all 3 SSG sites)

**New bar:**
```
[About] [Astro] [Doc] [Next.js] [WP] | [Admin ↗] [GitHub ↗]
```

| Link | URL | Behaviour |
|------|-----|-----------|
| About | `/about` | same tab, relative |
| Astro | `https://astro.4eng.online` | same tab |
| Doc | `https://docu.4eng.online` | same tab |
| Next.js | `https://next.4eng.online` | same tab |
| WP | `https://wp.4eng.online` | same tab (public site) |
| Admin ↗ | `https://wp.4eng.online/wp-admin/edit.php` | new tab |
| GitHub ↗ | `https://github.com/JinB/sdd-demo` | new tab |

Current site is rendered as `<span class="site-nav-link active">` (no link). "About" is always a link.

## 2. About Page (all 3 SSG sites)

Hardcoded static page at `/about`. Inherits site layout (Header + SiteNav + Footer).

### Content

**Title:** About

**Teaser:** Eugenio is a highly skilled software engineer known for his intelligence, creativity, and passion for innovation.

**Section 1**
- Heading: Eugenio's recent backend GitLab commits:
- Subtext: Java, Go, Liquibase, Terraform
- Image: `https://[site-domain]/media/2026/06/gitlab-BE-1.png`

**Section 2**
- Heading: Eugenio's recent frontend GitLab commits:
- Subtext: React, MobX, MUI, Axios
- Image: `https://[site-domain]/media/2026/06/gitlab-FE-1.png`

### Files

| Framework | File |
|-----------|------|
| Astro | `astro/src/pages/about.astro` — scoped `<style>` block |
| Next.js | `nextjs/src/app/about/page.tsx` + styles in `globals.css` |
| Docusaurus | `docusaurus/src/pages/about.js` — uses `@theme/Layout`, styles in `custom.css` |
