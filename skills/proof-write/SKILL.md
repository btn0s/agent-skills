---
name: proof-write
description: >-
  Write the script for a narrated PR walkthrough: the story arc, the spoken agenda, chapters, and the say: lines
  for each beat. Use when turning a change (a perf win, a bug fix, a new flow) into a proof.yaml that people can
  follow without effort, or when a draft walkthrough feels dense. Start here for any walkthrough; recordings and
  data come from proof-capture, and the render from proof-present.
---

# Writing a walkthrough script

A walkthrough is there to lower cognitive load. The viewer should never have to hold something in their head that isn't on screen, or decode a term nobody explained. This skill covers the words and the order. proof-capture gathers the recordings and data each beat points at, and proof-present renders the result (its "Walkthroughs" section has the beat syntax).

## The arc

1. **Intro.** Start with the result as a plain sentence ("Launches are ready in 19 seconds, down from 43"), then speak the agenda the way a person would: "First, we'll look at what we measured and where the numbers come from. Then, what was slowing things down. Then, the fix. And last, what's still left." Use an agenda card (`card: {title, agenda: true}`) with one `say:` sentence per chapter, so each line appears as it's said.
2. **What we measured.** Show where the data came from (trace, benchmark, device, date) and what the span covers. Before any number appears, use a `flow:` beat to show the steps of the process and a bracket over the part that was timed.
3. **What was going on.** Show the before state only. Walk the viewer's eye to the one stage that matters with `focus:`, and give one fact per beat.
4. **The fix.** Say what changed in one sentence of cause and effect, then show the after state against the before.
5. **Side effects.** Cover anything the fix could have broken (a crash path, a retry, a fallback) and show the evidence that it didn't.
6. **What's left.** List what isn't done, what wasn't measured, and the sample size, stated plainly and without a sign-off.

Open each chapter with its agenda card lit (`card: {agenda: true}` with `chapter:` set) and one short spoken line. Drop a chapter the change doesn't need, since five chapters is a ceiling, not a target.

## Rules for every line

- **Everything said is on screen.** If a sentence names a thing, that thing is visible, highlighted, or appearing as the sentence starts. Write `say:` as a list, one sentence per visual change. If a sentence has nothing to point at, cut it or add the visual.
- **Ground a term before you lean on it.** The first time a concept appears ("warm machine", "stream target"), say what it is in plain words while it's on screen. Only then can later beats use the short name. Rename jargon in charts with `labels:` rather than explaining span names aloud.
- **Plain English.** Write short sentences in the active voice, with words a new teammate would use. Say "the stream target is locked in", not "identity selection completes". Keep code names and PR numbers out of the voice and in the source line, unless the viewer needs them.
- **One fact per beat.** The heading states the fact ("The game was drawing by 13 s"), the caption adds one supporting detail, and the voice says both in sentence form. Don't stack three numbers on one screen.
- **Don't misrepresent.** Every number traces back to the source file. Round the same way everywhere (for example 42.749 becomes 42.7 on screen and "about 43" in speech, never "40"). Say "one sample each" when it is. If the fix removed a wait rather than making something faster, say that.
- **Match the screen and the voice.** A number spoken aloud is the number on screen, and a stage named aloud uses the same name as its row label.

## Before rendering

Read the script aloud from top to bottom and check:

- Could someone who skipped the PR follow it? Mark every term used before it was explained.
- For each sentence, what's on screen while it's said?
- Does every number match the source file?
- Is anything said twice? Cut the second one.
- Pacing: a 10-minute change should fit in 1 to 3 minutes. Cut beats before speeding up the voice.

Then render silently first (`proof run --no-narrate`) and read the contact sheet, before paying for narration.

## Example shape

```yaml
beats:
  - card: {title: "Checkout loads in 1.2 seconds, down from 3.4", agenda: true}
    say:
      - "One change cut checkout load time from 3.4 seconds to 1.2."
      - "First, we'll look at what we measured, and where the numbers come from."
      - "Then, what was slowing it down."
      - "Then, the fix."
      - "And last, what's still left to do."
  - card: {agenda: true}
    chapter: What we measured
    say: "First, what we measured."
  - flow:
      title: What happens when someone opens checkout
      source: "Browser trace, staging, 2026-09-29"
      steps: [Tap Checkout, {label: Cart fetched, at: 1}, {label: Prices fetched, at: 2}, {label: Page drawn, at: 3}]
      span: {from: 1, to: 3, label: "What we timed", at: 3}
    say:
      - "When someone taps Checkout, three things happen."
      - "The page fetches the cart,"
      - "then the prices for each item,"
      - "and then it draws. We timed from the cart fetch to the first draw."
```
