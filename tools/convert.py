"""Convert the supplied BIOBUZZ HTML without translating or rewriting its text.
Usage: python tools/convert.py path/to/source.html
Requires: beautifulsoup4, Pillow (for downloaded-image validation).
"""
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Comment
from urllib.request import urlopen, Request
from urllib.parse import urlsplit, unquote
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
import base64, copy, hashlib, io, json, re, sys

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
ASSETS = DOCS / 'assets'
ASSETS.mkdir(parents=True, exist_ok=True)
source = Path(sys.argv[1])
soup = BeautifulSoup(source.read_text(encoding='utf-8'), 'html.parser')
for official in soup.select('.top a[href]'):
    paragraph=soup.new_tag('p')
    paragraph.append(copy.deepcopy(official))
    soup.select_one('.hero').append(paragraph)
chapters = soup.select('main > section.chapter')
assert len(chapters) == 16
units = [('README.md', soup.select_one('.hero'))] + [(f'section-{i:02d}.md', c) for i, c in enumerate(chapters, 1)]
ids = {}
for filename, node in units:
    for el in [node] + list(node.select('[id]')):
        if el.get('id'):
            ids[el['id']] = filename

image_sources = list(dict.fromkeys(im['src'] for im in soup.select('main img')))
def download(item):
    i, src = item
    ext = '.png' if src.startswith('data:') else (Path(unquote(urlsplit(src).path)).suffix.lower() or '.png')
    name = f'image-{i:03d}{ext}'
    cached = ASSETS / name
    if cached.exists():
        data = cached.read_bytes()
        Image.open(io.BytesIO(data)).verify()
        return src, {'path': 'assets/' + name, 'bytes':len(data), 'sha256':hashlib.sha256(data).hexdigest()}
    if src.startswith('data:'):
        data = base64.b64decode(src.split(',', 1)[1])
        ext = '.png'
    else:
        ext = Path(unquote(urlsplit(src).path)).suffix.lower() or '.png'
        data = urlopen(Request(src, headers={'User-Agent':'Mozilla/5.0'}), timeout=30).read()
    Image.open(io.BytesIO(data)).verify()
    name = f'image-{i:03d}{ext}'
    (ASSETS / name).write_bytes(data)
    return src, {'path': 'assets/' + name, 'bytes':len(data), 'sha256':hashlib.sha256(data).hexdigest()}
with ThreadPoolExecutor(max_workers=8) as pool:
    assets = dict(pool.map(download, enumerate(image_sources, 1)))

def esc(text):
    text=text.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
    return re.sub(r'([\\`*_\[\]])', r'\\\1', text)

def clean_html(node, filename):
    n = copy.deepcopy(node)
    for e in [n] + list(n.find_all(True)):
        if e.name == 'colgroup':
            e.decompose()
            continue
        if e.attrs is None:
            continue
        e.attrs = {k:v for k,v in e.attrs.items() if k in ('colspan','rowspan','href','src','alt','id')}
        if e.name == 'img':
            e['src'] = assets[e['src']]['path']
        if e.name == 'a':
            e['href'] = link(e.get('href',''), filename)
    # GitBook does not support rectangular (2x2) merges. These two source
    # cells are first-column headers; retain colspan and split the vertical
    # extent into a populated first row and empty continuation row.
    for cell in list(n.select('[rowspan][colspan]')):
        if int(cell['rowspan']) > 1 and int(cell['colspan']) > 1:
            assert cell is cell.parent.find(['th','td'])
            rows = cell.parent.parent.find_all('tr', recursive=False)
            index = rows.index(cell.parent)
            for offset in range(1, int(cell['rowspan'])):
                blank = BeautifulSoup('<th></th>', 'html.parser').th
                blank['colspan'] = cell['colspan']
                rows[index + offset].insert(0, blank)
            del cell['rowspan']
    return str(n)

def link(href, filename):
    if href.startswith('#'):
        anchor = unquote(href[1:])
        if anchor not in ids:
            raise ValueError('Unresolved anchor: ' + href)
        return ('' if ids[anchor] == filename else ids[anchor]) + '#' + anchor
    return href

def render(node, filename):
    if isinstance(node, Comment):
        return ''
    if isinstance(node, NavigableString):
        return esc(str(node))
    t = node.name
    cls = node.get('class', [])
    children = lambda: ''.join(render(x, filename) for x in node.children)
    if t in ('script','style'):
        return ''
    if t == 'table':
        return '\n\n' + clean_html(node, filename) + '\n\n'
    if t == 'img':
        return '![' + esc(node.get('alt','')) + '](' + assets[node['src']]['path'] + ')'
    if t == 'a':
        return '[' + children() + '](<' + link(node.get('href',''), filename) + '>)'
    if re.fullmatch('h[1-6]', t):
        level = max(1, int(t[1])-1)
        anchor = node.get('id')
        if t == 'h2' and 'chapter' in node.parent.get('class',[]):
            anchor = node.parent.get('id')
        return '\n\n' + '#' * level + ' ' + children().strip() + (f' {{#{anchor}}}' if anchor else '') + '\n\n'
    if t in ('b','strong'):
        return '**' + children() + '**'
    if t in ('i','em'):
        return '*' + children() + '*'
    if t == 'br':
        return '<br>\n'
    if t == 'hr':
        return '\n\n---\n\n'
    if t in ('sup','sub'):
        return '<' + t + '>' + children() + '</' + t + '>'
    if t == 'code':
        return '`' + node.get_text() + '`'
    if t == 'ul' or t == 'ol':
        out=[]
        for i, li in enumerate(node.find_all('li',recursive=False), int(node.get('start',1))):
            text=render(li,filename).strip()
            prefix = '- ' if t == 'ul' else f'{i}. '
            out.append(prefix + text.replace('\n','\n' + ' '*len(prefix)))
        return '\n\n' + '\n'.join(out) + '\n\n'
    if 'rule-block' in cls:
        number=node.select_one('.rule-no')
        content=node.select_one('.rule-content')
        title=content.select_one('.rule-title')
        anchor=node.get('id', 'rule-' + number.get_text(strip=True))
        body=''.join(render(x,filename) for x in content.children if x is not title)
        # Use a single callout per rule. Nested hints are replaced with
        # blockquotes so explanatory notes remain distinct inside the box.
        def quote_note(match):
            return '\n\n' + '\n'.join('> ' + line for line in match.group(1).strip().splitlines()) + '\n\n'
        body=re.sub(r'\{% hint[^%]*%\}(.*?)\{% endhint %\}', quote_note, body, flags=re.S)
        heading='#### ' + render(number,filename).strip() + ' ' + render(title,filename).strip() + f' {{#{anchor}}}'
        return '\n\n{% hint style="success" %}\n' + heading + '\n\n' + body.strip() + '\n{% endhint %}\n\n'
    if 'alpha' in cls or 'roman' in cls:
        return '\n\n' + ' '.join(render(x,filename).strip() for x in node.children if str(x).strip()) + '\n\n'
    if any(c in cls for c in ('note-box','callout','notice')):
        return '\n\n{% hint style="info" %}\n' + children().strip() + '\n{% endhint %}\n\n'
    if 'quote' in cls or t == 'blockquote':
        return '\n\n' + '\n'.join('> ' + line for line in children().strip().splitlines()) + '\n\n'
    if 'caption' in cls:
        return '\n\n**' + children().strip() + '**\n\n'
    if t in ('div','p','section','figure','figcaption'):
        return '\n\n' + children().strip() + '\n\n'
    return children()

stats=[]
for filename, unit in units:
    result=render(unit,filename)
    result=re.sub(r'\n[ \t]+\n','\n\n',result)
    result=re.sub(r'\n{3,}','\n\n',result).strip()+'\n'
    (DOCS / filename).write_text(result,encoding='utf-8')
    # Exact table cell sequence and span check, allowing only the documented
    # two empty continuation cells introduced for rectangular headers.
    out_tables=BeautifulSoup(result,'html.parser').find_all('table')
    orig_tables=unit.find_all('table')
    assert len(out_tables)==len(orig_tables)
    for orig, new in zip(orig_tables,out_tables):
        expected=BeautifulSoup(clean_html(orig,filename),'html.parser').table
        assert str(expected)==str(new)
        old_text=re.sub(r'\s+','',orig.get_text())
        new_text=re.sub(r'\s+','',new.get_text())
        assert old_text==new_text, filename
    stats.append({'file':filename,'tables':len(orig_tables),'images':len(unit.select('img')),'rules':len(unit.select('.rule-block'))})

summary='# Table of contents\n\n* [BIOBUZZ 한국어 매뉴얼](README.md)\n'
for i,c in enumerate(chapters,1):
    summary+=f'* [{c.h2.get_text(strip=True)}](section-{i:02d}.md)\n'
(DOCS/'SUMMARY.md').write_text(summary,encoding='utf-8')
(ROOT/'.gitbook.yaml').write_text('root: ./docs/\n\nstructure:\n  readme: README.md\n  summary: SUMMARY.md\n',encoding='utf-8')
manifest={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'pages':stats,'assets':[{'source':k if not k.startswith('data:') else 'embedded PNG','index':i,**v} for i,(k,v) in enumerate(assets.items(),1)],'rectangular_header_adjustments':2,'gitbook_live_render_verified':False}
(ROOT/'conversion-report.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'pages':len(units),'tables':sum(s['tables'] for s in stats),'image_occurrences':sum(s['images'] for s in stats),'image_files':len(assets),'rules':sum(s['rules'] for s in stats)},ensure_ascii=False))
