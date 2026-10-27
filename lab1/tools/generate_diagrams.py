#!/usr/bin/env python3
"""Build editable draw.io, BPMN 2.0 XML and SVG views of two conceptual processes."""
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree, register_namespace
from html import escape
import textwrap

ROOT=Path(__file__).resolve().parents[1]/'diagrams'
B='http://www.omg.org/spec/BPMN/20100524/MODEL'
D='http://www.omg.org/spec/BPMN/20100524/DI'
C='http://www.omg.org/spec/DD/20100524/DC'
I='http://www.omg.org/spec/DD/20100524/DI'
for p,u in [('bpmn',B),('bpmndi',D),('dc',C),('di',I)]:register_namespace(p,u)
def E(parent,tag,attrs=None):return SubElement(parent,tag,attrs or {})

def node(i,label,kind,x,y,w=220,h=70,lane='tutor'):
 return dict(id=i,label=label,kind=kind,x=x,y=y,w=w,h=h,lane=lane)

def build(stem,title,nodes,flows,messages,height):
 byid={n['id']:n for n in nodes}
 # flow item: (id,source,target,label,waypoints)
 defs=Element('{'+B+'}definitions',{'id':stem.replace('-','_'),'targetNamespace':'https://example.org/tutoris/concept','exporter':'TutorIS educational model'})
 process=E(defs,'{'+B+'}process',{'id':'Process','name':title,'isExecutable':'false'})
 lanes=E(process,'{'+B+'}laneSet',{'id':'LaneSet'})
 for lane,name in [('tutor','Репетитор'),('system','ИС')]:
  le=E(lanes,'{'+B+'}lane',{'id':'Lane_'+lane,'name':name})
  for n in nodes:
   if n['lane']==lane:E(le,'{'+B+'}flowNodeRef').text=n['id']
 for n in nodes:
  el=E(process,'{'+B+'}'+n['kind'],{'id':n['id'],'name':n['label']})
  for fid,src,tgt,label,pts in flows:
   if tgt==n['id']:E(el,'{'+B+'}incoming').text=fid
   if src==n['id']:E(el,'{'+B+'}outgoing').text=fid
  if n['id']=='timer': E(el,'{'+B+'}timerEventDefinition',{'id':'TimerDefinition'})
  if n['id']=='start': E(el,'{'+B+'}messageEventDefinition',{'id':'MessageDefinition'})
 for fid,src,tgt,label,pts in flows:
  E(process,'{'+B+'}sequenceFlow',{'id':fid,'sourceRef':src,'targetRef':tgt,**({'name':label} if label else {})})
 collab=E(defs,'{'+B+'}collaboration',{'id':'Collaboration'})
 E(collab,'{'+B+'}participant',{'id':'TutorPool','name':'Рабочее пространство одного репетитора','processRef':'Process'})
 E(collab,'{'+B+'}participant',{'id':'FamilyPool','name':'Ученик / родитель'})
 for j,(src,tgt,label,pts) in enumerate(messages): E(collab,'{'+B+'}messageFlow',{'id':'Message_'+str(j),'sourceRef':src,'targetRef':tgt,'name':label})
 diagram=E(defs,'{'+D+'}BPMNDiagram',{'id':'Diagram'})
 plane=E(diagram,'{'+D+'}BPMNPlane',{'id':'Plane','bpmnElement':'Collaboration'})
 containers=[('TutorPool',20,70,960,height-110),('Lane_tutor',50,105,450,height-145),('Lane_system',500,105,480,height-145),('FamilyPool',1040,70,170,height-110)]
 for nid,x,y,w,h in containers:
  sh=E(plane,'{'+D+'}BPMNShape',{'id':'DI_'+nid,'bpmnElement':nid,'isHorizontal':'false'})
  E(sh,'{'+C+'}Bounds',{k:str(v) for k,v in dict(x=x,y=y,width=w,height=h).items()})
 for n in nodes:
  sh=E(plane,'{'+D+'}BPMNShape',{'id':'DI_'+n['id'],'bpmnElement':n['id']})
  E(sh,'{'+C+'}Bounds',{k:str(v) for k,v in dict(x=n['x'],y=n['y'],width=n['w'],height=n['h']).items()})
 for fid,src,tgt,label,pts in flows:
  edge=E(plane,'{'+D+'}BPMNEdge',{'id':'DI_'+fid,'bpmnElement':fid})
  for x,y in pts:E(edge,'{'+I+'}waypoint',{'x':str(x),'y':str(y)})
 for j,(src,tgt,label,pts) in enumerate(messages):
  edge=E(plane,'{'+D+'}BPMNEdge',{'id':'DI_Message_'+str(j),'bpmnElement':'Message_'+str(j)})
  for x,y in pts:E(edge,'{'+I+'}waypoint',{'x':str(x),'y':str(y)})
 ElementTree(defs).write(ROOT/(stem+'.bpmn'),encoding='utf-8',xml_declaration=True)
 # editable draw.io cells, all coordinates absolute
 mx=Element('mxfile',{'host':'app.diagrams.net','version':'24.7.17'})
 dia=E(mx,'diagram',{'name':title,'id':stem})
 model=E(dia,'mxGraphModel',{'dx':'1300','dy':str(height),'grid':'1','gridSize':'10','page':'1','pageScale':'1','pageWidth':'1240','pageHeight':str(height),'background':'#FFFFFF'})
 root=E(model,'root');E(root,'mxCell',{'id':'0'});E(root,'mxCell',{'id':'1','parent':'0'})
 def cell(nid,value,style,x,y,w,h):
  c=E(root,'mxCell',{'id':nid,'value':value,'style':style,'vertex':'1','parent':'1'})
  E(c,'mxGeometry',{'x':str(x),'y':str(y),'width':str(w),'height':str(h),'as':'geometry'})
 def edge(nid,label,pts,dashed=False):
  c=E(root,'mxCell',{'id':nid,'value':label,'style':'edgeStyle=none;rounded=0;html=0;fontFamily=Arial;fontSize=17;labelBackgroundColor=#FFFFFF;strokeColor=#334155;strokeWidth=2;endArrow='+('open;endFill=0;dashed=1;startArrow=oval;startFill=0;' if dashed else 'block;endFill=1;'),'edge':'1','parent':'1'})
  if nid in ['clockhand','envelopemark']: c.set('style',c.get('style').replace('endArrow=block;endFill=1;','endArrow=none;'))
  g=E(c,'mxGeometry',{'relative':'1','as':'geometry'})
  E(g,'mxPoint',{'x':str(pts[0][0]),'y':str(pts[0][1]),'as':'sourcePoint'})
  E(g,'mxPoint',{'x':str(pts[-1][0]),'y':str(pts[-1][1]),'as':'targetPoint'})
  arr=E(g,'Array',{'as':'points'})
  for x,y in pts[1:-1]:E(arr,'mxPoint',{'x':str(x),'y':str(y)})
 base='whiteSpace=wrap;html=0;fontFamily=Arial;fontSize=19;strokeColor=#334155;strokeWidth=2;'
 cell('title',title,'text;html=0;fontFamily=Arial;fontSize=27;fontStyle=1;align=left;strokeColor=none;fillColor=none;',25,10,1170,45)
 cell('pool','','rounded=0;'+base+'fillColor=#FFFFFF;',20,70,960,height-110)
 cell('lane1','','rounded=0;'+base+'fillColor=#F8FAFC;',50,105,450,height-145)
 cell('lane2','','rounded=0;'+base+'fillColor=#EFF6FF;',500,105,480,height-145)
 cell('external','Ученик / родитель','rounded=0;verticalLabelPosition=middle;verticalAlign=middle;'+base+'fillColor=#F1F5F9;',1040,70,170,height-110)
 cell('poolname','Процесс одного независимого репетитора','text;html=0;fontFamily=Arial;fontSize=17;align=center;strokeColor=none;fillColor=none;',50,72,930,28)
 cell('lane1name','Репетитор','text;html=0;fontFamily=Arial;fontSize=21;fontStyle=1;strokeColor=none;fillColor=none;',60,108,430,30)
 cell('lane2name','ИС','text;html=0;fontFamily=Arial;fontSize=21;fontStyle=1;strokeColor=none;fillColor=none;',510,108,460,30)
 for n in nodes:
  style=base+'fillColor=#FFFFFF;rounded=1;arcSize=14;'
  if n['kind'].endswith('Event'):style=base+'shape=ellipse;fillColor=#FFFFFF;'+('strokeWidth=4;' if n['kind']=='endEvent' else '')
  if n['kind']=='exclusiveGateway':style=base+'shape=rhombus;fillColor=#FFFFFF;'
  label=n['label'] if n['kind'].endswith('Task') or n['kind']=='task' else ('×' if n['kind']=='exclusiveGateway' else '')
  cell(n['id'],label,style,n['x'],n['y'],n['w'],n['h'])
  if n['id']=='timer':
   cell('clock','',base+'shape=ellipse;fillColor=none;',n['x']+8,n['y']+8,24,24)
   edge('clockhand','',[(n['x']+20,n['y']+10),(n['x']+20,n['y']+20),(n['x']+30,n['y']+20)])
  if n['id']=='start':
   cell('envelope','',base+'rounded=0;fillColor=none;',n['x']+10,n['y']+12,20,14)
   edge('envelopemark','',[(n['x']+10,n['y']+12),(n['x']+20,n['y']+20),(n['x']+30,n['y']+12)])
  if n['kind'].endswith('Event') or n['kind']=='exclusiveGateway':
   cell('label_'+n['id'],n['label'],'text;html=0;fontFamily=Arial;fontSize=17;align=center;whiteSpace=wrap;strokeColor=none;fillColor=none;',(60 if n['id'] in ['agreed','continue','state'] else 525 if n['id']=='debt' else n['x']-70),(n['y']-40 if n['id'] in ['state','continue'] else n['y'] if n['kind']=='exclusiveGateway' else n['y']+n['h']+4),(175 if n['kind']=='exclusiveGateway' else n['w']+140),40)
 for fid,src,tgt,label,pts in flows:edge(fid,label,pts)
 for j,(src,tgt,label,pts) in enumerate(messages):edge('Message_'+str(j),label,pts,True)
 ElementTree(mx).write(ROOT/(stem+'.drawio'),encoding='utf-8',xml_declaration=True)
 # SVG view, same model as both editable formats
 parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1240" height="{height}" viewBox="0 0 1240 {height}">', '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#334155"/></marker><marker id="open" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M 0 0 L 10 5 L 0 10" fill="none" stroke="#334155"/></marker></defs>',f'<rect width="1240" height="{height}" fill="white"/>']
 def txt(x,y,s,size=20,anchor='middle',weight='normal'):
  lines=[]
  for line in s.split('\n'):lines.extend(textwrap.wrap(line,width=max(9,int(220/(size*.55)))) or [''])
  for k,line in enumerate(lines):parts.append(f'<text x="{x}" y="{y+k*(size+4)}" font-family="Arial, sans-serif" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="#0F172A">{escape(line)}</text>')
 parts.append(f'<text x="25" y="42" font-family="Arial, sans-serif" font-size="27" font-weight="bold" fill="#0F172A">{escape(title)}</text>')
 for nid,x,y,w,h in containers:
  color='#F8FAFC' if nid=='Lane_tutor' else '#EFF6FF' if nid=='Lane_system' else '#F1F5F9' if nid=='FamilyPool' else '#FFFFFF'
  parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}" stroke="#334155" stroke-width="2"/>')
 txt(275,132,'Репетитор',21,weight='bold');txt(740,132,'ИС',21,weight='bold');txt(1125,height/2,'Ученик /\nродитель',20)
 parts.append('<text x="515" y="94" text-anchor="middle" font-family="Arial, sans-serif" font-size="17" fill="#0F172A">Процесс одного независимого репетитора</text>')
 for fid,src,tgt,label,pts in flows:
  pp=' '.join(f'{x},{y}' for x,y in pts)
  parts.append(f'<polyline points="{pp}" fill="none" stroke="#334155" stroke-width="2" marker-end="url(#arrow)"/>')
  if label:
   # choose label along longest segment, with a white background
   pairs=list(zip(pts,pts[1:]));a,b=max(pairs,key=lambda pair:abs(pair[0][0]-pair[1][0])+abs(pair[0][1]-pair[1][1]))
   x=(a[0]+b[0])/2;y=(a[1]+b[1])/2-7
   parts.append(f'<rect x="{x-55}" y="{y-18}" width="110" height="24" fill="white"/>');txt(x,y,label,16)
 for j,(src,tgt,label,pts) in enumerate(messages):
  pp=' '.join(f'{x},{y}' for x,y in pts)
  parts.append(f'<polyline points="{pp}" fill="none" stroke="#64748B" stroke-width="2" stroke-dasharray="7 5" marker-end="url(#open)"/>')
 for n in nodes:
  x,y,w,h=n['x'],n['y'],n['w'],n['h'];kind=n['kind']
  if kind.endswith('Event'):
   parts.append(f'<ellipse cx="{x+w/2}" cy="{y+h/2}" rx="{w/2}" ry="{h/2}" fill="white" stroke="#334155" stroke-width="{4 if kind=="endEvent" else 2}"/>')
   if n['id']=='timer':
    parts.append(f'<circle cx="{x+w/2}" cy="{y+h/2}" r="14" fill="none" stroke="#334155"/><path d="M {x+w/2},{y+8} V {y+h/2} H {x+w-9}" fill="none" stroke="#334155"/>')
   txt(x+w/2,y+h+24,n['label'],16)
  elif kind=='exclusiveGateway':
   parts.append(f'<polygon points="{x+w/2},{y} {x+w},{y+h/2} {x+w/2},{y+h} {x},{y+h/2}" fill="white" stroke="#334155" stroke-width="2"/>')
   txt(x+w/2,y+h/2+8,'×',29);txt((147 if n['id'] in ['agreed','continue','state'] else 612),(y-20 if n['id'] in ['state','continue'] else y+20),n['label'],16)
  else:
   parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="white" stroke="#334155" stroke-width="2"/>')
   lines=sum(max(1,len(textwrap.wrap(l,width=22))) for l in n['label'].split('\n'))
   txt(x+w/2,y+h/2-(lines-1)*12+7,n['label'],19)
 parts.append('</svg>');(ROOT/(stem+'.svg')).write_text('\n'.join(parts))

intake=[node('start','Обращение получено','startEvent',255,155,40,40),
node('register','Зарегистрировать\nобращение','task',630,205,lane='system'),
node('offer','Предложить время','userTask',165,320),
node('reply','Получить ответ\nо времени','receiveTask',165,440),
node('agreed','Время согласовано?','exclusiveGateway',250,565,50,50),
node('close','Закрыть обращение\nс причиной','userTask',135,700),node('refused','Отказ','endEvent',225,825,40,40),
node('trial','Записать на\nпробный урок','task',630,555,lane='system'),
node('confirm','Отправить\nподтверждение','sendTask',630,700,lane='system'),
node('teach','Провести пробный;\nполучить решение','userTask',165,930),
node('continue','Продолжает?','exclusiveGateway',250,1050,50,50),
node('stop','Работа завершена','endEvent',105,1180,40,40),
node('regular','Создать регулярный\nграфик','task',630,1040,lane='system'),
node('done','Ученик подключён','endEvent',720,1180,40,40,lane='system')]
flows1=[('f1','start','register','',[(295,175),(740,175),(740,205)]),('f2','register','offer','',[(740,275),(740,300),(275,300),(275,320)]),('f3','offer','reply','',[(275,390),(275,440)]),('f4','reply','agreed','',[(275,510),(275,565)]),('f5','agreed','close','Нет',[(275,615),(275,660),(245,660),(245,700)]),('f6','close','refused','',[(245,770),(245,800),(245,825)]),('f7','agreed','trial','Да',[(300,590),(630,590)]),('f8','trial','confirm','',[(740,625),(740,700)]),('f9','confirm','teach','',[(740,770),(740,895),(275,895),(275,930)]),('f10','teach','continue','',[(275,1000),(275,1050)]),('f11','continue','stop','Нет',[(250,1075),(125,1075),(125,1180)]),('f12','continue','regular','Да',[(300,1075),(630,1075)]),('f13','regular','done','',[(740,1110),(740,1180)])]
messages1=[('FamilyPool','start','Обращение',[(1040,160),(930,160),(930,150),(275,150),(275,155)]),('offer','FamilyPool','Предложение',[(385,350),(980,350),(1040,350)]),('FamilyPool','reply','Ответ',[(1040,470),(970,470),(385,470)]),('confirm','FamilyPool','Подтверждение',[(850,735),(1040,735)])]
build('01-intake','TO-BE: обращение и пробное занятие',intake,flows1,messages1,1360)
lesson=[node('timer','Пора напомнить','startEvent',720,155,40,40,lane='system'),node('remind','Сформировать\nнапоминание','sendTask',630,235,lane='system'),node('status','Уточнить статус\nзанятия','userTask',165,235),node('state','Статус?','exclusiveGateway',250,375,50,50),node('move','Задать\nновое время','userTask',60,505,180,80),node('moved','Новое время задано','endEvent',130,650,40,40),node('cancel','Применить правило\nотмены','task',630,505,lane='system'),node('teach','Провести урок','userTask',285,505,190,70),node('progress','Записать тему,\nДЗ и результат','userTask',285,650,190,70),node('account','Обновить списание\nбез дублирования','task',630,795,lane='system'),node('payment','Подтвердить\nпоступления / аванс','userTask',250,795),node('balance','Пересчитать баланс','task',630,930,lane='system'),node('debt','Есть долг?','exclusiveGateway',715,1060,50,50,lane='system'),node('notify','Отправить\nнапоминание о долге','sendTask',540,1170,lane='system'),node('nodebt','Цикл завершён','endEvent',885,1180,40,40,lane='system'),node('done','Долг зафиксирован','endEvent',630,1310,40,40,lane='system')]
flows2=[('f1','timer','remind','',[(740,195),(740,235)]),('f2','remind','status','',[(630,270),(385,270)]),('f3','status','state','',[(275,305),(275,375)]),('f4','state','move','Перенос',[(250,400),(150,400),(150,505)]),('f5','move','moved','',[(150,585),(150,650)]),('f6','state','cancel','Отмена',[(300,400),(740,400),(740,505)]),('f7','state','teach','Проведено',[(275,425),(275,465),(380,465),(380,505)]),('f8','teach','progress','',[(380,575),(380,650)]),('f9','progress','account','',[(475,685),(740,685),(740,795)]),('f10','cancel','account','',[(850,540),(930,540),(930,830),(850,830)]),('f11','account','payment','',[(630,830),(470,830)]),('f12','payment','balance','',[(360,865),(360,965),(630,965)]),('f13','balance','debt','',[(740,1000),(740,1060)]),('f14','debt','notify','Да',[(740,1110),(740,1140),(650,1140),(650,1170)]),('f15','debt','nodebt','Нет',[(765,1085),(905,1085),(905,1180)]),('f16','notify','done','',[(650,1240),(650,1310)])]
messages2=[('remind','FamilyPool','Напоминание',[(850,270),(1040,270)]),('notify','FamilyPool','Сумма долга',[(760,1205),(820,1205),(820,1280),(1040,1280)])]
build('02-lesson','TO-BE: занятие, прогресс и расчёты',lesson,flows2,messages2,1490)
print('Built 2 draw.io + 2 BPMN + 2 SVG files')
