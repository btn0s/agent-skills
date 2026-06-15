---
name: walkthrough
description: >
  Generate self-contained black-and-white guided reference HTML files for
  codebases, systems, workflows, products, and technical topics. The output is a
  detailed educational document with straightforward section titles,
  subsections, source references, command lists, tables, and pure-CSS
  section-owned sticky visuals. Use when Codex needs to create an onboarding
  guide, codebase walkthrough, architecture reference, process guide, subsystem
  map, or any artifact requested with "walkthrough", "walk me through",
  "guided reference", "explain this repo", "explain this flow", "show how this
  works", "Mermaid diagrams", or "$walkthrough".
---

# Walkthrough

## Overview

Create a self-contained HTML guided reference, not a marketing page and not a
thin visual essay. The document should help a reader who does not already know
the topic build a durable mental model: what the system is, where the important
parts live, how the pieces connect, what vocabulary matters, what commands prove
the behavior, and how to debug common questions.

Always produce an HTML artifact when this skill is triggered. Prefer one useful,
portable file over a textual description of what could be built.

## Required Output Shape

The default artifact is a `walkthrough-{topic}.html` file with:

- A clear title ending in "Guided Reference" when appropriate.
- A one-paragraph premise that explains who the guide is for and how to read it.
- A compact navigation row with numbered section links.
- 5-9 major sections with straightforward titles, such as "System Overview",
  "Runtime Reference", "Client Reference", or "Debugging Workflow".
- Multiple `<h3>` subsections inside each major section. Do not make each
  section a single broad essay.
- Reference tables for files, concepts, contracts, responsibilities, or
  evidence levels.
- Command blocks for validation, local workflows, smoke tests, or inspection
  commands when the topic has runnable commands.
- Source paths or links when the guide explains a real codebase, document set,
  or existing system.
- One section-owned visual per major section: a Mermaid diagram, an image, or a
  typographic callout.
- A caption under every visual.

## Workflow

### 1. Inspect the real subject

Identify what the user wants explained:

- A codebase, subsystem, architecture, or data flow.
- A product, user journey, operational process, or policy.
- A technical concept that needs examples, vocabulary, and proof commands.
- A collection of notes, diagrams, screenshots, or docs.

For code-related requests, inspect real files before generating the page. Use
fast search first, then read the relevant source, docs, tests, manifests, and
local instruction files. For broad codebase walkthroughs, gather enough context
to explain ownership boundaries, not just names of files.

If the user invokes `$walkthrough` with no topic, create a project overview
guided reference from the current workspace.

### 2. Choose the reader's path

Plan the guide as an onboarding path from basics to proof:

1. Start with a system overview that defines the purpose, main loop, and core
   vocabulary.
2. Move through the main facets or lanes in a stable order.
3. For each facet, explain purpose, important files, data flow, contracts,
   commands, and debugging questions.
4. End with an operational or debugging workflow that tells the reader what to
   check first and how to prove a change worked.

Use plain section names. Prefer "Game Packaging Reference" over clever titles,
"Telemetry Reference" over mood-setting phrases, and "Debugging Workflow" over
abstract slogans.

### 3. Write each section as a reference unit

Each major section should usually include 4-9 subsections chosen from this set:

- Purpose
- Main files and responsibilities
- Data flow
- Important terms
- Required contract
- Commands
- Example workflow
- Debugging questions
- Validation checklist
- Evidence levels
- Fields worth learning
- Common failure modes

Subsections should be skimmable. Use paragraphs for explanation, tables for
mapping, ordered lists for workflows, and bullets for checks or questions. Avoid
assuming the reader already understands project-specific acronyms.

### 4. Build visuals that teach structure

Use Mermaid for systems, flow, state, lifecycle, and relationship visuals. Keep
diagrams sparse: 4-10 nodes, human-readable labels, short edge verbs, and no
decorative color classes. For codebase walkthroughs, diagram nodes should
represent concepts or responsibilities rather than raw function names.

Use images when the user provides screenshots or when real visual state matters.
Use typographic callouts only when a section's key rule is more important than a
diagram.

### 5. Generate the HTML

Read [references/html-patterns.md](references/html-patterns.md) before writing
the file.

Write a single self-contained `walkthrough-{topic}.html` file in the project
root, or in the requested destination. Use vanilla HTML/CSS/JavaScript plus
Mermaid from a CDN unless the existing project clearly calls for another stack.

The page should use black, white, and neutral grays. The design should feel like
a detailed technical document with a strong visual margin, not a splash page.

### 6. Verify the artifact

Open the generated HTML in a browser when possible. Check that:

- The document has 5-9 major sections and meaningful subsections.
- The section titles are straightforward and useful as a table of contents.
- Tables, code paths, and command blocks do not overflow on mobile.
- Each section-owned visual sticks on desktop and becomes static on mobile.
- Mermaid diagrams render without syntax errors.
- Images load, fit, and include useful alt text.
- Text does not overlap or overflow at desktop and mobile widths.
- The page has no browser console errors.
- The page still works as a portable single file except for intentional CDN
  Mermaid loading.

## Design Rules

- Use only black, white, and neutral grays. Avoid colored accents, gradients,
  glows, shadows, and decorative blobs.
- Let typography, tables, rules, and spacing carry the design.
- Use one section per reference facet. Put that section's copy and visual in the
  same parent so `position: sticky` handles pinning and release without
  scroll-state JavaScript.
- Do not use `IntersectionObserver`, scroll listeners, or active-section
  JavaScript for the default layout.
- Do not make a landing page. The guide itself is the first screen.
- Do not hide the useful material behind cards. Use full-width document flow
  with a split reference/visual layout.
- Use stable mobile rules for tables and code paths so long identifiers wrap
  instead of creating horizontal overflow.

## Quality Bar

A good walkthrough from this skill should answer:

- What is this thing for?
- What are the main parts?
- Which files, commands, docs, APIs, or artifacts matter?
- What vocabulary does a new reader need?
- What facts or contracts cross subsystem boundaries?
- What does healthy behavior look like?
- What should I check first when something breaks?
- What command or evidence proves this section is working?

If the output only sounds polished but does not help someone operate or debug
the subject, keep iterating before calling it done.
