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
end
