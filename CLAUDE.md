# Maintainer notes (for Claude Code)

This is the **development** guide for the `econ-paper` Quarto
extension. User-facing docs (install, usage, markdown idioms) live
in [README.md](README.md). If you're answering a question about how
to *use* the extension, point the user there.

If you're answering a question about how to *change* this repo,
keep going.

## What this repo is

A Quarto format extension at `_extensions/econ-paper/` plus three
starter templates and shared `sections/` at the repo root. Single
purpose: produce health-econ / applied-econ PDF and HTML manuscripts
with separate main/appendix bibliographies, independently numbered
appendix tables, and journal-style notes.

The repo is **self-contained**: no Quarto extension dependencies.
`multibib.lua` and `the-lancet.csl` are vendored under
`_extensions/econ-paper/{filters,csl}/` with upstream credit in
[LICENSE](LICENSE).

## Layout (only the parts that matter when editing)

```
_extensions/econ-paper/
  _extension.yml        — format definition + filter list + crossref kinds
  filters/
    inject-bib.lua             — multibib-bibliography YAML key → bibliography map
    author-format-flags.lua    — `author-format: <v>` → `author-format-<v>: true`
    protect-quarto-xref.lua    — stash Quarto crossref Cites as Spans before
                                 multibib's citeproc pass (else Lancet-style
                                 CSL absorbs the leading space)
    div-to-env.lua             — .tblnotes / .landscape divs → LaTeX envs
    supplementary.lua          — # Foo {.supplementary} → centered uppercase
    multibib.lua               — vendored (Albert Krewinkel, ISC); don't edit
    restore-quarto-xref.lua    — restore stashed Spans → Cites so Quarto's
                                 internal crossref filter sees them normally
  partials/
    _include-in-header.tex  — packages, caption skips, float placement,
                              CSLReferences override, tblnotes env,
                              caption-patch for apx envs, citeproc →
                              \hyperlink override for clickable citations
    before-body.tex         — title block; branches on `author-format`
                              between numeric-superscript, horizontal AEA
                              and vertical AEA layouts
  csl/the-lancet.csl    — vendored (CC BY-SA 3.0); don't edit

template.qmd, template-numeric.qmd, template-lancet.qmd  — three sibling
                                                            variants users pick from
sections/_main.qmd, sections/_appendix.qmd               — shared body content

.github/workflows/render.yml — CI: render on push, attach PDF on tag push
images/preview-*.png         — README screenshots (refreshed by CI)
```

## Non-obvious decisions and why

These took real time to figure out — don't undo without understanding
the constraint:

| Pattern                                                       | Why                                                                                                                                                                            |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `multibib-bibliography:` (non-standard) instead of `bibliography:` as a map | Quarto's YAML schema validator rejects `bibliography:` as a map. `inject-bib.lua` rewrites the non-standard key into the standard slot, before pandoc sees it.                                                  |
| `_extensions/econ-paper/` at source (no owner namespace)      | Quarto's template installer adds the owner namespace (`fikrurizal/`) on install. If the source already has it, `quarto use template` silently fails to copy the extension.                                     |
| Caption `\vspace*{-1em}` patch inside apx envs                | Pandoc emits two blank-line `\par`s between `\caption{...}` and the table body (≈32pt under onehalfspacing). Caption-package `skip`/`belowskip` can't see them; `-2em` overshot and made the toprule overlap the caption.                                |
| `\AtBeginDocument{\floatplacement{apx*}{H}}`                  | Quarto declares the custom appendix floats with default `[h]`, so LaTeX can drift them onto later pages — and a `.tblnotes` block underneath then prints before its table.                                                                              |
| `\let\NAT@force@numbers\@empty` in the include-in-header      | Defensive: if the aea (`hchulkim/econ-paper-template`) extension is *also* loaded in a user project, it auto-loads natbib, which then chokes on citeproc's `\bibitem[\citeproctext]` output. The neutralizer makes the mix survive.                      |
| `geom_bin2d` not `geom_hex` in `sections/_appendix.qmd`       | `geom_hex` silently renders an empty plot when the `hexbin` package isn't installed (common in CI). `geom_bin2d` is base ggplot2.                                                                                                                       |
| Multi-panel figure via `patchwork`, not Quarto subfigures     | Native Quarto subfigures (`layout-ncol=2`) inside custom crossref kinds (`apxafig`) render with stacked panels and overlapping captions. `patchwork::wrap_plots` produces one float, one caption, panels side-by-side, reliably.                       |
| `\RenewDocumentCommand\citeproc{mm}{\hyperlink{#1}{#2}}` + `\AtBeginEnvironment{CSLReferences}` patching `\bibitem` to plant `\hypertarget` | Pandoc emits citations as `\citeproc{ref-key}{text}` and defines that as a natbib bridge (`\cite{ref-key}` inside a group). With CSL bibitems (`\bibitem[\citeproctext]{ref-key}`) the natbib chain breaks: `\citeproctext` is globally empty, so .aux records an empty label and `\cite` renders nothing. Pandoc considers this intended (see [pandoc#9022/#9031](https://github.com/jgm/pandoc/issues/9022)); the natbib bridge is meant for natbib-format bibs, not CSL. Loading natbib alone produces clickable-but-empty citations (verified). The override jumps straight to a `\hypertarget` we plant at each bibitem — sidesteps `\cite` entirely. Brittle on pandoc upgrade (silent fallback to plain-text citations); the CI smoke test should assert `/Subtype /Link` count > 0 in `template.pdf`. |
| `protect-quarto-xref.lua` + `restore-quarto-xref.lua` around `multibib.lua` | In Quarto's default flow, the crossref filter runs *before* citeproc, so crossref `@tbl-foo` Cites never reach citeproc. With multibib, multibib's citeproc invocation is a *user* filter — user filters run *before* Quarto's internal crossref filter. So crossref Cites (`@apxatbl-summary` etc.) get fed through citeproc and styles that attach citations to the preceding word (Lancet's superscript) eat the leading `Space` AST node. The pair of filters stashes crossref-pattern Cites in Spans before multibib (citeproc passes Spans through), then converts back after. Pattern list lives in `protect-quarto-xref.lua` — add new Quarto crossref prefixes there. |
| Unified `before-body.tex` with `$if(author-format-numeric)$ ... $elseif(author-format-horizontal)$` branching, driven by `author-format-flags.lua` | The earlier design had two partial files (`before-body.tex` and `before-body-numeric.tex`) selected via Quarto's `template-partials:` YAML. But pandoc identifies partials by **basename matching a known slot name** (`before-body`, `header-includes`, …); a basename of `before-body-numeric` matches no slot, so the override silently no-op'd and `template-numeric.qmd` was rendering with the default AEA stack — broken since extension creation, visible only by inspecting the title block. The lua filter translates `author-format: <value>` into per-value flags so pandoc's template (which can't compare strings directly) can branch via `$if(...)$`. |
| `\AtBeginDocument{\floatplacement{table}{H}\floatplacement{figure}{H}}` for main-text floats | Quarto's chunk-level `tbl-cap` / `fig-cap` wraps the chunk output in its own `\begin{table}` / `\begin{figure}` without `[H]`. The YAML keys `tbl-pos: H` / `fig-pos: H` don't reach these wrappers in the current Quarto version (verified by inspecting `template.tex`). Without forced placement, the main-text modelsummary table drifts to the top of the next page, pulling its `* p < 0.1, **...` footer with it and visually separating it from "The main result is summarized in Table 1." Forcing `H` globally pins them to source. |
| `dev = if (knitr::is_latex_output()) "pdf" else "svglite"` in setup chunk | Setting `dev = "pdf"` unconditionally makes the HTML render embed PDFs via `<embed src=...pdf>`, which browsers wrap in a PDF-viewer toolbar/frame around every figure. SVG via `svglite` is vector everywhere (no Inkscape required, unlike the `svg` LaTeX package). The CI workflow installs `any::svglite`. |
| `tblnotes`/`fignotes` = `\par\nointerlineskip\vspace*{-\intextsep}\vspace*{\noteTopGap}` + tables inside float divs kept as BARE tabulars (no `hold_position`, `position = "left"`) | An `[H]` float ends with exactly one `\vskip\intextsep`, so cancelling it and suppressing the first line's interline glue makes the visible gap exactly `\noteTopGap` (4pt) — deterministic across float kinds and font sizes. This only holds if the float body carries no extra glue of its own: kableExtra's `hold_position`/`position = "center"` wrap the tabular in a nested `\begin{table}`, and Quarto strips that wrapper only for float kinds with reference-prefix exactly "Table" (`maintbl`) — NOT for the `apx*` kinds — which made appendix notes sit ~1 `\intextsep` lower than main-text ones. Markdown pipe tables emit `longtable*`; its `\LTpre`/`\LTpost` glue is zeroed inside the table float kinds for the same reason. No left/right indent — most journal styles want notes spanning full text width. |
| `space-before-numbering: true` for `maintbl` but `false` for the `apx*` kinds | The flag controls the space between reference-prefix and counter in in-text refs. "Table A" + `false` → "Table A1" (wanted); "Table" needs `true` or refs render as "Table1". |
| `supplementary.lua` emits `\clearpage\setcounter{page}{1}` before the APPENDIX divider | Without it, the appendix continues main-text page numbering (e.g., main 1–5, appendix 6–10). Most journals expect appendix pages to restart at 1. To revert to continued numbering, drop the `\setcounter{page}{1}` from the raw block. |

## How to test a change

After editing any extension file:

1. **Local source-side render** (fast, tests the extension as a file
   tree without going through `quarto add`):
   ```bash
   cd c:/Users/friz0005/quarto-econ-paper
   quarto render template.qmd
   ```
   This works because `_extensions/econ-paper/` at the repo root
   matches what Quarto looks for when rendering from the same
   directory. **But**: paths in `template-numeric.qmd` and
   `template-lancet.qmd` reference `_extensions/fikrurizal/econ-paper/...`
   (where Quarto installs into a *user* project). Those variants will
   fail when rendered from the source repo. Test them via path #2 or
   the install-side mirror trick (path #1b).

1b. **Install-side mirror trick** (source-side render of the variants
    without pushing): replicate the install-side path locally so the
    variants resolve their `_extensions/fikrurizal/econ-paper/...`
    references against the same source tree you're editing.

    ```bash
    rm -rf _extensions/fikrurizal
    mkdir _extensions/fikrurizal
    cp -r _extensions/econ-paper _extensions/fikrurizal/econ-paper
    quarto render template-numeric.qmd
    quarto render template-lancet.qmd
    rm -rf _extensions/fikrurizal
    ```

    Quarto's extension resolution prefers a local match for the named
    extension, so this lets you iterate on all three variants without
    waiting for a CI cycle. The mirror is gitignored by virtue of the
    `fikrurizal` directory being absent from the tracked tree —
    don't accidentally `git add` it.

    **Always test all three variants** before declaring a change
    done. Recent silent failures: `template-numeric.qmd` was
    broken since extension creation because its title-block override
    used a partial basename pandoc doesn't recognise; the Lancet
    variant absorbed leading spaces around crossref Cites because
    its CSL attaches citations to the preceding word. Both fixed
    once the variants were exercised — not before.

2. **Installed-side render** (full integration, tests what users
   will actually experience):
   ```bash
   rm -rf /tmp/qep-scratch && mkdir -p /tmp/qep-scratch && cd /tmp/qep-scratch
   quarto use template fikrurizal/quarto-econ-paper --no-prompt
   quarto render qep-scratch.qmd
   quarto render template-numeric.qmd
   quarto render template-lancet.qmd
   ```
   This pulls from `main` on GitHub (or the latest tag if specified),
   so the change must be pushed first. Use a feature branch + the
   branch name in `quarto use template` to test before merging:
   `quarto use template fikrurizal/quarto-econ-paper@my-branch`.

3. **Check CI**: every push to `main` (and every PR) runs
   `.github/workflows/render.yml`, which renders `template.qmd` on
   a clean Ubuntu runner with R 4.5 + TinyTeX, refreshes preview
   PNGs, and uploads the PDF as an artifact. CI catches "works on
   my machine but missing an R package declaration" failures.

## Release process

1. Make changes on a branch, open a PR, let CI pass.
2. Merge to `main`.
3. Bump the version in `_extensions/econ-paper/_extension.yml`
   (`version: 0.1.x`).
4. Tag and push:
   ```bash
   git tag v0.1.x && git push --tags
   ```
5. CI then runs the workflow on the tag, attaches the freshly
   rendered `template.pdf` to a new GitHub release with
   auto-generated release notes.

Force-updating an existing tag (`git tag -f v0.1.0 && git push -f`)
is acceptable for the *first* point release while the project is at
v0.x.y and adoption is low. Once anyone has installed via a tagged
version, treat tags as immutable and bump.

## Common dev tasks

**Add a new crossref kind** (e.g., Appendix C with `Table C1`,
`Figure C1`):
- Add two entries to `crossref.custom:` in
  `_extensions/econ-paper/_extension.yml` (`apxctbl` + `apxcfig`).
- Add matching `\AtBeginEnvironment{apxctbl}{...}` and
  `\AtBeginEnvironment{apxcfig}{...}` lines in the caption-patch
  and floatplacement blocks of
  `_extensions/econ-paper/partials/_include-in-header.tex`.

**Swap or add a CSL**:
- Drop the file into `_extensions/econ-paper/csl/`.
- Add a `template-foo.qmd` sibling at the repo root if it deserves
  a dedicated variant, otherwise just document in README that users
  can set `csl: _extensions/fikrurizal/econ-paper/csl/foo.csl`.

**Refresh the user-level skill** (when the public API of the
extension changes — new format names, new markdown idioms, etc.):
- The skill lives at
  `c:/Users/friz0005/.claude/skills/quarto-econ-paper/SKILL.md`
  (not in this repo — it's user-level).
- Update the trigger description, the adoption-checklist, and the
  "Where things live" section to match.

**Update preview screenshots** (when the rendered output changes
visibly):
- Don't bother manually — the CI workflow re-renders and commits
  refreshed preview PNGs on every push to `main`.

## What's deliberately out of scope

- A `econ-paper-lancet-pdf` *format* (separate format that bakes in
  the Lancet CSL). The variant works via the `csl:` YAML key on top
  of `econ-paper-pdf`; one format per citation style would explode
  the surface area.
- Subfigure support for custom crossref kinds. Patchwork is the
  documented workaround and is more reliable.
- Word output. The aea-style title block uses LaTeX `\thanks`; the
  custom envs assume the LaTeX writer. HTML works because the
  filters are format-aware (`if FORMAT == "html"`). docx is not
  currently a goal.
