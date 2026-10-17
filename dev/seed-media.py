"""Create a new disposable database for real-renderer browser checks; never host data."""
import json,sys,struct,zlib,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from learning_store import Store
folder=Path(tempfile.mkdtemp(prefix='learning-media-preview-')).resolve()
print('Disposable preview data:',folder,file=sys.stderr)
s=Store(folder/'learning.sqlite3')
started=s.dispatch('course_start',{'request_id':'media-browser-v1','title':'Kafka diagrams and saved images','intent':'topic','level':'beginner','materials':[]})
s.dispatch('course_plan',{'context_id':started['context_id'],'job_id':started['job_id'],'summary':'Testing saved lesson media.','assumptions':[],'lessons':[{'key':'one','title':'How Kafka moves events','goal':'Follow an event from producer to consumers.'}]},channel='chat_relayed')
# A deterministic PNG fixture: blue producer, teal broker, orange consumer.
w,h=600,180
raw=bytearray()
for y in range(h):
 raw.append(0)
 for x in range(w):
  color=(247,249,253)
  if 50<y<130:
   if 30<x<170:color=(54,92,221)
   elif 230<x<370:color=(33,159,145)
   elif 430<x<570:color=(222,145,56)
  if 86<y<94 and (170<=x<=230 or 370<=x<=430):color=(70,83,110)
  raw.extend(color)
def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))
data=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
image=folder/'generated.png';image.write_bytes(data)
asset=s.dispatch('course_asset_import',{'context_id':started['context_id'],'path':str(image),'title':'Producer, broker, consumer — saved PNG fixture'},channel='chat_relayed')
arch=json.loads((ROOT/'tests/fixtures/archify/web-app.architecture.json').read_text())
mermaid='flowchart LR\n P[Producer] --> T[Kafka topic]\n T --> A[Consumer group A]\n T --> B[Consumer group B]'
content='# Follow an event\n\nA producer writes an event; independent consumer groups read it.\n\n```mermaid\n'+mermaid+'\n```\n\n## Architecture\n\n```archify\n'+json.dumps(arch)+'\n```\n\n## Saved image\n\n'+asset['markdown']+'\n\n## Invalid diagram fallback\n\n```mermaid\nflowchart LR\n A[broken\n```\n\n## Forbidden configuration fallback\n\n```mermaid\n%%{init: {securityLevel: "loose"}}%%\nflowchart LR\n A --> B\n```'
s.dispatch('course_lesson',{'context_id':started['context_id'],'job_id':started['job_id'],'lesson_key':'one','content':content,'source_ids':[]},channel='chat_relayed')
s.dispatch('course_propose',{'context_id':started['context_id'],'request_id':'media-preview','base_revision':1,'mode':'revise','summary':'Add clearer diagram captions.','lessons':[{'lesson_key':'one','content':content+'\n\nEach diagram can be enlarged.','source_ids':[]}]},channel='chat_relayed')
image.unlink() # Saved images must survive removal of the original generated file.
print(json.dumps({'data_dir':str(folder),**started}))
