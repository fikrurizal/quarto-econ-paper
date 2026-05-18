-- Render a Header with class `.supplementary` as a centered uppercase
-- divider (PDF) or a plain h2 with the class preserved (HTML).
--
-- Used to mark the start of the appendix section, e.g.
--   # Appendix {.supplementary}
-- which prints "APPENDIX" centered in bold in the PDF and as a normal
-- heading in HTML. Logic mirrors the aea extension's aea.lua, vendored
-- here so this extension is self-contained.

function Header(el)
  if not el.classes:includes("supplementary") then
    return nil
  end

  if quarto.doc.is_format("pdf") then
    local title_text = pandoc.text.upper(pandoc.utils.stringify(el.content))
    return pandoc.Div({
      pandoc.RawBlock("latex",
        "\\bigskip\n\\begin{center}{\\large\\bf " .. title_text .. "}\\end{center}\n")
    }, el.attr)
  end

  if quarto.doc.is_format("html") then
    return pandoc.Header(2, el.content,
      pandoc.Attr(el.identifier, {"supplementary", "unnumbered"}, el.attributes))
  end
end
