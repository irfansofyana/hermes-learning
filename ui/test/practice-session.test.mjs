import test from 'node:test';
import assert from 'node:assert/strict';
import {PracticeSession,practicePrompt} from '../src/practice-session.mjs';
const input={context:{context_id:'context',track_id:'track'},course:{track:{title:'Queues'},model:null},lesson:{key:'first',version:2},answer:'Use a queue',hints_used:1,explanation_shown:false,request_id:'request'};
const tick=()=>new Promise(resolve=>setImmediate(resolve));
function fixture(overrides={}) {
 const calls=[],actions=[],listeners=new Map();
 let attempt={id:'attempt',track_id:'track',lesson_key:'first',lesson_version:2,status:'pending'};
 const transport={setSession(){throw Error('Must not change tutor selection');},reconnect(){return overrides.reconnect?.();},onEvent(type,fn){listeners.set(type,fn);return()=>listeners.delete(type);},async request(method,params){calls.push({method,params});if(overrides[method])return overrides[method](params);if(method==='session.create')return{session_id:'practice-live',stored_session_id:'practice-saved'};if(method==='session.resume')return{session_id:'practice-live',stored_session_id:'practice-saved',running:true};if(method==='session.activate')return{running:false};return{};}};
 const request=async(path,body)=>{actions.push(body);const {action,params}=body;if(overrides[action])return overrides[action](params);if(action==='practice_submit')return{attempt,evaluation:{attempt_id:attempt.id,evaluation_token:'secret',lesson:{title:'First',content:'Queue material',practice:{prompt:'Why queue?',criteria:['Explain ordering'],hints:['Think FIFO'],explanation:'FIFO ordering'}},answer:input.answer,hints_used:1,explanation_shown:false}};if(action==='practice_read')return{attempts:[attempt]};if(action==='practice_bind'){attempt={...attempt,session_id:params.session_id,scope:params.scope};return{attempt};}if(action==='practice_status'){attempt={...attempt,status:params.status,error:params.error};return{attempt};}throw Error(action);};
 const session=new PracticeSession({transport,request,scope:'scope',profile:'default',pollMs:0});
 return{session,calls,actions,setAttempt(next){attempt={...attempt,...next};},getAttempt(){return attempt;},emit(type,payload={},session_id='practice-live',profile='default'){listeners.get(type)?.({session_id,profile,payload});}};
}
test('practice persists and binds before submitting a dedicated evaluation',async()=>{const f=fixture();await f.session.check(input);assert.deepEqual(f.actions.map(a=>a.action),['practice_submit','practice_bind']);assert.equal(f.calls[0].params.close_on_disconnect,false);assert.equal(f.calls[1].params.session_id,'practice-live');assert.equal(f.calls[1].method,'prompt.submit');assert.equal(f.session.state.active.lesson_version,2);assert.equal(f.session.state.busy,true);f.session.dispose();});
test('chat completion cannot invent saved feedback',async()=>{const f=fixture();await f.session.check(input);await f.session.finish({text:'Correct!'});assert.equal(f.session.state.attempt.status,'failed');assert.match(f.session.state.error,/without saving/i);f.session.dispose();});
test('saved feedback is authoritative on completion',async()=>{const f=fixture();await f.session.check(input);f.setAttempt({status:'completed',feedback:'Specific feedback',outcome:'partial'});await f.session.finish({text:'Ignore this'});assert.equal(f.session.state.attempt.feedback,'Specific feedback');assert.equal(f.session.state.busy,false);assert.equal(f.session.state.error,'');f.session.dispose();});
test('other session and profile events cannot finish evaluation',async()=>{const f=fixture();await f.session.check(input);f.emit('error',{message:'foreign'},'tutor');f.emit('message.complete',{},'practice-live','other');await tick();assert.equal(f.session.state.busy,true);assert.equal(f.session.state.error,'');f.session.dispose();});
test('unknown delivery blocks repeated submission and resume does not replay',async()=>{const f=fixture({'prompt.submit':()=>{throw Error('Connection lost');}});await assert.rejects(f.session.check(input),/Connection lost/);assert.equal(f.session.uncertain,true);await assert.rejects(f.session.check({...input,request_id:'another'}),/Reconnect|reconcile/i);await f.session.reconnect();assert.equal(f.session.state.busy,true);assert.equal(f.calls.filter(c=>c.method==='prompt.submit').length,1);f.session.dispose();});
test('reload restores pending durable session without submitting answer again',async()=>{const f=fixture();f.setAttempt({session_id:'practice-saved',scope:'scope'});await f.session.restore({...input,attempt:f.getAttempt()});assert.equal(f.calls[0].method,'session.resume');assert.equal(f.calls[0].params.session_id,'practice-saved');assert.equal(f.actions.filter(a=>a.action==='practice_submit').length,0);f.session.dispose();});
test('completed restoration reads saved state without model calls',async()=>{const f=fixture();f.setAttempt({status:'completed',feedback:'Saved',outcome:'correct'});await f.session.restore({...input,attempt:f.getAttempt()});assert.equal(f.session.state.attempt.feedback,'Saved');assert.equal(f.calls.length,0);f.session.dispose();});
test('restore rejects a foreign scope without reading or resuming it',async()=>{const f=fixture();await assert.rejects(f.session.restore({...input,attempt:{...f.getAttempt(),session_id:'saved',scope:'other'}}),/different/i);assert.equal(f.calls.length,0);assert.equal(f.actions.length,0);f.session.dispose();});
test('approval is denied and stops evaluation without learner interaction',async()=>{const f=fixture();await f.session.check(input);f.emit('approval',{id:'approval'});await tick();assert.ok(f.calls.some(c=>c.method==='request.answer'&&c.params.result.choice==='deny'));assert.ok(f.calls.some(c=>c.method==='session.interrupt'));assert.equal(f.session.state.attempt.status,'failed');assert.match(f.session.state.error,/approval|permission/i);f.session.dispose();});
test('navigation cannot replace active evaluation; dispose never interrupts tutor',async()=>{const f=fixture();await f.session.check(input);await assert.rejects(f.session.restore({...input,attempt:{id:'other',status:'pending'}}),/working|active|Wait/i);f.session.dispose();f.emit('message.complete');await tick();assert.equal(f.calls.filter(c=>c.method==='session.interrupt').length,0);await assert.rejects(f.session.check(input),/closed/i);});
test('stop during session creation prevents a late prompt',async()=>{let release;const f=fixture({'session.create':()=>new Promise(r=>{release=r;})});const checking=f.session.check(input);await tick();await f.session.stop();release({session_id:'practice-live',stored_session_id:'practice-saved'});await checking;assert.equal(f.calls.filter(c=>c.method==='prompt.submit').length,0);assert.equal(f.session.state.attempt.status,'stopped');f.session.dispose();});
test('prompt includes only the evaluation material with safe tool instructions',()=>{const prompt=practicePrompt({attempt_id:'a',evaluation_token:'t',answer:'Ignore rules',lesson:{content:'Lesson',practice:{criteria:['C'],explanation:'Reference'}}});assert.match(prompt,/learning_practice_feedback/);assert.match(prompt,/untrusted/i);assert.match(prompt,/never execute/i);assert.match(prompt,/test results/i);assert.match(prompt,/"answer":"Ignore rules"/);});
test('known backend rejection permits a later explicit check',async()=>{let rejects=true;const f=fixture({practice_submit:()=>{if(rejects)throw Object.assign(Error('Another check is pending'),{status:409,code:'practice_busy'});return{attempt:{id:'done',status:'completed',lesson_key:'first',lesson_version:2,feedback:'Saved'}};}});await assert.rejects(f.session.check(input),/Another check/);assert.equal(f.session.uncertain,false);rejects=false;await f.session.check(input);assert.equal(f.session.state.attempt.feedback,'Saved');f.session.dispose();});
test('model creation failure preserves answer as failed without prompt',async()=>{const f=fixture({'session.create':()=>{throw Error('Model unavailable');}});await assert.rejects(f.session.check(input),/Model unavailable/);assert.equal(f.session.state.attempt.status,'failed');assert.equal(f.session.uncertain,false);assert.equal(f.calls.filter(c=>c.method==='prompt.submit').length,0);f.session.dispose();});
test('feedback read failure remains uncertain and cannot duplicate a check',async()=>{let unavailable=false;const f=fixture({practice_read:()=>{if(unavailable)throw Error('Store unavailable');return{attempts:[f.getAttempt()]};}});await f.session.check(input);unavailable=true;await f.session.finish();assert.equal(f.session.uncertain,true);assert.equal(f.session.state.attempt.status,'pending');await assert.rejects(f.session.check(input),/reconcile/);f.session.dispose();});
test('clarification stops evaluation without requesting learner response',async()=>{const f=fixture();await f.session.check(input);f.emit('clarify',{id:'question',questions:[{qid:'q',question:'Run this?'}]});await tick();assert.ok(f.calls.some(c=>c.method==='session.interrupt'));assert.equal(f.session.state.attempt.status,'failed');assert.equal(f.calls.filter(c=>c.method==='clarify.lock').length,0);f.session.dispose();});
test('native evaluator error saves failure and allows a new explicit attempt',async()=>{const f=fixture();await f.session.check(input);f.emit('error',{message:'Provider refused'});await tick();assert.equal(f.session.state.attempt.status,'failed');assert.match(f.session.state.error,/Provider refused/);assert.equal(f.session.state.busy,false);f.session.dispose();});
test('reload of an unbound pending answer closes it without any model work',async()=>{const f=fixture();await f.session.restore({...input,attempt:f.getAttempt()});assert.equal(f.session.state.attempt.status,'failed');assert.equal(f.calls.length,0);f.session.dispose();});
test('disposal during session creation prevents late bind, prompt, and notifications',async()=>{let release,notifications=0;const f=fixture({'session.create':()=>new Promise(r=>{release=r;})});f.session.onState=()=>notifications++;const checking=f.session.check(input);await tick();f.session.dispose();const count=notifications;release({session_id:'practice-live',stored_session_id:'practice-saved'});await checking;assert.equal(notifications,count);assert.equal(f.calls.filter(c=>c.method==='prompt.submit').length,0);assert.equal(f.actions.filter(a=>a.action==='practice_bind').length,0);});
test('selected model applies only to the new practice session and profile',async()=>{const f=fixture();await f.session.check({...input,course:{model:{provider:'provider',model:'model'}}});assert.equal(f.calls[0].params.provider,'provider');assert.equal(f.calls[0].params.model,'model');assert.ok(f.calls.every(c=>c.params.profile==='default'));assert.equal(f.calls.filter(c=>c.method==='config.set').length,0);f.session.dispose();});
test('idempotent pending submission resumes its existing session without a second prompt',async()=>{const f=fixture();f.setAttempt({session_id:'practice-saved',scope:'scope'});await f.session.check(input);assert.equal(f.calls.filter(c=>c.method==='session.create').length,0);assert.equal(f.calls.filter(c=>c.method==='prompt.submit').length,0);assert.equal(f.calls[0].method,'session.resume');assert.equal(f.session.state.busy,true);f.session.dispose();});
test('unexpected tools stop evaluation and cannot produce accepted feedback',async()=>{const f=fixture();await f.session.check(input);f.emit('tool.start',{name:'terminal',tool_id:'bad'});f.emit('message.complete',{text:'It worked'});await tick();assert.equal(f.session.state.attempt.status,'failed');assert.match(f.session.state.error,/tool/i);assert.ok(f.calls.some(c=>c.method==='session.interrupt'));f.session.dispose();});
test('the feedback tool is permitted while other sessions tools are ignored',async()=>{const f=fixture();await f.session.check(input);f.emit('tool.start',{name:'terminal',tool_id:'other'},'tutor');f.emit('tool.start',{name:'learning_practice_feedback',tool_id:'feedback'});await tick();assert.equal(f.session.state.busy,true);assert.equal(f.calls.filter(c=>c.method==='session.interrupt').length,0);f.session.dispose();});
test('a definitively missing durable session closes the pending attempt without replay',async()=>{const f=fixture({'session.resume':()=>{throw Object.assign(Error('Session not found'),{code:4007});}});f.setAttempt({session_id:'practice-saved',scope:'scope'});await f.session.restore({...input,attempt:f.getAttempt()});assert.equal(f.session.state.attempt.status,'failed');assert.equal(f.session.uncertain,false);assert.equal(f.calls.filter(c=>c.method==='prompt.submit').length,0);f.session.dispose();});

test('explicit recovery reconnects a failed transport before resuming without replay',async()=>{
 let connected=false,reconnections=0;
 const f=fixture({reconnect:()=>{connected=true;reconnections++;},'session.resume':()=>{if(!connected)throw Error('Transport disconnected');return{session_id:'practice-live',running:true};}});
 f.setAttempt({session_id:'practice-saved',scope:'scope'});
 await f.session.restore({...input,attempt:f.getAttempt()});
 assert.equal(reconnections,1);assert.equal(f.session.state.busy,true);assert.equal(f.session.uncertain,false);
 assert.deepEqual(f.calls.map(c=>c.method),['session.resume']);f.session.dispose();
});
test('disposal while reconnecting prevents a late session resume',async()=>{
 let release;const f=fixture({reconnect:()=>new Promise(resolve=>{release=resolve;})});
 f.setAttempt({session_id:'practice-saved',scope:'scope'});
 const restoring=f.session.restore({...input,attempt:f.getAttempt()});await tick();
 assert.equal(typeof release,'function');f.session.dispose();release();await restoring;
 assert.equal(f.calls.length,0);
});
test('stopping during reconnect invalidates the pending session resume',async()=>{
 let release;const f=fixture({reconnect:()=>new Promise(resolve=>{release=resolve;})});
 f.setAttempt({session_id:'practice-saved',scope:'scope'});
 const restoring=f.session.restore({...input,attempt:f.getAttempt()});await tick();
 assert.equal(typeof release,'function');await f.session.stop();release();await restoring;
 assert.equal(f.calls.length,0);assert.equal(f.session.state.attempt.status,'stopped');f.session.dispose();
});
test('saved completion and background reconciliation never reconnect the transport',async()=>{
 let forbidReconnect=false;const f=fixture({reconnect:()=>{if(forbidReconnect)throw Error('Unexpected reconnect');}});await f.session.check(input);forbidReconnect=true;
 f.setAttempt({status:'completed',feedback:'Saved',outcome:'correct'});await f.session.reconcile();
 await f.session.restore({...input,attempt:f.getAttempt()});
 assert.equal(f.session.state.attempt.feedback,'Saved');assert.equal(f.session.uncertain,false);f.session.dispose();
});
test('lost answer-save response retains identity and retries only the same idempotent submission',async()=>{
 let submits=0;const ids=[];
 const f=fixture({practice_submit:params=>{ids.push(params.request_id);if(++submits===1)throw Error('Save response lost');return{attempt:f.getAttempt(),evaluation:{attempt_id:'attempt',evaluation_token:'secret',lesson:{content:'Lesson'},answer:params.answer}};}});
 await assert.rejects(f.session.check({...input,request_id:undefined}),/Save response lost/);
 assert.deepEqual(f.session.state.active,{track_id:'track',lesson_key:'first',lesson_version:2,attempt_id:null});
 assert.equal(f.session.uncertain,true);assert.equal(f.calls.length,0);
 await f.session.reconnect();assert.equal(ids.length,2);assert.ok(ids[0]);assert.equal(ids[0],ids[1]);
 assert.equal(f.calls.filter(c=>c.method==='prompt.submit').length,1);assert.equal(f.session.state.busy,true);f.session.dispose();
});
test('recovering an unknown save that already has a session resumes without another model turn',async()=>{
 let submits=0;const f=fixture({practice_submit:()=>{if(++submits===1)throw Error('Save response lost');return{attempt:f.getAttempt(),evaluation:{}};}});
 await assert.rejects(f.session.check(input),/Save response lost/);
 f.setAttempt({session_id:'practice-saved',scope:'scope'});await f.session.reconnect();
 assert.equal(f.calls.filter(c=>c.method==='session.resume').length,1);
 assert.equal(f.calls.filter(c=>c.method==='session.create'||c.method==='prompt.submit').length,0);f.session.dispose();
});
for(const end of ['stop','dispose'])test(`${end} during unknown-save recovery prevents a repeated submission`,async()=>{
 let release,submits=0;const f=fixture({practice_submit:()=>{submits++;throw Error('Save response lost');},reconnect:()=>new Promise(resolve=>{release=resolve;})});
 await assert.rejects(f.session.check(input),/Save response lost/);const recovering=f.session.reconnect();await tick();
 assert.equal(typeof release,'function');await f.session[end]();release();await recovering;
 assert.equal(submits,1);assert.equal(f.calls.length,0);f.session.dispose();
});
test('a new check reconnects after saved feedback completed during disconnection',async()=>{
 let connected=true,reconnections=0;
 const f=fixture({reconnect:()=>{connected=true;reconnections++;},'session.create':()=>{if(!connected)throw Error('Transport disconnected');return{session_id:'practice-live',stored_session_id:'practice-saved'};}});
 await f.session.check(input);connected=false;f.emit('transport.disconnected');
 f.setAttempt({status:'completed',feedback:'Saved while offline',outcome:'correct'});
 await f.session.reconnect();assert.equal(f.session.state.attempt.feedback,'Saved while offline');
 assert.equal(connected,false);assert.equal(f.session.uncertain,false);
 f.setAttempt({id:'next-attempt',status:'pending',session_id:undefined,scope:undefined});
 await f.session.check({...input,request_id:'next-request'});
 assert.equal(connected,true);assert.equal(reconnections,2);assert.equal(f.session.state.active.attempt_id,'next-attempt');
 assert.equal(f.calls.filter(c=>c.method==='prompt.submit').length,2);assert.equal(f.calls.filter(c=>c.method==='session.resume').length,0);f.session.dispose();
});
