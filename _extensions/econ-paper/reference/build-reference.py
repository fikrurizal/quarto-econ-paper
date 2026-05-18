"""Build econ-paper-reference.docx from scratch.

A pandoc reference doc only needs styles.xml, settings.xml,
fontTable.xml, document.xml, and the rels — pandoc reads the
style definitions and ignores the body content.

Units (OOXML):
  * 1 pt = 2 half-points (used for sz / szCs)
  * 1 pt = 20 twentieths-of-a-point (used for spacing/indents/margins)
  * A4 = 11906 x 16838 twips (210 x 297 mm)
  * 1 in = 1440 twips

Style mapping (pandoc styleId -> our intent):
  BodyText / FirstParagraph / Normal -> Times 12pt, 1.5 line, justified, black
  Heading1                            -> Times bold 14pt, 12pt before/after
  Heading2                            -> Times bold 12pt, 6pt before/after
  Heading3                            -> Times bold italic 12pt
  Heading4..9                         -> Times italic 12pt
  Caption / ImageCaption / TableCaption -> Times 12pt, centered
  TableNotes (custom)                 -> Times 10pt, single, justified
  FootnoteText                        -> Times 10pt, single
  Bibliography                        -> Times 12pt, single, hanging 0.5"
  Title / Author / Abstract           -> Title block
  BlockText / Quote                   -> Times italic 12pt, indented 0.5"

Run this whenever the spec changes:
    python _extensions/econ-paper/reference/build-reference.py
"""

import zipfile
from pathlib import Path

OUT = Path(__file__).parent / "econ-paper-reference.docx"

# ---------------------------------------------------------------------------
# Style XML fragments
# ---------------------------------------------------------------------------

# Twips helpers — write as ints
PT = lambda pt: int(pt * 20)         # noqa: E731  point -> twip (spacing/indent)
HALF = lambda pt: int(pt * 2)        # noqa: E731  point -> half-point (sz)

def style_para(style_id, name, *, based_on=None, font="Times New Roman",
               sz_pt=12, bold=False, italic=False, color="000000",
               line_twips=None, line_rule="auto",
               before_twips=0, after_twips=0,
               jc=None, ind=None, next_style=None, link=None):
    """Render a <w:style> for a paragraph style."""
    parts = [f'<w:style w:type="paragraph" w:styleId="{style_id}">',
             f'<w:name w:val="{name}"/>']
    if based_on:
        parts.append(f'<w:basedOn w:val="{based_on}"/>')
    if next_style:
        parts.append(f'<w:next w:val="{next_style}"/>')
    if link:
        parts.append(f'<w:link w:val="{link}"/>')
    # pPr
    ppr = []
    spacing_attrs = []
    if line_twips is not None:
        spacing_attrs.append(f'w:line="{line_twips}" w:lineRule="{line_rule}"')
    spacing_attrs.append(f'w:before="{before_twips}" w:after="{after_twips}"')
    ppr.append(f'<w:spacing {" ".join(spacing_attrs)}/>')
    if jc:
        ppr.append(f'<w:jc w:val="{jc}"/>')
    if ind:
        ppr.append(f'<w:ind {ind}/>')
    parts.append('<w:pPr>' + ''.join(ppr) + '</w:pPr>')
    # rPr
    rpr = [f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}" w:eastAsia="{font}" w:cs="{font}"/>']
    if bold:
        rpr.append('<w:b/><w:bCs/>')
    if italic:
        rpr.append('<w:i/><w:iCs/>')
    rpr.append(f'<w:color w:val="{color}"/>')
    rpr.append(f'<w:sz w:val="{HALF(sz_pt)}"/><w:szCs w:val="{HALF(sz_pt)}"/>')
    parts.append('<w:rPr>' + ''.join(rpr) + '</w:rPr>')
    parts.append('</w:style>')
    return ''.join(parts)


def style_char(style_id, name, *, based_on="DefaultParagraphFont",
               font="Times New Roman", sz_pt=12, bold=False, italic=False,
               color="000000"):
    parts = [f'<w:style w:type="character" w:styleId="{style_id}">',
             f'<w:name w:val="{name}"/>',
             f'<w:basedOn w:val="{based_on}"/>']
    rpr = [f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}" w:eastAsia="{font}" w:cs="{font}"/>']
    if bold:
        rpr.append('<w:b/><w:bCs/>')
    if italic:
        rpr.append('<w:i/><w:iCs/>')
    rpr.append(f'<w:color w:val="{color}"/>')
    rpr.append(f'<w:sz w:val="{HALF(sz_pt)}"/><w:szCs w:val="{HALF(sz_pt)}"/>')
    parts.append('<w:rPr>' + ''.join(rpr) + '</w:rPr>')
    parts.append('</w:style>')
    return ''.join(parts)


# ---------------------------------------------------------------------------
# Build styles.xml
# ---------------------------------------------------------------------------

# Body-paragraph defaults: Times 12pt, 1.5 line (360 twips), justified, black,
# 0 before / 0 after. No first-line indent.
BODY = dict(font="Times New Roman", sz_pt=12, line_twips=360, line_rule="auto",
            before_twips=0, after_twips=0, jc="both", color="000000")

styles = []

# docDefaults — sets the inherited baseline for ALL paragraphs.
doc_defaults = ('<w:docDefaults>'
                '<w:rPrDefault><w:rPr>'
                '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"'
                ' w:eastAsia="Times New Roman" w:cs="Times New Roman"/>'
                '<w:color w:val="000000"/>'
                f'<w:sz w:val="{HALF(12)}"/><w:szCs w:val="{HALF(12)}"/>'
                '<w:lang w:val="en-AU" w:eastAsia="en-US" w:bidi="ar-SA"/>'
                '</w:rPr></w:rPrDefault>'
                '<w:pPrDefault><w:pPr>'
                f'<w:spacing w:line="360" w:lineRule="auto" w:before="0" w:after="0"/>'
                '<w:jc w:val="both"/>'
                '</w:pPr></w:pPrDefault>'
                '</w:docDefaults>')

# Built-in defaults required by Word.
styles.append('<w:style w:type="paragraph" w:default="1" w:styleId="Normal">'
              '<w:name w:val="Normal"/>'
              '<w:qFormat/>'
              '</w:style>')
styles.append('<w:style w:type="character" w:default="1" w:styleId="DefaultParagraphFont">'
              '<w:name w:val="Default Paragraph Font"/>'
              '<w:uiPriority w:val="1"/>'
              '<w:semiHidden/><w:unhideWhenUsed/>'
              '</w:style>')
styles.append('<w:style w:type="table" w:default="1" w:styleId="TableNormal">'
              '<w:name w:val="Normal Table"/>'
              '<w:uiPriority w:val="99"/>'
              '<w:semiHidden/><w:unhideWhenUsed/>'
              '<w:tblPr>'
              '<w:tblInd w:w="0" w:type="dxa"/>'
              '<w:tblCellMar>'
              '<w:top w:w="0" w:type="dxa"/>'
              '<w:left w:w="108" w:type="dxa"/>'
              '<w:bottom w:w="0" w:type="dxa"/>'
              '<w:right w:w="108" w:type="dxa"/>'
              '</w:tblCellMar>'
              '</w:tblPr>'
              '</w:style>')
styles.append('<w:style w:type="numbering" w:default="1" w:styleId="NoList">'
              '<w:name w:val="No List"/>'
              '<w:uiPriority w:val="99"/>'
              '<w:semiHidden/><w:unhideWhenUsed/>'
              '</w:style>')

# Body styles — Body Text and First Paragraph are what pandoc emits for
# plain prose paragraphs. They mirror Normal (which already has docDefaults).
styles.append(style_para("BodyText", "Body Text", based_on="Normal", **BODY))
styles.append(style_para("FirstParagraph", "First Paragraph",
                         based_on="BodyText", **BODY))
styles.append(style_para("Compact", "Compact", based_on="BodyText",
                         **{**BODY, "after_twips": 0, "line_twips": 240}))

# Headings
styles.append(style_para("Heading1", "heading 1", based_on="Normal",
                         font="Times New Roman", sz_pt=14, bold=True,
                         line_twips=360, line_rule="auto",
                         before_twips=PT(12), after_twips=PT(12),
                         jc=None, next_style="BodyText", link="Heading1Char"))
styles.append(style_para("Heading2", "heading 2", based_on="Normal",
                         font="Times New Roman", sz_pt=12, bold=True,
                         line_twips=360, line_rule="auto",
                         before_twips=PT(6), after_twips=PT(6),
                         jc=None, next_style="BodyText", link="Heading2Char"))
styles.append(style_para("Heading3", "heading 3", based_on="Normal",
                         font="Times New Roman", sz_pt=12, bold=True, italic=True,
                         line_twips=360, line_rule="auto",
                         before_twips=PT(6), after_twips=0,
                         jc=None, next_style="BodyText", link="Heading3Char"))
for n in range(4, 10):
    styles.append(style_para(f"Heading{n}", f"heading {n}", based_on="Normal",
                             font="Times New Roman", sz_pt=12, italic=True,
                             line_twips=360, line_rule="auto",
                             before_twips=PT(6), after_twips=0,
                             jc=None, next_style="BodyText",
                             link=f"Heading{n}Char"))

# Character "Char" companions for headings (Word convention; some tools
# expect them).
styles.append(style_char("Heading1Char", "Heading 1 Char",
                         font="Times New Roman", sz_pt=14, bold=True))
styles.append(style_char("Heading2Char", "Heading 2 Char",
                         font="Times New Roman", sz_pt=12, bold=True))
styles.append(style_char("Heading3Char", "Heading 3 Char",
                         font="Times New Roman", sz_pt=12, bold=True, italic=True))
for n in range(4, 10):
    styles.append(style_char(f"Heading{n}Char", f"Heading {n} Char",
                             font="Times New Roman", sz_pt=12, italic=True))

# Title block
styles.append(style_para("Title", "Title", based_on="Normal",
                         font="Times New Roman", sz_pt=16, bold=True,
                         line_twips=360, line_rule="auto",
                         before_twips=0, after_twips=PT(12),
                         jc="center", next_style="Author"))
styles.append(style_para("Subtitle", "Subtitle", based_on="Normal",
                         font="Times New Roman", sz_pt=13, italic=True,
                         line_twips=360, line_rule="auto",
                         before_twips=0, after_twips=PT(6), jc="center",
                         next_style="Author"))
styles.append(style_para("Author", "Author", based_on="Normal",
                         font="Times New Roman", sz_pt=12,
                         line_twips=360, line_rule="auto",
                         before_twips=0, after_twips=PT(6), jc="center",
                         next_style="BodyText"))
styles.append(style_para("Date", "Date", based_on="Normal",
                         font="Times New Roman", sz_pt=12,
                         line_twips=360, line_rule="auto",
                         before_twips=0, after_twips=PT(6), jc="center",
                         next_style="BodyText"))
styles.append(style_para("Abstract", "Abstract", based_on="Normal",
                         font="Times New Roman", sz_pt=11,
                         line_twips=360, line_rule="auto",
                         before_twips=0, after_twips=PT(6), jc="both",
                         next_style="BodyText"))
styles.append(style_para("AbstractTitle", "Abstract Title", based_on="Heading2",
                         font="Times New Roman", sz_pt=12, bold=True,
                         line_twips=360, line_rule="auto",
                         before_twips=PT(6), after_twips=PT(6),
                         jc="center", next_style="Abstract"))

# Captions
styles.append(style_para("Caption", "caption", based_on="Normal",
                         font="Times New Roman", sz_pt=12,
                         line_twips=360, line_rule="auto",
                         before_twips=PT(6), after_twips=PT(6), jc="center",
                         next_style="BodyText"))
styles.append(style_para("ImageCaption", "Image Caption", based_on="Caption",
                         font="Times New Roman", sz_pt=12,
                         line_twips=360, line_rule="auto",
                         before_twips=PT(6), after_twips=PT(6), jc="center",
                         next_style="BodyText"))
styles.append(style_para("TableCaption", "Table Caption", based_on="Caption",
                         font="Times New Roman", sz_pt=12,
                         line_twips=360, line_rule="auto",
                         before_twips=PT(6), after_twips=PT(6), jc="center",
                         next_style="BodyText"))

# Table Notes — custom style applied by div-to-env.lua to .tblnotes divs.
# 10pt, single line, justified, black, no after-spacing.
styles.append(style_para("TableNotes", "Table Notes", based_on="Normal",
                         font="Times New Roman", sz_pt=10,
                         line_twips=240, line_rule="auto",
                         before_twips=0, after_twips=0, jc="both",
                         next_style="BodyText"))

# Block quotes
styles.append(style_para("BlockText", "Block Text", based_on="Normal",
                         font="Times New Roman", sz_pt=12, italic=True,
                         line_twips=360, line_rule="auto",
                         before_twips=PT(6), after_twips=PT(6), jc="both",
                         ind='w:left="720" w:right="720"',
                         next_style="BodyText"))
styles.append(style_para("Quote", "Quote", based_on="BlockText",
                         font="Times New Roman", sz_pt=12, italic=True,
                         line_twips=360, line_rule="auto",
                         before_twips=PT(6), after_twips=PT(6), jc="both",
                         ind='w:left="720" w:right="720"',
                         next_style="BodyText"))

# Footnotes
styles.append(style_para("FootnoteText", "footnote text", based_on="Normal",
                         font="Times New Roman", sz_pt=10,
                         line_twips=240, line_rule="auto",
                         before_twips=0, after_twips=0, jc=None,
                         next_style="BodyText", link="FootnoteTextChar"))
styles.append(style_char("FootnoteTextChar", "Footnote Text Char",
                         font="Times New Roman", sz_pt=10))
styles.append('<w:style w:type="character" w:styleId="FootnoteReference">'
              '<w:name w:val="footnote reference"/>'
              '<w:basedOn w:val="DefaultParagraphFont"/>'
              '<w:uiPriority w:val="99"/>'
              '<w:rPr><w:vertAlign w:val="superscript"/></w:rPr>'
              '</w:style>')

# Bibliography — hanging indent 0.5", single spacing, 6pt after
styles.append(style_para("Bibliography", "Bibliography", based_on="Normal",
                         font="Times New Roman", sz_pt=12,
                         line_twips=240, line_rule="auto",
                         before_twips=0, after_twips=PT(6), jc=None,
                         ind='w:left="720" w:hanging="720"',
                         next_style="BodyText"))

# Source code / verbatim
styles.append(style_para("SourceCode", "Source Code", based_on="Normal",
                         font="Courier New", sz_pt=10,
                         line_twips=240, line_rule="auto",
                         before_twips=0, after_twips=0, jc=None,
                         next_style="BodyText"))
styles.append(style_char("VerbatimChar", "Verbatim Char",
                         font="Courier New", sz_pt=10))

# Lists
styles.append(style_para("ListParagraph", "List Paragraph", based_on="Normal",
                         font="Times New Roman", sz_pt=12,
                         line_twips=360, line_rule="auto",
                         before_twips=0, after_twips=0, jc="both",
                         ind='w:left="720"',
                         next_style="ListParagraph"))

# Hyperlink (pandoc emits this for links + crossref). Blue, no
# underline (the underline reads as Word default and looks busy
# next to crossrefs that are already visually distinct).
styles.append('<w:style w:type="character" w:styleId="Hyperlink">'
              '<w:name w:val="Hyperlink"/>'
              '<w:basedOn w:val="DefaultParagraphFont"/>'
              '<w:uiPriority w:val="99"/>'
              '<w:rPr>'
              '<w:color w:val="0563C1"/>'
              '</w:rPr>'
              '</w:style>')

# Pandoc applies tblStyle="Table" to every w:tbl it emits, including
# the single-cell wrapper tables it uses to keep figures and their
# captions together. If "Table" has any borders, those borders frame
# every figure as a box. So this style is intentionally borderless;
# data tables that need visible borders (kable, modelsummary) should
# use flextable, which emits its own cell-level borders inline.
styles.append('<w:style w:type="table" w:styleId="Table">'
              '<w:name w:val="Table"/>'
              '<w:basedOn w:val="TableNormal"/>'
              '<w:tblPr/>'
              '</w:style>')

styles_xml = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
              '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
              + doc_defaults
              + ''.join(styles)
              + '</w:styles>')

# ---------------------------------------------------------------------------
# Other parts
# ---------------------------------------------------------------------------

CONTENT_TYPES = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                 '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                 '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                 '<Default Extension="xml" ContentType="application/xml"/>'
                 '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                 '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
                 '<Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>'
                 '<Override PartName="/word/fontTable.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.fontTable+xml"/>'
                 '</Types>')

ROOT_RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
             '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
             '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
             '</Relationships>')

DOC_RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>'
            '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/fontTable" Target="fontTable.xml"/>'
            '</Relationships>')

# Body: empty paragraph + sectPr with A4 page size and 1" margins
A4_W = 11906   # twips
A4_H = 16838
MARGIN = 1440  # 1 inch
DOCUMENT_XML = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                '<w:body>'
                '<w:p/>'
                '<w:sectPr>'
                f'<w:pgSz w:w="{A4_W}" w:h="{A4_H}"/>'
                f'<w:pgMar w:top="{MARGIN}" w:right="{MARGIN}" w:bottom="{MARGIN}"'
                f' w:left="{MARGIN}" w:header="720" w:footer="720" w:gutter="0"/>'
                '<w:cols w:space="720"/>'
                '<w:docGrid w:linePitch="360"/>'
                '</w:sectPr>'
                '</w:body>'
                '</w:document>')

SETTINGS_XML = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                '<w:zoom w:percent="100"/>'
                '<w:defaultTabStop w:val="720"/>'
                '<w:characterSpacingControl w:val="doNotCompress"/>'
                '<w:compat>'
                '<w:compatSetting w:name="compatibilityMode"'
                ' w:uri="http://schemas.microsoft.com/office/word"'
                ' w:val="15"/>'
                '</w:compat>'
                '</w:settings>')

FONT_TABLE_XML = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                  '<w:fonts xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                  '<w:font w:name="Times New Roman">'
                  '<w:panose1 w:val="02020603050405020304"/>'
                  '<w:charset w:val="00"/>'
                  '<w:family w:val="roman"/>'
                  '<w:pitch w:val="variable"/>'
                  '</w:font>'
                  '<w:font w:name="Courier New">'
                  '<w:panose1 w:val="02070309020205020404"/>'
                  '<w:charset w:val="00"/>'
                  '<w:family w:val="modern"/>'
                  '<w:pitch w:val="fixed"/>'
                  '</w:font>'
                  '</w:fonts>')

# ---------------------------------------------------------------------------
# Write the zip
# ---------------------------------------------------------------------------

OUT.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("[Content_Types].xml", CONTENT_TYPES)
    z.writestr("_rels/.rels", ROOT_RELS)
    z.writestr("word/_rels/document.xml.rels", DOC_RELS)
    z.writestr("word/document.xml", DOCUMENT_XML)
    z.writestr("word/styles.xml", styles_xml)
    z.writestr("word/settings.xml", SETTINGS_XML)
    z.writestr("word/fontTable.xml", FONT_TABLE_XML)

print(f"Wrote {OUT}  ({OUT.stat().st_size:,} bytes)")
