"""Seed a disposable continuity review; never reads or writes a Hermes profile."""
import json,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from learning_store import Store
folder=Path(tempfile.mkdtemp(prefix='learning-continuity-'))
s=Store(folder/'learning.sqlite3')
start=s.dispatch('course_start',dict(request_id='start',title='Connected Kafka lessons',intent='topic',level='beginner',materials=[]))
def call(name,**p):return s.dispatch(name,{'context_id':start['context_id'],**p})
outline=[dict(key='one',title='Events and topics',goal='Follow an order event'),dict(key='two',title='Consumer groups',goal='Read the same topic independently'),dict(key='three',title='Offsets and recovery',goal='Continue from saved consumer progress')]
call('course_plan',job_id=start['job_id'],summary='Follow the same Kafka example across lessons.',assumptions=[],lessons=outline)
call('course_lesson',job_id=start['job_id'],lesson_key='one',content='# Order events\n\nPublish orders to the orders topic using order_id.',source_ids=[])
job=call('course_generate',request_id='second',lesson_key='two')
call('course_lesson',job_id=job['job_id'],lesson_key='two',content='# Consumer groups\n\nTwo consumer groups read the orders topic independently. Continue using order_id.',source_ids=[])
call('course_position',lesson_key='two',completed=['one','two'])
p=call('course_propose',request_id='payments',base_revision=1,mode='revise',summary='Use payment events as our running example.',lessons=[dict(lesson_key='one',content='# Payment events\n\nPublish payments to the payments topic using payment_id.',source_ids=[])])['proposal']
call('course_apply',proposal_id=p['id'])
print(json.dumps({'data_dir':str(folder),**start}))
