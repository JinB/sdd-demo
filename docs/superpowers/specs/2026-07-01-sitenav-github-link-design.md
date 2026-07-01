# SiteNav GitHub Link — Design Spec

**Date:** 2026-07-01
**Status:** Approved

## Overview

Add a GitHub repository link to the inter-site navigation bar on all three SSG sites, immediately after the existing WP Admin link.

## Change

**Before:**
```
[Astro]  [Docusaurus]  [Next.js]  |  [WP Admin ↗]
```

**After:**
```
[Astro]  [Docusaurus]  [Next.js]  |  [WP Admin ↗]  [GitHub ↗]
```

## Specification

- **Label:** `GitHub ↗`
- **URL:** `https://github.com/JinB/sdd-demo`
- **Behaviour:** opens in a new tab (`target="_blank" rel="noopener"`)
- **Style:** identical to WP Admin — same CSS class (`site-nav-link`), no additional separator
- **Placement:** immediately after WP Admin, inside the same post-separator group

## Files

| File | Change |
|------|--------|
| `astro/src/components/SiteNav.astro` | Append `<a>` after WP Admin line |
| `nextjs/src/components/SiteNav.tsx` | Append `<a>` after WP Admin line |
| `docusaurus/src/components/SiteNav.js` | Append `<a>` after WP Admin line |

No CSS changes required — `site-nav-link` already styles external links correctly.
No `openspec.yaml` changes required.
