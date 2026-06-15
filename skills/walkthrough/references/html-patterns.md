# Guided Reference HTML Pattern

Use this reference when generating a black-and-white guided reference with a
split document/visual layout.

The default layout is pure CSS. Each major reference section owns its visual.
`position: sticky` pins that section's visual and releases it when the section
ends. Do not use `IntersectionObserver` or scroll listeners for this pattern.

## Page Structure

Create one self-contained HTML file:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Topic Guided Reference</title>
  <link rel="icon" href="data:," />
  <script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
  <style>/* inline CSS */</style>
</head>
<body>
  <header class="intro">
    <div class="kicker">Guided Reference</div>
    <h1>Topic Guided Reference</h1>
    <p>
      One paragraph explaining what the reader will understand, where the guide
      starts, and how to use the section titles as a debugging map.
    </p>
    <nav class="nav" aria-label="Guide sections">
      <a href="#overview">00 System Overview</a>
      <a href="#runtime">01 Runtime Reference</a>
      <a href="#proof">02 Debugging Workflow</a>
    </nav>
  </header>

  <main>
    <section class="scene" id="overview">
      <article class="copy">
        <div class="kicker">00 / system overview</div>
        <h2>System Overview</h2>

        <h3>Purpose</h3>
        <p>Explain the subsystem in plain language.</p>

        <h3>Main files and responsibilities</h3>
        <table class="reference-table">
          <tr><th>Core</th><td><code>src/core.ts</code> owns the shared model.</td></tr>
          <tr><th>Tests</th><td><code>tests/core.test.ts</code> proves the contract.</td></tr>
        </table>

        <h3>Commands</h3>
        <div class="command-list">
          <code>npm test -- core</code>
          <code>npm run lint</code>
        </div>

        <h3>Debugging questions</h3>
        <ul>
          <li>What input created the bad state?</li>
          <li>Which boundary should have rejected it?</li>
        </ul>
      </article>

      <aside class="visual" aria-label="System overview diagram">
        <div class="visual-inner">
          <pre class="mermaid">flowchart LR
  input["Input"] --> core["Core Contract"]
  core --> proof["Proof Command"]</pre>
          <p class="caption">Each section pairs reference material with one structural visual.</p>
        </div>
      </aside>
    </section>
  </main>

  <script>
    mermaid.initialize({ startOnLoad: true });
  </script>
</body>
</html>
```

## Section Model

Plan 5-9 `.scene` sections. Each section contains:

- `.copy`: section number, straightforward title, subsections, body text,
  tables, command lists, and optional source paths.
- `.visual`: the right-side visual column.
- `.visual-inner`: the sticky element. Put Mermaid, image, or callout content
  here.
- `.caption`: one sentence explaining the visual.

Every major section should include real subsections with `<h3>` headings. A
section with only a title and two paragraphs is too thin for this skill.

Good section titles:

- System Overview
- Repository Scope and Ownership
- Packaging Reference
- Runtime Reference
- Protocol and Client Reference
- Telemetry Reference
- Infrastructure and Serving Reference
- Debugging and Proof Workflow

Avoid clever, atmospheric, or marketing-style titles.

## Reference Components

Use tables for mappings:

```html
<table class="reference-table">
  <tr><th>Manifest</th><td>Declares install, launch, capture, and validation facts.</td></tr>
  <tr><th>Runtime</th><td>Turns manifest facts into a running process and health state.</td></tr>
</table>
```

Use command lists for runnable proof:

```html
<div class="command-list">
  <code>just test</code>
  <code>cargo test -p example-crate</code>
</div>
```

Use source lists for local evidence:

```html
<ul class="sources">
  <li>src/runtime/session.rs</li>
  <li>docs/runtime/health.md</li>
</ul>
```

Use ordered lists for workflows:

```html
<ol class="read-path">
  <li>Find the owner file.</li>
  <li>Check the contract fields.</li>
  <li>Run the narrow proof command.</li>
</ol>
```

## Monochrome CSS

Use neutral variables and stable layout dimensions:

```css
:root {
  color-scheme: light;
  --bg: #ffffff;
  --fg: #050505;
  --muted: #666666;
  --line: #d8d8d8;
  --soft: #f5f5f5;
  --ink: #000000;
  --mono: "SFMono-Regular", "SF Mono", Consolas, "Liberation Mono", monospace;
  --sans: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--fg);
  font-family: var(--sans);
  letter-spacing: 0;
}

a { color: inherit; text-decoration-thickness: 1px; text-underline-offset: 3px; }
code {
  font-family: var(--mono);
  font-size: .9em;
  background: var(--soft);
  padding: .1em .32em;
  border: 1px solid var(--line);
  overflow-wrap: anywhere;
}

.intro {
  min-height: 78vh;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: clamp(28px, 5vw, 72px);
  border-bottom: 1px solid var(--line);
}

.intro h1 {
  margin: 0;
  max-width: 12ch;
  font-size: clamp(3rem, 8vw, 8rem);
  line-height: .9;
  font-weight: 760;
  letter-spacing: 0;
}

.intro p {
  max-width: 49rem;
  margin: 24px 0 0;
  color: var(--muted);
  font-size: 1.05rem;
  line-height: 1.6;
}

.nav {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  max-width: 62rem;
  margin-top: 28px;
  padding-top: 18px;
  border-top: 1px solid var(--line);
  font-family: var(--mono);
  font-size: .78rem;
  text-transform: uppercase;
  letter-spacing: .08em;
}

.scene {
  min-height: 118vh;
  display: grid;
  grid-template-columns: minmax(320px, 42vw) minmax(420px, 1fr);
  border-bottom: 1px solid var(--line);
}

.copy {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: clamp(28px, 5vw, 72px);
}

.visual {
  min-height: 118vh;
  border-left: 1px solid var(--line);
  padding: clamp(20px, 4vw, 56px);
}

.visual-inner {
  position: sticky;
  top: clamp(16px, 4vh, 40px);
  min-height: calc(100vh - 80px);
  display: grid;
  grid-template-rows: 1fr auto;
  gap: 20px;
  align-items: center;
}

.kicker,
.caption,
.sources-title {
  font-family: var(--mono);
  font-size: .78rem;
  text-transform: uppercase;
  letter-spacing: .08em;
  color: var(--muted);
}

.copy h2 {
  margin: 12px 0 18px;
  font-size: clamp(1.9rem, 3.4vw, 3.8rem);
  line-height: 1.02;
  letter-spacing: 0;
}

.copy h3 {
  max-width: 39rem;
  margin: 24px 0 8px;
  padding-top: 14px;
  border-top: 1px solid var(--line);
  font-size: 1rem;
  line-height: 1.25;
  letter-spacing: 0;
  font-weight: 720;
}

.copy p {
  max-width: 39rem;
  margin: 0 0 14px;
  color: #222222;
  font-size: 1rem;
  line-height: 1.65;
}

.copy ul,
.copy ol {
  max-width: 39rem;
  margin: 2px 0 18px;
  padding-left: 1.1rem;
  color: #222222;
  line-height: 1.6;
}

.copy li { margin-bottom: 8px; }

.reference-table {
  max-width: 39rem;
  width: 100%;
  margin: 16px 0 18px;
  border-collapse: collapse;
  font-size: .9rem;
  line-height: 1.45;
}

.reference-table th,
.reference-table td {
  vertical-align: top;
  text-align: left;
  padding: 10px 8px;
  border-top: 1px solid var(--line);
}

.reference-table th {
  width: 31%;
  font-family: var(--mono);
  font-size: .74rem;
  text-transform: uppercase;
  letter-spacing: .08em;
  color: var(--muted);
  font-weight: 500;
}

.reference-table tr:last-child th,
.reference-table tr:last-child td {
  border-bottom: 1px solid var(--line);
}

.command-list {
  max-width: 39rem;
  display: grid;
  gap: 8px;
  margin: 12px 0 18px;
}

.command-list code {
  display: block;
  width: 100%;
  padding: 8px 10px;
  overflow-wrap: anywhere;
}

.mermaid,
.image-frame,
.typographic-callout {
  width: 100%;
  min-height: 440px;
  display: grid;
  place-items: center;
  border-block: 1px solid var(--line);
  padding: clamp(18px, 4vw, 48px) 0;
}

.mermaid svg {
  max-width: 100%;
  height: auto;
}

.image-frame img {
  max-width: 100%;
  max-height: 68vh;
  object-fit: contain;
  filter: grayscale(1);
}

.typographic-callout {
  justify-items: start;
  align-content: center;
  font-size: clamp(3.8rem, 9vw, 8.2rem);
  line-height: .9;
  font-weight: 760;
  letter-spacing: 0;
  text-transform: lowercase;
}

.caption {
  margin: 0;
  line-height: 1.5;
}

.sources {
  max-width: 40rem;
  margin: 24px 0 0;
  padding: 0;
  list-style: none;
  border-top: 1px solid var(--line);
}

.sources li {
  padding-top: 10px;
  color: var(--muted);
  font-family: var(--mono);
  font-size: .78rem;
  line-height: 1.45;
  word-break: break-word;
}

@media (max-width: 860px) {
  .intro { min-height: 70vh; padding: 24px; }
  .scene {
    display: flex;
    flex-direction: column;
    min-height: auto;
  }
  .copy {
    min-height: auto;
    padding: 56px 24px 28px;
  }
  .visual {
    min-height: auto;
    border-left: 0;
    padding: 0 24px 56px;
  }
  .visual-inner {
    position: static;
    min-height: auto;
  }
  .mermaid,
  .image-frame,
  .typographic-callout {
    min-height: 260px;
  }
  .reference-table,
  .reference-table tbody,
  .reference-table tr,
  .reference-table th,
  .reference-table td {
    display: block;
    width: 100%;
  }
  .reference-table th {
    padding-bottom: 2px;
  }
  .reference-table td {
    padding-top: 0;
  }
}
```

For a dark variant, invert the variables only:

```css
:root {
  color-scheme: dark;
  --bg: #000000;
  --fg: #ffffff;
  --muted: #a3a3a3;
  --line: #2a2a2a;
  --soft: #111111;
  --ink: #ffffff;
}
.copy p,
.copy ul,
.copy ol { color: #dddddd; }
```

## Mermaid Setup

Initialize Mermaid in monochrome. Avoid colored class definitions.

```js
mermaid.initialize({
  startOnLoad: true,
  securityLevel: "loose",
  theme: "base",
  themeVariables: {
    background: "#ffffff",
    primaryColor: "#ffffff",
    primaryTextColor: "#000000",
    primaryBorderColor: "#000000",
    lineColor: "#000000",
    secondaryColor: "#f5f5f5",
    tertiaryColor: "#ffffff",
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif",
    edgeLabelBackground: "#ffffff",
    clusterBkg: "#ffffff",
    clusterBorder: "#d8d8d8"
  },
  flowchart: { useMaxWidth: true, htmlLabels: true, curve: "linear" },
  sequence: { mirrorActors: false },
  er: { useMaxWidth: true }
});
```

For dark pages, switch Mermaid variables to black background, white text, white
lines, and dark neutral cluster fills.

## Visual Patterns

Mermaid:

```html
<pre class="mermaid">flowchart LR
  source["Source Facts"] --> runtime["Runtime Contract"]
  runtime --> evidence["Evidence"]</pre>
```

Image:

```html
<div class="image-frame">
  <img src="./screenshot.png" alt="Telemetry session detail screen" />
</div>
```

Typographic callout:

```html
<div class="typographic-callout">
  one path
  <span class="callout-small">Manifest facts. Runtime facts. Evidence proves promotion.</span>
</div>
```

## Diagram Guidance

- Prefer `flowchart TD` for lifecycles and responsibility maps.
- Prefer `flowchart LR` for pipelines.
- Prefer `sequenceDiagram` for back-and-forth protocols.
- Prefer `erDiagram` only when relationships between entities are the point.
- Keep labels human-readable: "Session Health", not `SessionHealthSnapshot`.
- Use plain edge verbs: "creates", "validates", "hands off", "stores".
- Avoid Mermaid styling unless it is monochrome and clarifies grouping.

## Writing Guidance

- Define project-specific vocabulary before using it heavily.
- Put the most useful nouns in headings: "Main files and responsibilities",
  "Required contract", "Commands", "Debugging questions".
- Use file paths as evidence, not decoration.
- Explain why a command is the first proof command when that matters.
- Keep paragraphs short enough to scan. Dense sections should use tables or
  lists.
- End with a workflow section that helps the reader debug or validate the topic.

## When JavaScript Scroll State Is Acceptable

Use `IntersectionObserver` only when the user explicitly asks for one persistent
visual stage that changes content in place, custom transitions between visuals,
progress bars tied to scroll thresholds, or other cross-section state. Otherwise,
keep the walkthrough pure CSS with section-owned sticky visuals.

## Verification Checklist

- Confirm the document has 5-9 major sections.
- Confirm each major section has meaningful `<h3>` subsections.
- Confirm the section titles are straightforward enough to work as a table of
  contents.
- Confirm each section's visual pins on desktop and releases when the section
  ends.
- Confirm mobile stacks copy and visual without overlap.
- Confirm tables and long code paths do not create horizontal overflow.
- Confirm all Mermaid diagrams render.
- Confirm images load and remain inspectable.
- Confirm there are no browser console errors.
- Confirm the page still works as a portable single file except for intentional
  Mermaid CDN loading.
