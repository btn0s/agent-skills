# Typographic Walkthrough HTML Pattern

Use this reference when generating a black-and-white split-panel scrolling walkthrough.

The default layout is pure CSS. Each story beat owns its visual. `position: sticky`
pins that section's visual and releases it when the section ends. Do not use
`IntersectionObserver` or scroll listeners for this default pattern.

## Page Structure

Create one self-contained HTML file:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Walkthrough: Topic</title>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
  <style>/* inline CSS */</style>
</head>
<body>
  <header class="intro">
    <div class="kicker">Walkthrough</div>
    <h1>Topic</h1>
    <p>One-paragraph premise.</p>
  </header>

  <main>
    <section class="scene">
      <article class="copy">
        <div class="kicker">01</div>
        <h2>The first idea</h2>
        <p>Concise explanation.</p>
      </article>
      <aside class="visual" aria-label="Visual for section 1">
        <div class="visual-inner">
          <pre class="mermaid">flowchart LR
  a[Input] --> b[Output]</pre>
          <p class="caption">Caption.</p>
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

- `.copy`: section number, title, body text, optional source paths.
- `.visual`: the right-side column.
- `.visual-inner`: the sticky element. Put Mermaid, image, or callout content here.
- `.caption`: one sentence explaining the visual.

Use static HTML markup by default. A data model is acceptable for convenience, but
do not introduce scroll-state JavaScript. The scroll behavior should come from
the document structure and CSS sticky containment.

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
  max-width: 11ch;
  font-size: clamp(3rem, 8vw, 8rem);
  line-height: .9;
  font-weight: 760;
}

.intro p {
  max-width: 42rem;
  margin: 24px 0 0;
  color: var(--muted);
  font-size: 1.05rem;
  line-height: 1.6;
}

.scene {
  min-height: 115vh;
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
  min-height: 115vh;
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
  font-size: clamp(2rem, 4vw, 4.5rem);
  line-height: .98;
  letter-spacing: 0;
}

.copy p {
  max-width: 36rem;
  margin: 0 0 14px;
  color: #222222;
  font-size: 1rem;
  line-height: 1.65;
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
  font-size: clamp(4rem, 10vw, 9rem);
  line-height: .88;
  font-weight: 760;
}

.caption {
  margin: 0;
  line-height: 1.5;
}

.sources {
  max-width: 38rem;
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
  line-height: 1.4;
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
.copy p { color: #dddddd; }
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
  source[Source] --> system[System]
  system --> evidence[Evidence]</pre>
```

Image:

```html
<div class="image-frame">
  <img src="./screenshot.png" alt="Checkout review screen" />
</div>
```

Typographic callout:

```html
<div class="typographic-callout">one path, one proof</div>
```

## Diagram Guidance

- Prefer `flowchart TD` for lifecycles and responsibility maps.
- Prefer `flowchart LR` for pipelines.
- Prefer `sequenceDiagram` for back-and-forth protocols.
- Prefer `erDiagram` only when relationships between entities are the point.
- Keep labels human-readable: "User Intent", not `createCheckoutIntent()`.
- Use plain edge verbs: "creates", "validates", "hands off", "stores".
- Avoid Mermaid styling unless it is monochrome and clarifies grouping.

## Image Guidance

- Use images when visual state matters more than structure.
- Use `object-fit: contain`, max dimensions, and grayscale filtering.
- Always provide alt text.
- Prefer local relative paths for user-provided images copied into the project.
  Use remote URLs only when stable and already provided by the user.

## When JavaScript Scroll State Is Acceptable

Use `IntersectionObserver` only when the user explicitly asks for one persistent
visual stage that changes content in place, custom transitions between visuals,
progress bars tied to scroll thresholds, or other cross-section state. Otherwise,
keep the walkthrough pure CSS with section-owned sticky visuals.

## Verification Checklist

- Scroll through the whole file and confirm each section's visual pins and then
  releases when the section ends.
- Confirm the next section's visual replaces the previous one through normal
  document flow.
- Confirm mobile stacks copy and visual without overlap.
- Confirm all Mermaid diagrams render.
- Confirm images load and remain inspectable.
- Confirm there is no horizontal overflow.
- Confirm the page still works if opened directly from disk.
