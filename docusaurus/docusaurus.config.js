// @ts-check
const { themes: prismThemes } = require("prism-react-renderer");

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: "Eugenio Docusaurus",
  tagline: "Sport, Travel & More",
  url: "https://docu.4eng.online",
  baseUrl: "/",
  onBrokenLinks: "warn",
  markdown: {
    hooks: {
      onBrokenMarkdownLinks: "warn",
    },
  },
  i18n: {
    defaultLocale: "en",
    locales: ["en"],
  },
  presets: [
    [
      "classic",
      {
        docs: false,
        blog: {
          routeBasePath: "/",
          showReadingTime: false,
          blogSidebarCount: "ALL",
          blogSidebarTitle: "All posts",
        },
        theme: {
          customCss: require.resolve("./src/css/custom.css"),
        },
      },
    ],
  ],
  themeConfig: {
    navbar: {
      title: "Eugenio Docusaurus",
      items: [
        {
          type: "custom-LiveClock",
          position: "right",
        },
      ],
    },
    footer: {
      style: "dark",
      copyright:
        "<strong>About Docusaurus</strong> — " +
        "Docusaurus is an open-source SSG from Meta, purpose-built for documentation and blogs. " +
        "It handles versioning, MDX, search, and i18n out of the box. " +
        "Pros: opinionated defaults that work immediately, strong community, free Algolia DocSearch. " +
        "Cons: tightly scoped to docs/blog formats, hard to deviate from its structure, " +
        "can feel heavy for simple content needs.",
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  },
};

module.exports = config;
