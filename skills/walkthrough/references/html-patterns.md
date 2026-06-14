# Typographic Walkthrough HTML Pattern

Use this reference when generating a black-and-white split-panel scrolling walkthrough.

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
  <main class="shell">
    <section class="copy-rail" aria-label="Walkthrough sections"></section>
    <aside class="visual-rail" aria-label="Active visual">
      <div class="visual-stage">
        <div class="visual-meta"></div>
        <div id="visual"></div>
        <p id="caption"></p>
      </div>
    </aside>
  </main>
  <script>/* inline JS */</script>
</body>
</html>
```

## Data Model

Represent the walkthrough as data, then render the page from it:

```js
const WALKTHROUGH = {
  title: "How Checkout Works",
  premise: "A concise overview of the path from cart intent to durable order.",
  sections: [
    {
      id: "intent",
      kicker: "01",
      title: "The user creates intent",
      body: [
        "The cart page turns selected items into a checkout intent.",
        "At this point the system is still reversible: prices can change, inventory can fail, and payment has not started."
      ],
      visual: {
        type: "mermaid",
        caption: "The first handoff is from mutable cart state into a checkout session.",
        source: `flowchart TD
          cart[Cart] --> intent[Checkout Intent]
          intent --> session[Payment Session]`
      }
    },
    {
      id: "review",
      kicker: "02",
      title: "Review locks the shape",
      body: ["The review step validates totals, shipping, tax, and available inventory."],
      visual: {
        type: "image",
        caption: "A product screenshot can replace a diagram when interface state matters.",
        src: "./checkout-review.png",
        alt: "Checkout review screen"
      }
    }
  ]
};
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

.shell {
  display: grid;
  grid-template-columns: minmax(320px, 42vw) minmax(420px, 1fr);
  min-height: 100vh;
}

.copy-rail {
  border-right: 1px solid var(--line);
  padding: clamp(28px, 5vw, 72px);
}

.visual-rail {
  min-height: 100vh;
  padding: clamp(20px, 4vw, 56px);
}

.visual-stage {
  position: sticky;
  top: clamp(16px, 4vh, 40px);
  min-height: calc(100vh - 80px);
  display: grid;
  grid-template-rows: auto 1fr auto;
  gap: 20px;
  align-items: center;
}

.intro {
  min-height: 70vh;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding-bottom: 20vh;
}

.intro h1 {
  margin: 0;
  max-width: 11ch;
  font-size: clamp(3rem, 8vw, 8rem);
  line-height: .9;
  font-weight: 760;
}

.intro p {
  max-width: 38rem;
  margin: 24px 0 0;
  color: var(--muted);
  font-size: 1.05rem;
  line-height: 1.6;
}

.step {
  min-height: 85vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 12vh 0;
  border-top: 1px solid var(--line);
  opacity: .38;
  transition: opacity .2s ease;
}

.step.is-active { opacity: 1; }
.kicker, .visual-meta {
  font-family: var(--mono);
  font-size: .78rem;
  text-transform: uppercase;
  letter-spacing: .08em;
  color: var(--muted);
}

.step h2 {
  margin: 12px 0 18px;
  font-size: clamp(2rem, 4vw, 4.5rem);
  line-height: .98;
  letter-spacing: 0;
}

.step p {
  max-width: 36rem;
  margin: 0 0 14px;
  color: #222222;
  font-size: 1rem;
  line-height: 1.65;
}

#visual {
  width: 100%;
  min-height: 440px;
  display: grid;
  place-items: center;
  border-block: 1px solid var(--line);
  padding: clamp(18px, 4vw, 48px) 0;
}

#visual svg {
  max-width: 100%;
  height: auto;
}

#visual img {
  max-width: 100%;
  max-height: 68vh;
  object-fit: contain;
  filter: grayscale(1);
}

#caption {
  margin: 0;
  color: var(--muted);
  font-size: .9rem;
  line-height: 1.5;
}

@media (max-width: 860px) {
  .shell { display: block; }
  .copy-rail {
    border-right: 0;
    padding: 24px;
  }
  .visual-rail {
    position: sticky;
    top: 0;
    z-index: 5;
    min-height: auto;
    padding: 14px 24px;
    background: rgba(255,255,255,.96);
    border-bottom: 1px solid var(--line);
  }
  .visual-stage {
    position: static;
    min-height: auto;
    gap: 10px;
  }
  #visual {
    min-height: 220px;
    max-height: 38vh;
    overflow: hidden;
    padding: 12px 0;
  }
  .intro { min-height: 62vh; padding-bottom: 12vh; }
  .step { min-height: 76vh; }
}
```

For a dark variant, invert the variables only. Keep the same monochrome restraint:

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
.step p { color: #dddddd; }
```

## Mermaid Setup

Initialize Mermaid in monochrome. Avoid colored class definitions.

```js
mermaid.initialize({
  startOnLoad: false,
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

For dark pages, switch Mermaid variables to black background, white text, white lines, and dark neutral cluster fills.

## Rendering and Scroll State

Use `IntersectionObserver` to choose the active section. Render the active visual into the sticky panel.

```js
const copyRail = document.querySelector(".copy-rail");
const visualEl = document.querySelector("#visual");
const captionEl = document.querySelector("#caption");
const metaEl = document.querySelector(".visual-meta");

function renderSections() {
  copyRail.innerHTML = `
    <header class="intro">
      <div class="kicker">Walkthrough</div>
      <h1>${escapeHtml(WALKTHROUGH.title)}</h1>
      <p>${escapeHtml(WALKTHROUGH.premise)}</p>
    </header>
    ${WALKTHROUGH.sections.map((section, index) => `
      <section class="step" data-step="${section.id}">
        <div class="kicker">${section.kicker || String(index + 1).padStart(2, "0")}</div>
        <h2>${escapeHtml(section.title)}</h2>
        ${section.body.map(text => `<p>${escapeHtml(text)}</p>`).join("")}
      </section>
    `).join("")}
  `;
}

async function setActive(sectionId) {
  const section = WALKTHROUGH.sections.find(item => item.id === sectionId) || WALKTHROUGH.sections[0];
  document.querySelectorAll(".step").forEach(el => {
    el.classList.toggle("is-active", el.dataset.step === section.id);
  });

  metaEl.textContent = `${section.kicker || ""} / ${section.title}`;
  captionEl.textContent = section.visual.caption || "";

  if (section.visual.type === "image") {
    visualEl.innerHTML = `<img src="${escapeAttr(section.visual.src)}" alt="${escapeAttr(section.visual.alt || section.title)}" />`;
    return;
  }

  if (section.visual.type === "blank") {
    visualEl.innerHTML = `<div class="typographic-callout">${escapeHtml(section.visual.text || section.title)}</div>`;
    return;
  }

  const renderId = `diagram-${section.id}-${Date.now()}`;
  try {
    const { svg } = await mermaid.render(renderId, section.visual.source);
    visualEl.innerHTML = svg;
  } catch (error) {
    visualEl.innerHTML = `<pre class="diagram-error">${escapeHtml(String(error))}</pre>`;
  }
}

function observeSections() {
  const observer = new IntersectionObserver((entries) => {
    const visible = entries
      .filter(entry => entry.isIntersecting)
      .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
    if (visible) setActive(visible.target.dataset.step);
  }, {
    root: null,
    threshold: [0.25, 0.45, 0.65],
    rootMargin: "-18% 0px -35% 0px"
  });

  document.querySelectorAll(".step").forEach(step => observer.observe(step));
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(value) {
  return escapeHtml(value).replaceAll("`", "&#096;");
}

renderSections();
setActive(WALKTHROUGH.sections[0].id);
observeSections();
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
- Prefer local relative paths for user-provided images copied into the project. Use remote URLs only when stable and already provided by the user.

## Verification Checklist

- Scroll through the whole file and confirm every section activates the correct visual.
- Confirm the sticky right panel stays fixed on desktop.
- Confirm mobile does not overlap text and visuals.
- Confirm all Mermaid diagrams render.
- Confirm images load and remain inspectable.
- Confirm the page still works if opened directly from disk.
