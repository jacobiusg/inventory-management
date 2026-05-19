---
name: vue-analyze
description: Analyze Vue 3 components in client/src for reactivity hygiene and reuse opportunities, then produce a prioritized report of suggested optimizations. Invoked via the /vue-analyze slash command.
---

# Vue Component Analyzer

Analyze Vue 3 Composition API components under `client/src/` and report optimization opportunities in two areas: **reactivity hygiene** and **reuse**. Stop at recommendations — do not edit files unless the user explicitly asks for a follow-up fix.

## Scope

When the user runs `/vue-analyze`:

- **No argument:** analyze all `.vue` files under `client/src/views/` and `client/src/components/`.
- **Path/glob argument:** analyze only that file or matching files (e.g. `/vue-analyze client/src/views/Orders.vue`).

Read every targeted `.vue` file in full before reporting. Also read any composable in `client/src/composables/` referenced by the targets, so reuse comparisons are grounded.

## What to check

### 1. Reactivity hygiene

For each component, flag:

- **`ref` / `reactive` misuse** — primitives wrapped in `reactive`, objects unnecessarily destructured from `reactive` (losing reactivity), nested `ref` of `ref`.
- **`computed` vs method** — derived values defined as functions called from the template (re-runs on every render) that should be `computed`.
- **`watch` that should be `computed`** — watchers whose only job is to set another ref from existing reactive state.
- **Expensive template expressions** — non-trivial computation, `.filter().map().reduce()` chains, or `new Date()` calls inline in templates; should be `computed`.
- **`v-for` keys** — `:key="index"` or missing `:key`; flag and suggest a stable identifier (sku, id, etc., per repo convention in CLAUDE.md).
- **`v-if` + `v-for` on same element** — anti-pattern; suggest extracting `v-if` to a wrapper or pre-filtering via `computed`.
- **Unstable prop identities** — inline object/array literals passed as props (`:foo="{ a: 1 }"`) that cause child re-renders; suggest hoisting to a `computed` or constant.
- **Missing `shallowRef` / `shallowReactive`** — large, mostly-immutable data structures (lookup tables, big JSON blobs) using deep reactivity.

### 2. Reuse opportunities

Across the analyzed set, look for:

- **Duplicated `<template>` fragments** — near-identical markup blocks (≥ ~8 lines) in 2+ files; suggest a shared component, possibly under `client/src/components/`.
- **Duplicated script logic** — repeated data-fetching, filtering, formatting, or status-mapping logic; suggest a composable in `client/src/composables/` (the repo already has `useAuth`, `useFilters`, `useI18n` — match that naming).
- **Repeated formatters** — currency / date / percent formatters defined per-component; suggest a single `client/src/utils/format.js` (or composable) and consolidate.
- **Inline status-color / badge logic** — repeated `class` ternaries mapping status → color; suggest a shared `<StatusBadge>` component or a lookup map.
- **Repeated filter wiring** — components manually reading the same query params or filter state that `useFilters` already exposes; flag as candidates to migrate.

## Output format

Produce a single Markdown report with this structure. Keep it skimmable — no preamble, no closing summary.

```
# Vue analysis: <N> files

## Reactivity findings
### <file>:<line>
**<short title>** (severity: high|med|low)
<one-sentence problem>
**Suggestion:** <one-sentence fix, with the exact replacement pattern when short>

## Reuse findings
### <pattern name>
Found in:
- <file>:<line-range>
- <file>:<line-range>
**Suggestion:** <extract to component / composable / util, with proposed name and path>
```

Order findings by severity (high → low) within each section. Cap at the top ~15 findings per section; if more, end with `... and N more (run with a narrower path to see them)`.

## Severity guide

- **High** — measurable runtime impact (re-render storms, O(n²) in template, missing keys causing DOM thrash) or duplicated logic in 3+ files.
- **Medium** — clear cleanup win but bounded impact (single computed that could be cached, two-file duplication).
- **Low** — stylistic / future-proofing (could be `shallowRef`, minor consolidation).

## Out of scope

- Bundle size / lazy-loading (user opted out).
- Re-render hotspot benchmarking (user opted out).
- Auto-fixing — only report. If the user follows up asking to apply a finding, delegate the actual `.vue` edits to the `vue-expert` subagent per the repo's CLAUDE.md rule.

## Project conventions to respect

From `CLAUDE.md`:
- Stable keys per repo: `sku`, `month`, `id` — never `index`.
- Raw data in `ref`, derived data in `computed` — flag deviations.
- No emojis in UI — do not suggest any.
- Filters: `useFilters` is the canonical source — suggest migrating ad-hoc filter state to it.
