#!/usr/bin/env python3
"""Render report.md to a black-and-white reading copy; reportlab + pypdfium2 required."""
from pathlib import Path
import re
from html import escape
import pypdfium2 as pdfium
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepInFrame
from reportlab.lib.pagesizes import A4

ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/'qa';QA.mkdir(exist_ok=True)
FONT=Path('/System/Library/Fonts/Supplemental')
for name,file in [('Arial','Arial.ttf'),('Arial-Bold','Arial Bold.ttf'),('Arial-Italic','Arial Italic.ttf')]:
 pdfmetrics.registerFont(TTFont(name,str(FONT/file)))
pdfmetrics.registerFontFamily('Arial',normal='Arial',bold='Arial-Bold',italic='Arial-Italic',boldItalic='Arial-Bold')
styles={
 'body':ParagraphStyle('body',fontName='Arial',fontSize=10.2,leading=13.6,spaceAfter=7,textColor=colors.black,splitLongWords=True),
 'h1':ParagraphStyle('h1',fontName='Arial-Bold',fontSize=17,leading=21,spaceAfter=12,textColor=colors.black),
 'h2':ParagraphStyle('h2',fontName='Arial-Bold',fontSize=13,leading=16,spaceAfter=9,spaceBefore=5,textColor=colors.black),
 'h3':ParagraphStyle('h3',fontName='Arial-Bold',fontSize=11,leading=14,spaceAfter=7,spaceBefore=4),
 'cell':ParagraphStyle('cell',fontName='Arial',fontSize=8.6,leading=11.0,spaceAfter=0,splitLongWords=True),
 'head':ParagraphStyle('head',fontName='Arial-Bold',fontSize=8.6,leading=11.0,textColor=colors.black,spaceAfter=0,splitLongWords=True),
}

def inline(t):
 t=t.replace('<br>','\n')
 links=[]
 def link(m):
  href=m.group(2)
  if not href.startswith(('http://','https://')):href=str((ROOT/href).resolve())
  links.append((m.group(1),href));return f'@@LINK{len(links)-1}@@'
 t=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',link,t)
 t=escape(t)
 t=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',t)
 t=re.sub(r'`([^`]+)`',r'<font color="#000000">\1</font>',t)
 for i,(label,href) in enumerate(links):
  t=t.replace(f'@@LINK{i}@@',f'<link href="{escape(href,quote=True)}" color="#000000">{escape(label)}</link>')
 return t.replace('\n','<br/>')

def diagram_png(stem):
 pdf=pdfium.PdfDocument(str(ROOT/'diagrams'/(stem+'.pdf')))
 page=pdf[0];image=page.render(scale=2.0).to_pil();out=QA/(stem+'.png');image.save(out);page.close();pdf.close();return out
images={x:diagram_png(x) for x in ['01-intake','02-lesson']}

def parse(chunk,width):
 lines=chunk.strip().splitlines();flow=[];i=0
 while i<len(lines):
  s=lines[i].strip()
  if not s:i+=1;continue
  if s.startswith('!['):
   m=re.search(r'\(([^)]+)\)',s);stem=Path(m.group(1)).stem
   img=Image(str(images[stem]));scale=min(width/img.imageWidth,300/img.imageHeight)
   img.drawWidth=img.imageWidth*scale;img.drawHeight=img.imageHeight*scale
   flow.extend([img,Spacer(1,8)]);i+=1;continue
  if s.startswith('|'):
   rows=[]
   while i<len(lines) and lines[i].strip().startswith('|'):
    r=[x.strip() for x in lines[i].strip().strip('|').split('|')]
    if not all(re.fullmatch(r'[:\- ]+',x or '-') for x in r):rows.append(r)
    i+=1
   n=len(rows[0]);weights=[]
   for col in range(n):
    mx=max(len(re.sub(r'\[[^\]]+\]\([^)]+\)','source',r[col])) for r in rows)
    weights.append(max(6,min(mx,65))**.7)
   # numeric columns stay compact, prose columns receive the remaining width
   total=sum(weights);widths=[width*w/total for w in weights]
   cells=[[Paragraph(inline(c),styles['head' if j==0 else 'cell']) for c in row] for j,row in enumerate(rows)]
   table=Table(cells,colWidths=widths,hAlign='LEFT',repeatRows=1)
   table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E8E8E8')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#F7F7F7'),colors.white]),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#AAAAAA')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
   flow.extend([table,Spacer(1,9)]);continue
  if s.startswith('#'):
   level=len(s)-len(s.lstrip('#'));flow.append(Paragraph(inline(s.lstrip('#').strip()),styles['h1' if level==1 else 'h2' if level==2 else 'h3']));i+=1;continue
  if re.match(r'^(\d+\. |[-*] )',s):
   flow.append(Paragraph(inline(s),styles['body']));i+=1;continue
  parts=[s];i+=1
  while i<len(lines) and lines[i].strip() and not re.match(r'^(#|\||!\[|\d+\. |[-*] )',lines[i].strip()):
   parts.append(lines[i].strip());i+=1
  flow.append(Paragraph(inline(' '.join(parts)),styles['body']))
 return flow

width=A4[0]-86;height=A4[1]-92
chunks=(ROOT/'report.md').read_text().split('<!-- pagebreak -->')
page_count=len(chunks)
assert 12 <= page_count <= 20,page_count
scales=[]
class Tracked(KeepInFrame):
 def wrap(self,aW,aH):
  result=super().wrap(aW,aH)
  scales.append(getattr(self,'_scale',1))
  return result
story=[]
for index,chunk in enumerate(chunks):
 if index:story.append(PageBreak())
 story.append(Tracked(width,height,parse(chunk,width),mode='shrink',hAlign='LEFT',vAlign='TOP'))
def footer(canvas,doc):
 canvas.saveState();canvas.setStrokeColor(colors.HexColor('#BBBBBB'));canvas.line(43,38,A4[0]-43,38)
 canvas.setFont('Arial',8);canvas.setFillColor(colors.HexColor('#555555'))
 canvas.drawString(43,25,'TutorIS · Концепция ИС · 27.10.2026')
 canvas.drawRightString(A4[0]-43,25,f'{doc.page} / {page_count}');canvas.restoreState()
doc=SimpleDocTemplate(str(ROOT/'report.pdf'),pagesize=A4,leftMargin=43,rightMargin=43,topMargin=43,bottomMargin=49,title='TutorIS — Концепция информационной системы',author='Команда TutorIS',pageCompression=1)
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print('Report rendered. Page scales:',[round(x,3) for x in scales])
# Render every final page to inspect layout.
pdf=pdfium.PdfDocument(str(ROOT/'report.pdf'))
print('Pages:',len(pdf))
for i in range(len(pdf)):
 page=pdf[i];page.render(scale=1.3).to_pil().save(QA/f'report-{i+1:02}.png');page.close()
pdf.close()
