import test from 'node:test';
import assert from 'node:assert/strict';
import {TutorSession, tutorPrompt, visibleHistory} from '../src/tutor-session.mjs';
function fixture(overrides={}) {
 const calls=[], listeners=new Map(), actions=[];
 const transport={onEvent(type,fn){listeners.set(type,fn);return()=>listeners.delete(type);},setSession(){},async request(method,params){calls.push({method,params});if(method==='session.create'&&params.parent_session_id&&overrides.seededCreate)return overrides.seededCreate(params);if(overrides[method])return overrides[method](params);if(method==='model.options')return {provider:'openai',model:'gpt-default',providers:[]};if(method==='config.set')return {key:'model',value:params.value.split(' ')[0],scope:'session',confirm_required:false};if(method==='session.create'&&params.parent_session_id)return {session_id:'branch-live',stored_session_id:'branch-saved'};if(method==='session.create')return {session_id:'live',stored_session_id:'saved'};if(method==='session.resume')return {session_id:'live2',stored_session_id:'saved',messages:[{role:'assistant',text:'Earlier lesson'}]};if(method==='session.history')return {messages:[]};if(method==='session.activate')return {running:false,open_requests:[]};return {status:'streaming'};}};
 const session=new TutorSession({transport,scope:'scope',profile:'default',pollMs:0,request:async(path,body)=>{actions.push(body);return overrides.action?overrides.action(body):{};}});
 return{session,calls,actions,emit:(type,payload={},sid='live')=>listeners.get(type)?.({session_id:sid,payload})};
}
const context={track_id:'track',context_id:'context',job_id:'job',course:{track:{title:'Queues'},sources:[],outline:[]}};
test('path naming is scoped to supported generation and carries saved naming status',()=>{
 const course={...context.course,capabilities:['path-titles-v1'],track:{title:'I want to learn Kafka',interest:'I want to learn Kafka'}};
 assert.match(tutorPrompt('Generate',{...context,course}),/Include path_title/);
 assert.doesNotMatch(tutorPrompt('Explain',{...context,job_id:undefined,course}),/During this generation, name/);
 assert.doesNotMatch(tutorPrompt('Generate',context),/During this generation, name/);
 const named=tutorPrompt('Generate',{...context,course:{...course,track:{...course.track,title:'Kafka Fundamentals',title_generated:true}}});
 assert.match(named,/"title_generated":true/);
 assert.doesNotMatch(named,/During this generation, name/);
});
test('creates and binds durable session before one contextual submit',async()=>{const f=fixture();await f.session.send('Build a queue',context);assert.equal(f.calls.filter(c=>c.method==='prompt.submit').length,1);assert.equal(f.actions[0].action,'course_bind');assert.equal(f.actions[0].params.session_id,'saved');assert.match(f.calls.at(-1).params.text,/learning_course_plan/);assert.equal(f.session.state.messages[0].text,'Build a queue');assert.equal(f.session.state.busy,true);f.session.dispose();});
test('restores history and uses runtime ID without sending a prompt',async()=>{const f=fixture();await f.session.restore({session_id:'saved',scope:'scope'},context);assert.equal(f.session.state.messages[0].text,'Earlier lesson');assert.equal(f.calls.filter(c=>c.method==='prompt.submit').length,0);await f.session.send('Explain', {...context,job_id:undefined});assert.equal(f.calls.at(-1).params.session_id,'branch-live');f.session.dispose();});
test('rejects binding from another connection scope',async()=>{const f=fixture();await assert.rejects(f.session.restore({session_id:'saved',scope:'other'},context),/different/);assert.equal(f.calls.length,0);f.session.dispose();});
test('uncertain submission is never replayed and blocks another send until restored',async()=>{const f=fixture({'prompt.submit':()=>{throw Error('Connection lost');}});await assert.rejects(f.session.send('Teach',context),/Connection lost/);await assert.rejects(f.session.send('Teach',context),/Reconnect/);assert.equal(f.calls.filter(c=>c.method==='prompt.submit').length,1);assert.match(f.session.state.error,/Reconnect/);f.session.dispose();});
test('events from other sessions and after clear do not change transcript',async()=>{const f=fixture();await f.session.send('Teach',context);f.emit('message.delta',{text:'foreign'},'another');assert.equal(f.session.state.messages.length,1);f.emit('message.delta',{text:'Hello'});assert.equal(f.session.state.messages.at(-1).text,'Hello');f.session.clear();f.emit('message.delta',{text:'late'});assert.deepEqual(f.session.state.messages,[]);f.session.dispose();});
test('stop interrupts the correct runtime and marks the generation stopped',async()=>{const f=fixture();await f.session.send('Teach',context);await f.session.stop();assert.equal(f.calls.at(-1).method,'session.interrupt');assert.equal(f.actions.at(-1).params.status,'stopped');assert.equal(f.session.state.busy,false);f.session.dispose();});
test('approval is scoped and requires explicit response',async()=>{const f=fixture();await f.session.send('Teach',context);f.emit('approval',{id:'srq-1',command:'echo example',choices:['once','deny']});assert.equal(f.session.state.pending.kind,'approval');assert.equal(f.calls.filter(c=>c.method==='request.answer').length,0);await f.session.respond('deny');assert.deepEqual(f.calls.at(-1).params.result,{choice:'deny'});f.session.dispose();});
test('generated context stays out of rendered history and source excerpts stay out of prompt',()=>{const prompt=tutorPrompt('Explain',{...context,course:{...context.course,sources:[{id:'s',title:'Private',sharing:'metadata-only',excerpt:'SECRET'}]}});assert.ok(!prompt.includes('SECRET'));assert.deepEqual(visibleHistory([{role:'user',text:prompt},{role:'tool',text:'hidden'}]).map(m=>m.text),['Explain']);});
test('clarification locks use host qid and restore skips answers already locked',async()=>{const f=fixture();await f.session.send('Teach',context);f.emit('clarify',{id:'srq-c',questions:[{qid:'q1',question:'First?'},{qid:'q2',question:'Second?'}],answers:{q1:'already'}});assert.equal(f.session.state.pending.question,'Second?');await f.session.respond('answer');assert.equal(f.calls.at(-1).params.question_id,'q2');f.session.dispose();});
test('clear during session creation never submits or binds the old track',async()=>{let resolve;const f=fixture({'session.create':()=>new Promise(r=>{resolve=r;})});const pending=f.session.send('Teach',context);f.session.clear();resolve({session_id:'old',stored_session_id:'saved'});await pending;assert.equal(f.actions.length,0);assert.equal(f.calls.filter(c=>c.method==='prompt.submit').length,0);f.session.dispose();});
test('polling cannot finish a job while course binding is still pending',async()=>{let release;const f=fixture();f.session.request=async(path,body)=>body.action==='course_bind'?new Promise(r=>{release=r;}):{};const send=f.session.send('Teach',context);await new Promise(r=>setTimeout(r,0));await f.session.reconcile();assert.equal(f.calls.filter(c=>c.method==='session.activate').length,0);release({});await send;f.session.dispose();});
test('authoritative snapshots clear resolved permissions and expired decisions are explicit',async()=>{const f=fixture({'request.answer':()=>({status:'expired'})});await f.session.send('Teach',context);f.emit('approval',{id:'r',choices:['deny']});assert.deepEqual(f.session.state.pending.options,['deny']);await assert.rejects(f.session.respond('once'),/available/);await f.session.respond('deny');assert.equal(f.session.state.pending,null);assert.match(f.session.state.error,/expired/);f.emit('approval',{id:'r2',choices:['once','deny']});f.session.pendingFrom({});assert.equal(f.session.state.pending,null);f.session.dispose();});
test('profile-mismatched stream is ignored even with same runtime ID',async()=>{const f=fixture();await f.session.send('Teach',context);f.session.event('message.delta',{session_id:'live',profile:'other',payload:{text:'foreign'}});assert.equal(f.session.state.messages.length,1);f.session.dispose();});
test('Stop during preparation cancels submission even when bind resolves later',async()=>{let release;const f=fixture();f.session.request=async(path,body)=>body.action==='course_bind'?new Promise(r=>{release=r;}):{};const sending=f.session.send('Teach',context);await new Promise(r=>setTimeout(r,0));await f.session.stop();release({});await sending;assert.equal(f.calls.filter(c=>c.method==='prompt.submit').length,0);assert.equal(f.session.state.busy,false);f.session.dispose();});
test('Stop before session creation returns prevents bind and submission',async()=>{let release;const f=fixture({'session.create':()=>new Promise(r=>{release=r;})});const sending=f.session.send('Teach',context);await f.session.stop();release({session_id:'new',stored_session_id:'new-saved'});await sending;assert.equal(f.calls.filter(c=>c.method==='prompt.submit').length,0);assert.equal(f.actions.filter(a=>a.action==='course_bind').length,0);f.session.dispose();});
test('disposed sessions cannot create or submit new model work',async()=>{const f=fixture();f.session.dispose();await assert.rejects(f.session.send('Teach',context),/closed/);assert.equal(f.calls.length,0);});
test('prompt carries selected level and project intent separately from full goal',()=>{const prompt=tutorPrompt('Teach',{...context,course:{track:{title:'Queues',level:'advanced',intent:'project',interest:'Build a durable queue'},sources:[],outline:[]}});assert.match(prompt,/"level":"advanced"/);assert.match(prompt,/"intent":"project"/);assert.match(prompt,/"interest":"Build a durable queue"/);});
test('completion holds the turn until persistence is confirmed',async()=>{const f=fixture();await f.session.send('Teach',context);let release;f.session.request=async(path,body)=>body.action==='course_read'?new Promise(r=>{release=r;}):{};const finishing=f.session.finish();await assert.rejects(f.session.send('Another',{...context,job_id:'other'}),/Wait/);release({jobs:[{id:'job',status:'completed'}]});await finishing;assert.equal(f.session.state.busy,false);f.session.dispose();});
test('explicit send replaces a definitively missing saved conversation',async()=>{const f=fixture({'session.resume':()=>{throw Object.assign(Error('Session not found'),{code:4007});}});await f.session.send('Teach',{...context,course:{...context.course,binding:{session_id:'missing',scope:'scope'}}});assert.equal(f.calls.filter(c=>c.method==='session.create').length,1);assert.equal(f.calls.filter(c=>c.method==='prompt.submit').length,1);f.session.dispose();});
test('transient restore failures never create a replacement conversation',async()=>{const f=fixture({'session.resume':()=>{throw Error('Connection lost');}});await assert.rejects(f.session.send('Teach',{...context,course:{...context.course,binding:{session_id:'saved',scope:'scope'}}}),/Connection lost/);assert.equal(f.calls.filter(c=>c.method==='session.create').length,0);f.session.dispose();});
test('restoring a failed idle turn exposes its error and closes its job',async()=>{const f=fixture({'session.resume':()=>({session_id:'live',messages:[],running:false,inflight:{error:'Provider failed'}})});await f.session.restore({session_id:'saved',scope:'scope'},context);assert.match(f.session.state.error,/Provider failed/);assert.ok(f.actions.some(a=>a.action==='course_job_status'&&a.params.status==='failed'));f.session.dispose();});
test('conversation prompts authorize proposals for requested edits and carry authoritative revision',()=>{
 const prompt=tutorPrompt('Make the lesson practical',{...context,job_id:undefined,lesson_key:'first',change_request:{mode:'revise',target:'lesson'},course:{revision:3,track:{title:'Queues'},outline:[{key:'first',title:'Basics',goal:'Understand queues'}],sources:[]}});
 assert.match(prompt,/learning_course_propose/);assert.match(prompt,/"revision":3/);assert.match(prompt,/"target":"lesson"/);
 assert.match(prompt,/Apply changes/);assert.doesNotMatch(prompt,/call learning_course_apply/);
});
test('streams exposed thinking and correlated tools without replacing the reply',async()=>{
 const f=fixture();await f.session.send('Explain',context);
 f.emit('reasoning.delta',{text:'Compare the examples.'},'foreign');
 assert.equal(f.session.state.messages.length,1);
 f.emit('reasoning.delta',{text:'Compare '});f.emit('reasoning.delta',{text:'the examples.'});
 f.emit('tool.start',{tool_id:'a',name:'learning_course_read',args:{context_id:'private'}});
 f.emit('tool.start',{tool_id:'b',name:'web_search'});
 f.emit('tool.complete',{tool_id:'b',name:'web_search',result:{error:'Search unavailable'}});
 f.emit('tool.complete',{tool_id:'a',name:'learning_course_read',duration_s:1.2});
 f.emit('message.delta',{text:'Here is the example.'});
 const messages=f.session.state.messages;
 assert.equal(messages.find(m=>m.kind==='reasoning').text,'Compare the examples.');
 assert.equal(messages.find(m=>m.toolId==='a').status,'complete');
 assert.equal(messages.find(m=>m.toolId==='b').status,'error');
 assert.equal(messages.at(-1).text,'Here is the example.');
 assert.ok(!JSON.stringify(messages).includes('private'));f.session.dispose();
});
test('plan snapshots are revision guarded and restored without a model request',async()=>{
 const f=fixture({'session.resume':()=>({session_id:'live',messages:[],running:false,todo_state:{revision:3,todos:[{id:'a',content:'Read source',status:'completed'}]}})});
 await f.session.restore({session_id:'saved',scope:'scope'},context);
 assert.equal(f.session.state.plan.todos[0].status,'completed');
 f.emit('todo.updated',{revision:2,todos:[{id:'a',content:'Old',status:'pending'}]});
 assert.equal(f.session.state.plan.revision,3);
 f.emit('todo.updated',{revision:4,todos:[]});assert.deepEqual(f.session.state.plan.todos,[]);
 f.session.clear();assert.equal(f.session.state.plan,null);f.session.dispose();
});
test('restored host reasoning and tool rows remain visible without raw tool arguments',()=>{
 const history=visibleHistory([{role:'assistant',text:'',reasoning:'Compare options.'},{role:'tool',name:'web_search',tool_call_id:'t',context:'queue docs',args:{secret:'not for display'}},{role:'assistant',text:'Answer'},{role:'assistant',display_kind:'hidden',reasoning:'hidden'}]);
 assert.equal(history[0].kind,'reasoning');assert.equal(history[0].text,'Compare options.');
 assert.equal(history[1].kind,'tool');assert.equal(history[1].status,'finished');
 assert.equal(history[2].text,'Answer');assert.ok(!JSON.stringify(history).includes('not for display'));
});
test('stop and disconnect leave tool results unconfirmed, never successful',async()=>{
 const f=fixture();await f.session.send('Explain',context);f.emit('tool.start',{tool_id:'a',name:'web_search'});
 await f.session.stop();assert.equal(f.session.state.messages.find(m=>m.toolId==='a').status,'interrupted');f.session.dispose();
 const g=fixture();await g.session.send('Explain',context);g.emit('tool.start',{tool_id:'b',name:'web_search'});g.emit('transport.disconnected');
 assert.equal(g.session.state.messages.find(m=>m.toolId==='b').status,'unknown');g.session.dispose();
});
test('waiting notices are status updates, not model reasoning',async()=>{
 const f=fixture();await f.session.send('Explain',context);
 f.emit('thinking.delta',{text:'⏳ waiting on the provider'});
 assert.equal(f.session.state.status,'⏳ waiting on the provider');
 assert.equal(f.session.state.messages.length,1);
 f.emit('status.update',{kind:'compacting',text:'Compacting conversation'});
 assert.equal(f.session.state.status,'Compacting conversation');f.session.dispose();
});
test('a late plan snapshot cannot replace newer state after another send',async()=>{
 const f=fixture();await f.session.send('Explain',{...context,job_id:undefined});
 f.emit('todo.updated',{revision:10,todos:[{id:'a',content:'Current',status:'completed'}]});await f.session.finish();
 await f.session.send('Another question',{...context,job_id:undefined});
 f.emit('todo.updated',{revision:9,todos:[{id:'a',content:'Old',status:'pending'}]});
 assert.equal(f.session.state.plan.revision,10);f.session.dispose();
});
test('new tutor pins the path model in session creation without touching global configuration',async()=>{
 const f=fixture();await f.session.send('Teach',{...context,course:{...context.course,model:{provider:'openai',model:'gpt-picked'}}});
 const create=f.calls.find(c=>c.method==='session.create');assert.equal(create.params.model,'gpt-picked');assert.equal(create.params.provider,'openai');assert.equal(f.calls.filter(c=>c.method==='config.set').length,0);f.session.dispose();
});
test('changing an existing path model and returning to default are confirmed before prompt submission',async()=>{
 const f=fixture({'model.options':()=>({provider:'openai',model:'gpt-default',providers:[]}), 'config.set':params=>({key:'model',value:params.value.split(' ')[0],scope:'session',confirm_required:false})});
 const send=selection=>f.session.send('Explain',{...context,job_id:undefined,course:{...context.course,model:selection}});
 await send({provider:'openai',model:'gpt-first'});await f.session.finish();await send({provider:'openai',model:'gpt-next'});await f.session.finish();await send(null);
 assert.deepEqual(f.calls.filter(c=>c.method==='session.create'&&c.params.parent_session_id).map(c=>c.params.model),['gpt-next','gpt-default']);assert.equal(f.calls.filter(c=>c.method==='config.set').length,0);
 assert.equal(f.calls.at(-1).method,'prompt.submit');f.session.dispose();
});
test('restored model override is reconciled before the first new prompt',async()=>{
 const f=fixture({'model.options':()=>({provider:'openai',model:'gpt-default',providers:[]}), 'config.set':()=>({key:'model',value:'gpt-default',scope:'session',confirm_required:false})});
 await f.session.restore({session_id:'saved',scope:'scope'},context);assert.equal(f.calls.filter(c=>c.method==='config.set').length,0);
 await f.session.send('Explain',{...context,job_id:undefined});assert.equal(f.calls.filter(c=>c.method==='session.create'&&c.params.parent_session_id).length,1);f.session.dispose();
});
test('unsupported safe branching never sends with the previous model',async()=>{
 const f=fixture({seededCreate:()=>{throw Error('Session branching is unavailable');}});
 await f.session.send('Explain',{...context,job_id:undefined});await f.session.finish();
 await assert.rejects(f.session.send('Again',{...context,job_id:undefined,course:{...context.course,model:{provider:'openai',model:'gpt-picked'}}}),/branching/);
 assert.equal(f.calls.filter(c=>c.method==='prompt.submit').length,1);assert.equal(f.session.uncertain,false);f.session.dispose();
});
test('model switching is blocked during a tutor response',async()=>{
 const f=fixture();await f.session.send('Explain',context);
 await assert.rejects(f.session.send('Again',{...context,course:{...context.course,model:{provider:'openai',model:'gpt-picked'}}}),/Wait/);
 assert.equal(f.calls.filter(c=>c.method==='config.set').length,0);f.session.dispose();
});
test('lesson instructions specify observable teaching and separate optional practice',()=>{
 const prompt=tutorPrompt('Teach',context);assert.match(prompt,/prerequisites/);assert.match(prompt,/misconception/);assert.match(prompt,/criteria/);assert.match(prompt,/separate practice/i);assert.match(prompt,/coherent project/i);
});
test('a cancelled model branch keeps the original conversation and cannot submit late',async()=>{
 let release;const f=fixture({seededCreate:()=>new Promise(r=>{release=r;})});
 const selected={provider:'openai',model:'gpt-original'};const ctx=model=>({...context,job_id:undefined,course:{...context.course,model}});
 await f.session.send('First',ctx(selected));await f.session.finish();
 const sending=f.session.send('Switch',ctx({provider:'openai',model:'gpt-next'}));await new Promise(r=>setTimeout(r,0));
 await f.session.stop();release({session_id:'next',stored_session_id:'next-saved'});await assert.rejects(sending,/changed|cancel/);
 assert.equal(f.session.runtime,'live');assert.equal(f.calls.filter(c=>c.method==='prompt.submit').length,1);f.session.dispose();
});
test('clearing a restored path during default lookup prevents config mutation and submission',async()=>{
 let release;const f=fixture({'model.options':()=>new Promise(r=>{release=r;})});
 await f.session.restore({session_id:'saved',scope:'scope'},context);const sending=f.session.send('Explain',context);await new Promise(r=>setTimeout(r,0));
 f.session.clear();release({provider:'openai',model:'gpt-default',providers:[]});await assert.rejects(sending,/changed|cancel/);
 assert.equal(f.calls.filter(c=>['config.set','prompt.submit'].includes(c.method)).length,0);f.session.dispose();
});
test('model branch retains displayed history, rebinds the path, and ignores old-session events',async()=>{
 const f=fixture();await f.session.send('First',{...context,job_id:undefined});f.emit('message.delta',{text:'Original answer'});await f.session.finish();
 await f.session.send('Next',{...context,job_id:undefined,course:{...context.course,model:{provider:'openai',model:'gpt-next'}}});
 assert.ok(f.session.state.messages.some(m=>m.text==='Original answer'));
 assert.equal(f.actions.filter(a=>a.action==='course_bind').at(-1).params.session_id,'branch-saved');
 f.emit('message.delta',{text:'stale'},'live');assert.ok(!f.session.state.messages.some(m=>m.text.includes('stale')));
 assert.equal(f.calls.at(-1).params.session_id,'branch-live');f.session.dispose();
});
test('failed branch creation reuses its idempotency key and never submits the pending turn',async()=>{
 let tries=0;const f=fixture({seededCreate:()=>{if(++tries===1)throw Error('Connection lost');return{session_id:'next',stored_session_id:'next-saved'};}});
 await f.session.send('First',{...context,job_id:undefined});await f.session.finish();
 const ctx={...context,job_id:undefined,course:{...context.course,model:{provider:'openai',model:'gpt-next'}}};
 await assert.rejects(f.session.send('Next',ctx),/Connection lost/);assert.equal(f.calls.filter(c=>c.method==='prompt.submit').length,1);
 await f.session.send('Next',ctx);const branches=f.calls.filter(c=>c.method==='session.create'&&c.params.parent_session_id);assert.equal(branches[0].params.idempotency_key,branches[1].params.idempotency_key);f.session.dispose();
});
test('restoring an unchanged durable model selection reuses the saved conversation',async()=>{
 for(const model of [null,{provider:'openai',model:'gpt-picked'}]){
  const f=fixture();const ctx={...context,job_id:undefined,course:{...context.course,model}};
  await f.session.restore({session_id:'saved',scope:'scope',model},ctx);await f.session.send('Continue',ctx);
  assert.equal(f.calls.filter(c=>c.method==='session.create'&&c.params.parent_session_id).length,0);assert.equal(f.calls.at(-1).params.session_id,'live2');f.session.dispose();
 }
});
test('a changed path selection branches after restoring a different applied selection',async()=>{
 const f=fixture();const model={provider:'openai',model:'gpt-new'},ctx={...context,job_id:undefined,course:{...context.course,model}};
 await f.session.restore({session_id:'saved',scope:'scope',model:null},ctx);await f.session.send('Continue',ctx);
 assert.equal(f.calls.filter(c=>c.method==='session.create'&&c.params.parent_session_id).length,1);
 assert.deepEqual(f.actions.filter(a=>a.action==='course_bind').at(-1).params.model,model);f.session.dispose();
});
test('creation persists the applied default or explicit selection beside the durable binding',async()=>{
 for(const model of [null,{provider:'openai',model:'gpt-picked'}]){
  const f=fixture();await f.session.send('Teach',{...context,course:{...context.course,model}});
  assert.deepEqual(f.actions.find(a=>a.action==='course_bind').params.model,model);f.session.dispose();
 }
});

test('fresh tutor automatically receives saved earlier lessons before generation',async()=>{
 const continuity={revision:3,outline:[{key:'three',title:'Groups',goal:'Read events'}],earlier_lessons:[{key:'one',content:'Orders use order_id.',version:2}],missing_earlier_lessons:['two']};
 const f=fixture({action:body=>body.action==='course_context'?continuity:{}});
 await f.session.send('Teach',{...context,lesson_key:'three',course:{...context.course,capabilities:['lesson-continuity-v1']}});
 assert.equal(f.actions[0].action,'course_context');
 const prompt=f.calls.find(c=>c.method==='prompt.submit').params.text;
 assert.match(prompt,/Orders use order_id/);assert.match(prompt,/"revision":3/);assert.match(prompt,/missing_earlier_lessons/);
 f.session.dispose();
});
test('context preparation failure does not submit a disconnected lesson',async()=>{
 const f=fixture({action:()=>{throw Error('Context unavailable');}});
 await assert.rejects(f.session.send('Teach',{...context,course:{...context.course,capabilities:['lesson-continuity-v1']}}),/Context unavailable/);
 assert.equal(f.calls.filter(c=>c.method==='prompt.submit').length,0);f.session.dispose();
});
