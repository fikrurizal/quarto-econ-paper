-- For docx output only, fold each author's affiliations into the
-- author meta-string so the title block shows them. By the time
-- user-level filters run, Quarto has flattened `meta.author` to a
-- list of plain Inlines containing just the name — affiliations have
-- been moved out into the structured store `meta["by-author"]`. We
-- read `by-author`, build "Name (Department, University; ...)"
-- strings, and overwrite `meta.author` with the result. Pandoc's
-- docx writer then renders each as an Author paragraph.
--
-- Skipped for non-docx formats: PDF uses its own AEA-style title-
-- block partial that consumes the structured affiliations directly,
-- and HTML uses Quarto's own author/affiliation rendering.

local function s(x)
  if x == nil then return nil end
  local out = pandoc.utils.stringify(x)
  if out == "" then return nil end
  return out
end

local function full_name(name_tbl)
  if pandoc.utils.type(name_tbl) ~= "table" then
    return s(name_tbl)
  end
  if name_tbl.literal then return s(name_tbl.literal) end
  local given = s(name_tbl.given)
  local family = s(name_tbl.family)
  if given and family then return given .. " " .. family end
  return given or family
end

local function affiliation_label(aff)
  local parts = {}
  local dept = s(aff.department)
  local name = s(aff.name)
  if dept then table.insert(parts, dept) end
  if name then table.insert(parts, name) end
  if #parts == 0 then return nil end
  return table.concat(parts, ", ")
end

function Meta(m)
  if FORMAT ~= "docx" then return nil end
  local by_author = m["by-author"]
  if not by_author then return nil end

  local new_authors = pandoc.MetaList({})
  for _, a in ipairs(by_author) do
    local name = full_name(a.name) or ""
    local affs = {}
    if a.affiliations then
      for _, aff in ipairs(a.affiliations) do
        local label = affiliation_label(aff)
        if label then table.insert(affs, label) end
      end
    end
    local entry = name
    if #affs > 0 then
      entry = entry .. " (" .. table.concat(affs, "; ") .. ")"
    end
    table.insert(new_authors, pandoc.MetaInlines({pandoc.Str(entry)}))
  end
  m.author = new_authors
  return m
end
