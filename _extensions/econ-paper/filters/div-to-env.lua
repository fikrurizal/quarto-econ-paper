-- Wrap Quarto divs in a matching LaTeX environment, by class name.
-- Quarto preserves div classes as HTML classes (so CSS can target
-- `.tblnotes` in the HTML output), but in the LaTeX writer it does
-- not auto-wrap the div contents in `\begin{tblnotes}...\end`. This
-- filter does that wrapping for the classes listed in `class_to_env`.
--
-- The environment itself is defined in _include-in-header.tex.

local class_to_env = {
  tblnotes  = "tblnotes",
  landscape = "landscape",  -- from lscape/pdflscape package
}

function Div(el)
  if FORMAT:match("latex") then
    for class, env in pairs(class_to_env) do
      if el.classes:includes(class) then
        local pre  = pandoc.RawBlock("latex", "\\begin{" .. env .. "}")
        local post = pandoc.RawBlock("latex", "\\end{" .. env .. "}")
        table.insert(el.content, 1, pre)
        table.insert(el.content, post)
        return el.content
      end
    end
  end

  if FORMAT == "docx" then
    -- Tag .tblnotes paragraphs with a custom-style attribute. The
    -- bundled reference.docx defines styleId "TableNotes" (name
    -- "Table Notes"): Times New Roman 10pt, single-spaced,
    -- justified. Pandoc emits this as `w:pStyle w:val="TableNotes"`.
    if el.classes:includes("tblnotes") then
      for i, block in ipairs(el.content) do
        if block.t == "Para" or block.t == "Plain" then
          local attr = pandoc.Attr("", {}, {["custom-style"] = "TableNotes"})
          el.content[i] = pandoc.Div({block}, attr)
        end
      end
      return el.content
    end

    -- Rotate .landscape divs by wrapping them in OOXML section breaks.
    -- A `w:sectPr` inside a paragraph's `w:pPr` describes the section
    -- that *ends* with that paragraph, so the pattern is: emit a
    -- portrait sectPr paragraph BEFORE the rotated content (closing
    -- the preceding portrait section), then a landscape sectPr
    -- paragraph AFTER (closing the rotated section as landscape).
    -- The doc's final sectPr (portrait, from reference.docx) governs
    -- everything after.
    --
    -- Page dimensions match the bundled reference.docx: A4 portrait
    -- (11906x16838 twips = 210x297mm). If you swap to a US Letter
    -- reference doc, change these to 12240x15840.
    if el.classes:includes("landscape") then
      local portrait_break = pandoc.RawBlock("openxml",
        '<w:p><w:pPr><w:sectPr>' ..
        '<w:pgSz w:w="11906" w:h="16838"/>' ..
        '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"' ..
        ' w:header="720" w:footer="720" w:gutter="0"/>' ..
        '<w:cols w:space="720"/>' ..
        '</w:sectPr></w:pPr></w:p>')
      local landscape_break = pandoc.RawBlock("openxml",
        '<w:p><w:pPr><w:sectPr>' ..
        '<w:pgSz w:w="16838" w:h="11906" w:orient="landscape"/>' ..
        '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"' ..
        ' w:header="720" w:footer="720" w:gutter="0"/>' ..
        '<w:cols w:space="720"/>' ..
        '</w:sectPr></w:pPr></w:p>')
      table.insert(el.content, 1, portrait_break)
      table.insert(el.content, landscape_break)
      return el.content
    end
  end
end
