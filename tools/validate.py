"""Check source text preservation and local asset references. Requires markdown."""
from pathlib import Path
from bs4 import BeautifulSoup
from collections import Counter
import copy, difflib, json, re, sys
import markdown

root=Path(__file__).resolve().parents[1]
source=BeautifulSoup(Path(sys.argv[1]).read_text(encoding='utf-8'),'html.parser')
for official in source.select('.top a[href]'):
    paragraph=source.new_tag('p')
    paragraph.append(copy.deepcopy(official))
    source.select_one('.hero').append(paragraph)
units=[('README.md',source.select_one('.hero'))]+[(f'section-{i:02d}.md',c) for i,c in enumerate(source.select('main > section.chapter'),1)]
normal=lambda s:re.sub(r'\s+','',s)
results=[]
for filename,original in units:
    text=(root/'docs'/filename).read_text(encoding='utf-8')
    # Only GitBook-specific wrapper syntax is removed for text comparison.
    text=re.sub(r'\{% (?:hint[^%]*|endhint) %\}','',text)
    text=re.sub(r' \{#[^}]+\}', '', text)
    html=markdown.markdown(text,extensions=['tables','sane_lists'])
    rendered=BeautifulSoup(html,'html.parser')
    before=normal(original.get_text())
    after=normal(rendered.get_text())
    if before!=after:
        diff=list(difflib.SequenceMatcher(None,before,after,autojunk=False).get_opcodes())
        issues=[{'op':op,'source':before[a:b][:150],'output':after[c:d][:150]} for op,a,b,c,d in diff if op!='equal']
        print(filename, json.dumps(issues[:20],ensure_ascii=False))
        raise AssertionError('Text differs: '+filename)
    for im in rendered.select('img'):
        assert (root/'docs'/im['src']).is_file(), im['src']
    original_links=Counter(a.get('href') for a in original.select('a[href]'))
    output_links=Counter(a.get('href') for a in rendered.select('a[href]'))
    assert original_links==output_links,filename
    assert len(original.select('img'))==len(rendered.select('img')),filename
    results.append({'file':filename,'source_text_matches':True,'images_resolve':True,'links_preserved':True})
(root/'validation-report.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS: all 17 pages preserve source text, image occurrences, and links.')
