-- Stash Quarto crossref Cite elements as Spans so multibib's citeproc
-- pass (which runs next) ignores them. The companion filter
-- `restore-quarto-xref.lua` runs after multibib to convert the Spans
-- back into Cite elements before Quarto's own crossref filter sees them.
--
-- Why this is needed:
-- In Quarto's default flow (without multibib), Quarto runs its crossref
-- filter BEFORE its citeproc pass, so crossref Cite elements never
-- reach citeproc. When multibib is loaded it runs citeproc itself as a
-- user filter — and user filters run BEFORE Quarto's internal filters
-- (including crossref). So crossref Cites get passed through citeproc.
--
-- For most citation styles this is harmless: citeproc emits a "?"
-- placeholder for the unresolved key and Quarto's crossref filter
-- still recognises it. But citation styles where citations attach to
-- the preceding word (e.g. Lancet's superscript number style) cause
-- citeproc to absorb the preceding `Space` inline into the citation
-- rendering. The result is `\quartoapxatblref{...}` with no leading
-- space — `see Table A1` becomes `seeTable A1` in the PDF.
--
-- Stashing crossref Cites in Spans defangs the side-effect: the
-- Span structure preserves the surrounding Spaces verbatim, and
-- citeproc passes Spans through unchanged.

local crossref_prefixes = {
  -- Quarto built-in crossref kinds (see
  -- https://quarto.org/docs/authoring/cross-references.html)
  "tbl%-", "fig%-", "sec%-", "eq%-", "thm%-", "lem%-", "cor%-",
  "prp%-", "cnj%-", "def%-", "exm%-", "exr%-", "rem%-", "alg%-",
  "lst%-", "fnr%-",
  -- This extension's custom kinds
  "apxatbl%-", "apxbtbl%-", "apxafig%-", "apxbfig%-",
}

local function is_crossref_id(id)
  if not id then return false end
  for _, p in ipairs(crossref_prefixes) do
    if id:match("^" .. p) then return true end
  end
  return false
end

local function mode_string(mode)
  if mode == nil then return "NormalCitation" end
  if type(mode) == "string" then return mode end
  -- Pandoc Lua enum value — its tostring lookup varies by version;
  -- the safest is to compare against the named constants.
  if mode == pandoc.AuthorInText then return "AuthorInText" end
  if mode == pandoc.SuppressAuthor then return "SuppressAuthor" end
  return "NormalCitation"
end

function Cite(c)
  if not c.citations or #c.citations == 0 then return nil end
  local cit = c.citations[1]
  if not is_crossref_id(cit.id) then return nil end
  return pandoc.Span(c.content, pandoc.Attr("",
    {"_qep_xref_stash"},
    {id = cit.id, mode = mode_string(cit.mode)}))
end
