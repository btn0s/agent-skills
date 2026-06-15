---
name: walkthrough
description: >
  Generate self-contained black-and-white typographic scrolling walkthrough HTML
  files with pure-CSS section-owned sticky visuals: each section has left-side
  narrative copy and a right-side Mermaid diagram, image, or typographic callout
  that pins and releases with `position: sticky`. Use when Codex needs to create
  an interactive explainer, codebase walkthrough, architecture narrative, process
  story, product flow, onboarding page, or scrollytelling document, especially
  when the user asks for "walkthrough", "walk me through", "explain this flow",
  "show how this works", "sticky visual panel", "Mermaid diagrams",
  "scroll-driven explainer", or explicitly invokes "$walkthrough".
---

# Walkthrough

## Overview

Create a self-contained HTML walkthrough that reads like a spare editorial essay: black text, white or black canvas, strong type hierarchy, and repeated split-screen sections where the left narrative scrolls while the section's right-side visual pins and releases with pure CSS.

Always produce an HTML artifact when this skill is triggered. Prefer a working single file over a textual explanation of what could be built.

## Workflow

### 1. Understand the story

Identify the walkthrough subject:

- A codebase feature, architecture, lifecycle, or data flow
- A product or user journey
- A process, policy, technical concept, or onboarding guide
- A visual essay assembled from provided text, Mermaid diagrams, or images

If the request is code-related, inspect real files before generating the page. Use fast search first, then read the relevant source. If available and the topic is broad, split exploration across parallel agents and synthesize their results into the final story.

If the user invokes `$walkthrough` with no topic, create a project overview walkthrough from the current workspace.

### 2. Shape the sections

Plan 5-9 scroll sections. Each section should have:

- A short title
- Two to four concise paragraphs or bullets
- One visual: Mermaid diagram, image, or intentionally blank typographic callout
- A caption that explains the visual in one sentence
- Optional source file paths or links when the walkthrough explains code

Treat sections as story beats, not documentation pages. Each beat should advance the reader's mental model.

### 3. Build the visual model

Use Mermaid for systems, flow, state, lifecycle, and relationship visuals. Keep diagrams sparse: 4-10 nodes, plain labels, short edge verbs, and no decorative color classes. Use images when the user provides screenshots, product images, diagrams, or when a real visual explains the section better than a generated diagram.

For codebase walkthroughs, each diagram node should represent a concept or responsibility rather than a raw function name.

### 4. Generate the HTML

Read [references/html-patterns.md](references/html-patterns.md) before writing the file.

Write a single self-contained `walkthrough-{topic}.html` file in the project root, or in the requested destination. Use vanilla HTML/CSS/JavaScript plus Mermaid from a CDN unless the existing project clearly calls for another stack.

### 5. Verify

Open the generated HTML in a browser when possible. Check that:

- Each section-owned right visual sticks on desktop and releases when its section ends
- Mermaid diagrams render without syntax errors
- Images load, fit, and include useful alt text
- Text does not overlap or overflow at desktop and mobile widths
- The mobile layout stacks the visual above or below the active text without breaking reading flow

## Design Rules

- Use only black, white, and neutral grays. Avoid colored accents, gradients, glows, shadows, and decorative blobs.
- Let typography carry the design. Use one strong sans-serif stack and one monospace stack for code, labels, counters, and file paths.
- Use one section per story beat. Put that section's copy and visual in the same parent so `position: sticky` handles pinning and release without scroll-state JavaScript.
- Do not use `IntersectionObserver`, scroll listeners, or active-section JavaScript for the default layout. Use them only when the user explicitly needs one shared persistent visual surface with custom transitions or cross-section state.
- Keep the interface quiet: thin rules, section numbers, compact captions, and lots of controlled whitespace.
- Do not put the main layout inside cards. Use the full viewport and simple columns.
- Do not make a marketing landing page. The walkthrough itself is the first screen.

## Output Requirements

- Include a clear title, a one-paragraph premise, and 5-9 sections.
- Include section-owned sticky visuals on desktop.
- Let normal document flow replace visuals as each section scrolls past.
- Support both Mermaid diagrams and images in the same walkthrough.
- Add section counters or compact captions inside each section.
- Keep generated files portable: no build step, no framework install, no local server required unless the project requires one.
