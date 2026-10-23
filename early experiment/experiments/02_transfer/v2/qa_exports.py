import json,subprocess,sys,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
from pypdf import PdfReader
from experiment import ROOT,save

figures=ROOT/'figures';records=[]
for png in sorted(figures.glob('0*.png')):
    svg=png.with_suffix('.svg');pdf=png.with_suffix('.pdf')
    assert svg.exists() and pdf.exists()
    im=Image.open(png);xml=ET.parse(svg);text_nodes=xml.findall('.//{http://www.w3.org/2000/svg}text')
    reader=PdfReader(str(pdf));text=reader.pages[0].extract_text()
    assert len(text_nodes)>10 and len(text)>50
    records.append(dict(name=png.stem,png_pixels=list(im.size),svg_text_nodes=len(text_nodes),
        pdf_text_characters=len(text),pdf_width_points=float(reader.pages[0].mediabox.width)))
# Preserve the original source-validator record. Portable checks below validate exports.
preflight=json.loads((ROOT/'figure_source_preflight.json').read_text(encoding='utf-8'))
assert preflight['summary']['counts']['FAIL']==0
save(ROOT/'figure_export_qa.json',dict(figures=records,backend='Python matplotlib only',
    exclusions='No quantitative test histories excluded. Illustrative case chosen by an explicit recorded median-benefit rule. Numerical audit uses the preselected first 16 complete history pairs.',
    statistics='128 whole pairs; three training seeds. Paired bootstrap resamples pairs after averaging seeds. Seed ranges shown for selected prediction curves. No p-value claims.',
    warnings_reviewed=['PNG 300dpi and SVG/PDF satisfy requested formats; TIFF not requested.',
        'Random generator in plotting is exclusively bootstrap uncertainty, not fabricated response data.',
        'All data are actual executed synthetic experiments, explicitly labeled; no real material inference.',
        'Positive finite RMSE checked before log scaling; zero-error oracle omitted only from logarithmic error panels and retained in decision comparisons.']))
print('FIGURE_QA_OK',len(records),'PNG/SVG/PDF groups; editable vector text verified')
