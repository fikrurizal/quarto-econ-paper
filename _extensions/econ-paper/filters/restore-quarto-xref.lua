-- Convert the Spans planted by `protect-quarto-xref.lua` back into
-- Cite elements after multibib's citeproc pass has run. The restored
-- Cites are then consumed by Quarto's internal crossref filter, which
-- runs after all user filters. See `protect-quarto-xref.lua` for the
-- full rationale.

local function string_to_mode(s)
  if s == "AuthorInText" then return pandoc.AuthorInText end
  if s == "SuppressAuthor" then return pandoc.SuppressAuthor end
  return pandoc.NormalCitation
end

function Span(s)
  if not s.classes:includes("_qep_xref_stash") then return nil end
  local id = s.attributes.id
  if not id or id == "" then return nil end
  local mode = string_to_mode(s.attributes.mode)
  return pandoc.Cite(s.content, {pandoc.Citation(id, mode)})
end
