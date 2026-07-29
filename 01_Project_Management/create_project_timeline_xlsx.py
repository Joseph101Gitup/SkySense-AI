from pathlib import Path
import zipfile
from xml.sax.saxutils import escape

out = Path(r'd:\personal\SkySense_AI\01_Project_Management\Project_Timeline.xlsx')

rows = [
    ['Task', 'Start Date', 'End Date', 'Status', 'Owner', 'Notes'],
    ['Project kickoff', '2026-07-24', '2026-07-31', 'Planned', 'Project Lead', 'Finalize scope and team roles'],
    ['Research and requirements', '2026-07-31', '2026-08-14', 'Planned', 'Research Lead', 'Collect requirements and define technical approach'],
    ['Prototype design', '2026-08-14', '2026-09-01', 'Planned', 'Architecture Lead', 'Complete design for AI model, simulator, and backend'],
    ['Model training baseline', '2026-09-01', '2026-10-15', 'Planned', 'AI Lead', 'Train initial baseline model and evaluate performance'],
    ['Integration sprint', '2026-10-15', '2026-11-01', 'Planned', 'Backend Lead', 'Integrate simulator, backend, and data flow'],
    ['App and hardware demo', '2026-11-01', '2026-11-30', 'Planned', 'Android/RPi Leads', 'Prepare end-to-end demo for validation'],
    ['Testing and documentation', '2026-11-30', '2026-12-15', 'Planned', 'QA Lead', 'Validate system and finalize documentation'],
    ['Final presentation', '2026-12-15', '2026-12-31', 'Planned', 'Project Team', 'Prepare thesis and final showcase'],
]

shared_strings = []

def add_string(value: str):
    if value not in shared_strings:
        shared_strings.append(value)
    return shared_strings.index(value)

sheet_rows = []
for row_index, row in enumerate(rows, start=1):
    cells = []
    for col_index, value in enumerate(row, start=1):
        if isinstance(value, str):
            idx = add_string(value)
            cells.append(f'<c r="{chr(65 + (col_index - 1))}{row_index}" t="s"><v>{idx}</v></c>')
        else:
            cells.append(f'<c r="{chr(65 + (col_index - 1))}{row_index}"><v>{value}</v></c>')
    sheet_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')

shared_strings_xml = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="{count}" uniqueCount="{count}">{items}</sst>'
).format(
    count=len(shared_strings),
    items=''.join(f'<si><t>{escape(s)}</t></si>' for s in shared_strings),
)

sheet_xml = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
    '<sheetData>{rows}</sheetData></worksheet>'
).format(rows=''.join(sheet_rows))

content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/><Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/><Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/><Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/></Types>'''

rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/></Relationships>'''

workbook_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/></Relationships>'''

workbook = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Project Timeline" sheetId="1" r:id="rId1"/></sheets></workbook>'''

styles = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts><fills count="1"><fill><patternFill patternType="none"/></fill></fills><borders count="1"><border/></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>'''

app = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"><Application>Microsoft Excel</Application></Properties>'''

core = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>Project Timeline</dc:title><dc:creator>GitHub Copilot</dc:creator><cp:lastModifiedBy>GitHub Copilot</cp:lastModifiedBy></cp:coreProperties>'''

with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.writestr('[Content_Types].xml', content_types)
    zf.writestr('_rels/.rels', rels)
    zf.writestr('docProps/app.xml', app)
    zf.writestr('docProps/core.xml', core)
    zf.writestr('xl/workbook.xml', workbook)
    zf.writestr('xl/_rels/workbook.xml.rels', workbook_rels)
    zf.writestr('xl/styles.xml', styles)
    zf.writestr('xl/sharedStrings.xml', shared_strings_xml)
    zf.writestr('xl/worksheets/sheet1.xml', sheet_xml)

print(out)
print(out.exists(), out.stat().st_size)
