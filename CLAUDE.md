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
    inject-bib.lua      — multibib-bibliography YAML key → bibliography map
    div-to-env.lua      — .tblnotes / .landscape divs → LaTeX envs
    supplementary.lua   — # Foo {.supplementary} → centered uppercase divider
    multibib.lua        — vendored (Albert Krewinkel, ISC); don't edit
  partials/
    _include-in-header.tex  — packages, caption skips, float placement,
                              CSLReferences override, tblnotes env,
                              caption-patch for apx envs
    before-body.tex         — AEA-style title block (default)
    before-body-numeric.tex — numeric-superscript title block (variant)
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
   fail when rendered from the source repo. Test them via path #2.

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
