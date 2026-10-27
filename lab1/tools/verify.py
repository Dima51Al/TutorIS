#!/usr/bin/env python3
"""Check the document package; this does not test a deployed information system."""
from pathlib import Path
import ast
import csv
import importlib.util
import json
import math
import re
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parent
checks=[]
def require(ok,message):
 if not ok: raise AssertionError(message)
 checks.append(message)

report=(ROOT/'report.md').read_text()
expected_pages=report.count('<!-- pagebreak -->')+1
require(12 <= expected_pages <= 20,'Markdown length is within 12–20 pages')
for p in REPO.rglob('*.md'):
 if '.git' in p.parts or 'qa' in p.parts: continue
 for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',p.read_text()):
  if target.startswith(('https://','http://','#')): continue
  require((p.parent/target.split('#')[0]).exists(),f'Local link: {p.relative_to(REPO)} -> {target}')
for code in [*[f'F{i:02}' for i in range(1,15)],*[f'N{i:02}' for i in range(1,9)],*[f'Q{i}' for i in range(1,8)],*[f'R{i}' for i in range(1,11)]]:
 require(code in report,f'Report contains {code}')
for p in ROOT.rglob('*.py'):ast.parse(p.read_text());checks.append(f'Python syntax: {p.relative_to(ROOT)}')
spec=importlib.util.spec_from_file_location('lab_calculations',ROOT/'calculations/calculate.py')
calc=importlib.util.module_from_spec(spec);spec.loader.exec_module(calc)
scores=calc.weighted(calc.WEIGHTS)
require(scores=={'A':3.22,'B':3.72,'C':3.6},'Weighted scores recomputed independently of results.json')
require(all(x['winner']=='B' for x in calc.sensitivity().values()),'B leads in all three one-factor weight cases')
case=calc.business_case(180000,297600,calc.effects()['annual'])
require(case['tco_3y']==1072800 and case['net_3y']==412200,'TCO and net effect agree with cost and ramp assumptions')
require(math.isclose(case['roi_percent'],38.422818791946305),'ROI = 38.4228%')
require(math.isclose(case['ramp_payback_months'],15.594059405940595),'Payback with ramp = 15.5941 months')
require(calc.business_case(180000,297600,calc.effects(3,600,.3,.1)['annual'])['ramp_payback_months'] is None,'Pessimistic case does not pay back within 36 months')
stored=json.loads((ROOT/'calculations/results.json').read_text())
require(stored['scores']==scores,'Stored scores match current inputs')
for k,v in case.items():require(stored['cases']['B'][k]==v,f'Stored case B matches recomputation: {k}')
with (ROOT/'calculations/cashflow_b.csv').open() as f: rows=list(csv.DictReader(f))
require(len(rows)==36 and float(rows[-1]['cumulative_after_investment_rub'])==412200,'36-month CSV ends at 412200 rubles')
B='{http://www.omg.org/spec/BPMN/20100524/MODEL}'
D='{http://www.omg.org/spec/BPMN/20100524/DI}'
for p in sorted((ROOT/'diagrams').glob('*.bpmn')):
 tree=ET.parse(p);root=tree.getroot();ids=[x.get('id') for x in root.iter() if x.get('id')]
 require(len(ids)==len(set(ids)),f'{p.stem}: unique XML IDs')
 process=root.find(B+'process');nodes={x.get('id'):x for x in process if x.tag not in [B+'laneSet',B+'sequenceFlow']}
 flows=process.findall(B+'sequenceFlow');out={n:[] for n in nodes};inc={n:[] for n in nodes}
 for f in flows:
  a,b=f.get('sourceRef'),f.get('targetRef');require(a in nodes and b in nodes,f'{p.stem}: flow {f.get("id")} endpoints exist')
  out[a].append(b);inc[b].append(a)
 starts=[n for n,x in nodes.items() if x.tag==B+'startEvent'];ends=[n for n,x in nodes.items() if x.tag==B+'endEvent']
 require(len(starts)==1 and len(ends)>=1,f'{p.stem}: start and end events present')
 reachable=set();todo=starts[:]
 while todo:
  n=todo.pop()
  if n not in reachable:reachable.add(n);todo.extend(out[n])
 require(reachable==set(nodes),f'{p.stem}: every flow node reachable')
 require(all(not inc[n] for n in starts) and all(not out[n] for n in ends),f'{p.stem}: start/end direction constraints')
 lane_refs=[x.text for x in process.iter(B+'flowNodeRef')]
 require(sorted(lane_refs)==sorted(nodes),f'{p.stem}: every node assigned to exactly one lane')
 for n,x in nodes.items():
  if x.tag==B+'exclusiveGateway':
   branches=[f for f in flows if f.get('sourceRef')==n]
   require(len(branches)>=2 and all(f.get('name') for f in branches),f'{p.stem}: exclusive gateway {n} has labelled alternatives')
 for x in root.iter():
  for key in ['bpmnElement','sourceRef','targetRef','processRef']:
   if x.get(key): require(x.get(key) in ids,f'{p.stem}: {key} reference resolves')
 mx=ET.parse(p.with_suffix('.drawio'));svg=ET.parse(p.with_suffix('.svg'))
 require(mx.getroot().tag=='mxfile' and svg.getroot().tag.endswith('svg'),f'{p.stem}: draw.io and SVG parse')
 require(p.with_suffix('.pdf').stat().st_size>10000,f'{p.stem}: PDF is non-empty')
try:
 from pypdf import PdfReader
except ImportError:
 print('Optional PDF inspection skipped: install pypdf or use bundled workspace Python.')
else:
 pdf=PdfReader(ROOT/'report.pdf');require(len(pdf.pages)==expected_pages,f'Final report PDF has {expected_pages} pages')
 for i,page in enumerate(pdf.pages): require(len(page.extract_text() or '')>300,f'PDF page {i+1}: text extractable')
 for p in (ROOT/'diagrams').glob('*.pdf'):require(len(PdfReader(p).pages)==1,f'{p.name}: one-page diagram PDF')
print(f'PASS: {len(checks)} package checks. No SaaS or user acceptance tests were executed.')
