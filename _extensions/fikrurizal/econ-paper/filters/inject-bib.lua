-- Move user-provided `multibib-bibliography:` (a map of topic-name →
-- bib file) into the standard pandoc `bibliography:` slot, as a
-- MetaMap that the multibib filter knows how to handle.
--
-- Quarto's YAML schema refuses to accept `bibliography:` as a map
-- (the validator requires a string or list of strings), so we expose
-- a sibling unknown-to-the-schema key and rewrite it here. The user
-- writes, in their document YAML:
--
--   multibib-bibliography:
--     main: refs-main.bib
--     appendix: refs-appendix.bib
--
-- and references the same topic names in the per-topic ref divs:
--
--   ::: {#refs-main}
--   :::
--   ::: {#refs-appendix}
--   :::

function Meta(m)
  local bib = m["multibib-bibliography"]
  if not bib then
    return nil
  end

  if pandoc.utils.type(bib) ~= "table" then
    io.stderr:write("[inject-bib] expected `multibib-bibliography` "
                    .. "to be a map of topic-name -> bib file path; "
                    .. "skipping.\n")
    return nil
  end

  local out = pandoc.MetaMap({})
  for k, v in pairs(bib) do
    out[k] = pandoc.MetaInlines{ pandoc.Str(pandoc.utils.stringify(v)) }
  end
  m.bibliography = out
  return m
end
