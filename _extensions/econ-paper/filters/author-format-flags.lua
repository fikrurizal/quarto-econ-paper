-- Translate `author-format: <value>` (a single string) into per-value
-- boolean meta flags `author-format-<value>: true` that pandoc's
-- LaTeX title-block template can branch on.
--
-- Pandoc template syntax doesn't support direct string equality
-- (`$if(author-format=='numeric')$` is not valid), so this filter
-- normalises the single user-facing key into the multiple boolean
-- flags the template needs.
--
-- Supported values (matched verbatim, lowercased):
--   horizontal — AEA-style title block, authors side-by-side via \and
--   numeric    — numeric superscript affiliations, deduped affiliation
--                list below (biomedical-journal style)
-- Any other value is silently ignored; the template falls through to
-- a stacked vertical AEA layout.

function Meta(m)
  local raw = m["author-format"]
  if not raw then return nil end
  local format = pandoc.utils.stringify(raw):lower()
  if format == "" then return nil end
  m["author-format-" .. format] = true
  return m
end
