"""A tiny Word (.docx) writer that needs nothing but Python's standard library."""
import zipfile
from xml.sax.saxutils import escape

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
FONT = "Cambria"


def _x(s):
    return escape(str(s), {'"': "&quot;"})


class Doc:
    def __init__(self, text_width):
        self.parts = []
        self.links = []
        self.text_width = text_width

    # ---- inline
    def link_id(self, url):
        if url not in self.links:
            self.links.append(url)
        return f"rIdL{self.links.index(url) + 1}"

    def run(self, text, b=False, i=False, color=None, sz=10, caps=False, link=None):
        pr = ""
        if b:
            pr += "<w:b/><w:bCs/>"
        if i:
            pr += "<w:i/><w:iCs/>"
        if caps:
            pr += "<w:caps/>"
        if color:
            pr += f'<w:color w:val="{color}"/>'
        if sz:
            pr += f'<w:sz w:val="{int(sz * 2)}"/><w:szCs w:val="{int(sz * 2)}"/>'
        r = f'<w:r>{"<w:rPr>" + pr + "</w:rPr>" if pr else ""}<w:t xml:space="preserve">{_x(text)}</w:t></w:r>'
        if link:
            return f'<w:hyperlink r:id="{self.link_id(link)}" w:history="1">{r}</w:hyperlink>'
        return r

    @staticmethod
    def tab():
        return "<w:r><w:tab/></w:r>"

    # ---- blocks
    def para(self, runs, jc=None, before=0, after=0, right_tab=False, keep_next=False, keep_lines=False,
             border=False, left=None, hanging=None, line=None):
        pr = ""
        if keep_next:
            pr += "<w:keepNext/>"
        if keep_lines:
            pr += "<w:keepLines/>"
        if border:
            pr += '<w:pBdr><w:bottom w:val="single" w:sz="10" w:space="2" w:color="B9C6D8"/></w:pBdr>'
        if right_tab:
            pr += f'<w:tabs><w:tab w:val="right" w:pos="{self.text_width}"/></w:tabs>'
        pr += f'<w:spacing w:before="{before}" w:after="{after}"' + (f' w:line="{line}" w:lineRule="auto"' if line else "") + "/>"
        if left is not None or hanging is not None:
            pr += f'<w:ind w:left="{left or 0}"' + (f' w:hanging="{hanging}"' if hanging else "") + "/>"
        if jc:
            pr += f'<w:jc w:val="{jc}"/>'
        self.parts.append(f"<w:p><w:pPr>{pr}</w:pPr>{''.join(runs)}</w:p>")

    def table(self, rows, widths, keep_next=False):
        """rows: list of (cells, space_after); a cell is (runs, jc). No borders, so it looks like aligned text."""
        grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
        out = (f'<w:tbl><w:tblPr><w:tblW w:w="{sum(widths)}" w:type="dxa"/><w:tblLayout w:type="fixed"/>'
               '<w:tblCellMar><w:left w:w="0" w:type="dxa"/><w:right w:w="0" w:type="dxa"/></w:tblCellMar></w:tblPr>'
               f"<w:tblGrid>{grid}</w:tblGrid>")
        for ri, (cells, after) in enumerate(rows):
            out += "<w:tr><w:trPr><w:cantSplit/></w:trPr>"
            kn = "<w:keepNext/>" if (keep_next or ri < len(rows) - 1) else ""
            for k, (runs, jc) in enumerate(cells):
                jcx = f'<w:jc w:val="{jc}"/>' if jc else ""
                out += (f'<w:tc><w:tcPr><w:tcW w:w="{widths[k]}" w:type="dxa"/></w:tcPr>'
                        f'<w:p><w:pPr>{kn}<w:spacing w:before="0" w:after="{after}"/>{jcx}</w:pPr>{"".join(runs)}</w:p></w:tc>')
            out += "</w:tr>"
        out += "</w:tbl>"
        self.parts.append(out)

    # ---- file
    def save(self, path, title, author, footer_runs_before, footer_after_runs=()):
        body = "".join(self.parts)
        sect = ('<w:sectPr><w:footerReference w:type="default" r:id="rIdF1"/>'
                '<w:pgSz w:w="12240" w:h="15840"/>'
                '<w:pgMar w:top="864" w:right="1037" w:bottom="1152" w:left="1037" w:header="720" w:footer="560" w:gutter="0"/></w:sectPr>')
        document = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {W}><w:body>{body}{sect}</w:body></w:document>'
        footer = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr {W}><w:p><w:pPr><w:jc w:val="center"/></w:pPr>'
                  f'{footer_runs_before}<w:r><w:rPr><w:color w:val="5C6975"/><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:rPr><w:color w:val="5C6975"/><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
                  f'<w:r><w:rPr><w:color w:val="5C6975"/><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:rPr><w:color w:val="5C6975"/><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr><w:t>1</w:t></w:r><w:r><w:rPr><w:color w:val="5C6975"/><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr><w:fldChar w:fldCharType="end"/></w:r>'
                  f'{"".join(footer_after_runs)}</w:p></w:ftr>')
        styles = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles {W}><w:docDefaults><w:rPrDefault><w:rPr>'
                  f'<w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}" w:eastAsia="{FONT}" w:cs="{FONT}"/><w:color w:val="202124"/>'
                  '<w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:val="en-US"/></w:rPr></w:rPrDefault>'
                  '<w:pPrDefault><w:pPr><w:spacing w:after="0" w:line="252" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>'
                  '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>'
                  '<w:style w:type="character" w:styleId="Hyperlink"><w:name w:val="Hyperlink"/><w:rPr><w:color w:val="1F4E79"/></w:rPr></w:style>'
                  '</w:styles>')
        rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rIdS1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
                '<Relationship Id="rIdF1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>'
                + "".join(f'<Relationship Id="rIdL{k + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" '
                          f'Target="{_x(u)}" TargetMode="External"/>' for k, u in enumerate(self.links))
                + "</Relationships>")
        ctypes = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                  '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                  '<Default Extension="xml" ContentType="application/xml"/>'
                  '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                  '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
                  '<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>'
                  '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
                  '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
                  "</Types>")
        root = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
                '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
                '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
                "</Relationships>")
        core = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
                'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
                f"<dc:title>{_x(title)}</dc:title><dc:creator>{_x(author)}</dc:creator></cp:coreProperties>")
        app = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
               "<Application>Microsoft Office Word</Application></Properties>")
        files = [("[Content_Types].xml", ctypes), ("_rels/.rels", root), ("word/document.xml", document), ("word/styles.xml", styles),
                 ("word/footer1.xml", footer), ("word/_rels/document.xml.rels", rels), ("docProps/core.xml", core), ("docProps/app.xml", app)]
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            for name, data in files:
                zi = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))  # fixed date: identical input gives an identical file
                zi.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(zi, data)
        return document
