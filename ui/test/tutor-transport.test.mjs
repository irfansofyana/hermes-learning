import test from 'node:test';
import assert from 'node:assert/strict';
import {createTutorTransport, createWebTutorTransport} from '../src/tutor-transport.mjs';

class Socket {
  static instances = [];
  constructor(url) { this.url=url; this.readyState=0; this.listeners=new Map(); this.sent=[]; Socket.instances.push(this); }
  addEventListener(type, fn) { const listeners=this.listeners.get(type)||new Set(); listeners.add(fn); this.listeners.set(type,listeners); }
  removeEventListener(type, fn) { this.listeners.get(type)?.delete(fn); }
  emit(type, data={}) { for(const fn of [...(this.listeners.get(type)||[])]) fn(data); }
  open() { this.readyState=1; this.emit('open'); }
  send(data) { this.sent.push(JSON.parse(data)); }
  message(frame) { this.emit('message',{data:JSON.stringify(frame)}); }
  reply(frame, result) { this.message({jsonrpc:'2.0',id:frame.id,result}); }
  close() { this.readyState=3; this.emit('close',{code:1006}); }
}
const tick=()=>new Promise(resolve=>setImmediate(resolve));
function web(options={}) {
  Socket.instances=[];
  const paths=[];
  const transport=createWebTutorTransport({async buildWsUrl(...args){paths.push(args);return 'wss://host/base/api/ws?ticket=single-use';}}, {WebSocket:Socket,...options});
  return {transport,paths};
}
async function connected(transport) {
  const pending=transport.request('session.create',{title:'Learn'});
  await tick();
  const socket=Socket.instances.at(-1); socket.open();
  assert.equal(socket.sent[0].method,'client.capabilities');
  assert.deepEqual(socket.sent[0].params,{server_requests:true});
  socket.reply(socket.sent[0],{declines_not_shown:true});
  await tick();
  socket.reply(socket.sent.at(-1),{session_id:'runtime',stored_session_id:'stored'});
  await pending;
  transport.setSession('runtime');
  return socket;
}

test('web connects lazily with SDK authentication and correlates out-of-order results',async()=>{
  const {transport,paths}=web();
  assert.equal(Socket.instances.length,0);
  const socket=await connected(transport);
  assert.deepEqual(paths,[['/api/ws']]);
  assert.equal(socket.url,'wss://host/base/api/ws?ticket=single-use');
  const first=transport.request('session.history',{session_id:'runtime'});
  const second=transport.request('approval.pending',{session_id:'runtime'});
  await tick();
  const [a,b]=socket.sent.slice(-2);
  assert.notEqual(a.id,b.id);
  socket.reply(b,{pending:[]}); socket.reply(a,{messages:[{role:'user',content:'hi'}]});
  assert.deepEqual(await first,{messages:[{role:'user',content:'hi'}]});
  assert.deepEqual(await second,{pending:[]});
  transport.dispose();
});

test('web normalizes notifications and delivers only selected-session server requests',async()=>{
  const {transport}=web(); const socket=await connected(transport); const seen=[];
  const off=transport.onEvent('message.delta',event=>seen.push(event));
  transport.onEvent('clarify',event=>seen.push(event));
  socket.message({jsonrpc:'2.0',method:'event',params:{type:'message.delta',session_id:'runtime',payload:{text:'Hello'},profile:'work'}});
  socket.message({jsonrpc:'2.0',id:'q1',method:'clarify',params:{session_id:'runtime',questions:[{qid:'one',question:'Which?'}]}});
  socket.message({jsonrpc:'2.0',id:'other',method:'clarify',params:{session_id:'other',questions:[]}});
  assert.equal(seen.length,2);
  assert.equal(seen[0].session_id,'runtime'); assert.deepEqual(seen[0].payload,{text:'Hello'});
  assert.equal(seen[0].profile,'work'); assert.equal(seen[1].payload.id,'q1');
  assert.equal(socket.sent.at(-1).error.code,4404);
  off(); socket.message({method:'event',params:{type:'message.delta',session_id:'runtime',payload:{text:'ignored'}}});
  assert.equal(seen.length,2); transport.dispose();
});

test('disconnect rejects pending prompts, reports uncertainty, and never reconnects or replays',async()=>{
  const {transport}=web(); const socket=await connected(transport); const errors=[];
  transport.onEvent('transport.disconnected',event=>errors.push(event));
  const prompt=transport.request('prompt.submit',{session_id:'runtime',text:'Teach me'});
  const rejected=assert.rejects(prompt,/disconnected/i); await tick(); socket.close(); await rejected;
  await assert.rejects(transport.request('prompt.submit',{text:'Again'}),/disconnected/i);
  assert.equal(Socket.instances.length,1);
  assert.equal(socket.sent.filter(frame=>frame.method==='prompt.submit').length,1);
  assert.equal(errors.length,1); assert.match(errors[0].payload.message,/disconnected/i);
  assert.equal([...socket.listeners.values()].reduce((n,set)=>n+set.size,0),0);
  transport.dispose();
});

test('dispose during authentication rejects the waiting request and never opens a socket',async()=>{
  let authenticate;
  const transport=createWebTutorTransport({buildWsUrl:()=>new Promise(resolve=>{authenticate=resolve;})},{WebSocket:Socket});
  Socket.instances=[];
  const request=transport.request('session.create',{}); const rejected=assert.rejects(request,/disposed/i);
  await tick(); transport.dispose(); await rejected;
  authenticate('wss://host/api/ws?ticket=late'); await tick();
  assert.equal(Socket.instances.length,0);
});

test('RPC errors retain the code and data without killing the connection',async()=>{
  const {transport}=web();const socket=await connected(transport);
  const request=transport.request('prompt.submit',{});await tick();
  socket.message({id:socket.sent.at(-1).id,error:{code:4001,message:'Invalid session',data:{reason:'gone'}}});
  await assert.rejects(request,error=>error.code===4001&&error.data.reason==='gone');
  const next=transport.request('session.history',{});await tick();socket.reply(socket.sent.at(-1),{messages:[]});await next;
  transport.dispose();
});

test('connection timeout and request timeout are terminal without automatic replay',async()=>{
  const first=web({connectTimeoutMs:10});
  await assert.rejects(first.transport.request('session.create',{}),/timed out/i);
  first.transport.dispose();
  const second=web({requestTimeoutMs:10});const socket=await connected(second.transport);
  await assert.rejects(second.transport.request('prompt.submit',{text:'hello'}),/timed out/i);
  await assert.rejects(second.transport.request('prompt.submit',{text:'hello'}),/timed out/i);
  assert.equal(socket.sent.filter(frame=>frame.method==='prompt.submit').length,1);second.transport.dispose();
});

test('desktop preserves host event identity and removes subscriptions without closing the host',async()=>{
  const listeners=new Map(); const calls=[];
  const host={request(method,params){calls.push([method,params]);return Promise.resolve({session_id:'runtime'});},onEvent(type,fn){listeners.set(type,fn);return()=>listeners.delete(type);}};
  const transport=createTutorTransport(host);const seen=[];
  transport.onEvent('message.delta',event=>seen.push(event));
  await transport.request('session.create',{profile:'study'});
  listeners.get('message.delta')({type:'message.delta',session_id:'runtime',payload:{text:'Hi'},connectionId:'local',profile:'study'});
  assert.equal(seen[0].session_id,'runtime');assert.equal(seen[0].connectionId,'local');assert.equal(seen[0].profile,'study');
  assert.deepEqual(calls,[['session.create',{profile:'study'}]]);
  transport.dispose();assert.equal(listeners.size,0);
  await assert.rejects(transport.request('session.create',{}),/disposed/i);
});

test('desktop disposes an outstanding host request immediately',async()=>{
  const transport=createTutorTransport({request:()=>new Promise(()=>{}),onEvent:()=>()=>{}});
  const pending=transport.request('prompt.submit',{}); const rejected=assert.rejects(pending,/disposed/i);
  transport.dispose();await rejected;
});

test('desktop reports gateway loss through the public state atom and cleans it up',()=>{
  let listener;let removed=false;const seen=[];
  const host={request:async()=>({}),onEvent:()=>()=>{},state:{gateway:{get:()=> 'open',listen(fn){listener=fn;return()=>{removed=true;};}}}};
  const transport=createTutorTransport(host);
  transport.onEvent('transport.disconnected',event=>seen.push(event));
  listener('closed');assert.equal(seen.length,1);assert.match(seen[0].payload.message,/disconnected/i);
  transport.dispose();assert.equal(removed,true);
});

test('authentication failures are terminal and never create unauthenticated sockets',async()=>{
  Socket.instances=[];let calls=0;
  const transport=createWebTutorTransport({buildWsUrl:async()=>{calls++;throw new Error('Login required');}},{WebSocket:Socket});
  await assert.rejects(transport.request('session.create',{}),/Login required/);
  await assert.rejects(transport.request('session.create',{}),/Login required/);
  assert.equal(calls,1);assert.equal(Socket.instances.length,0);transport.dispose();
});

test('heartbeat loss reports a disconnected streaming turn even with no outstanding prompt',async()=>{
  const {transport}=web({heartbeatIntervalMs:5,heartbeatDeadlineMs:10});const socket=await connected(transport);
  const disconnected=new Promise(resolve=>transport.onEvent('transport.disconnected',resolve));
  socket.message({method:'event',params:{type:'gateway.ready',payload:{heartbeat:true}}});
  const event=await disconnected;assert.match(event.payload.message,/gateway.ping/);
  assert.equal(socket.sent.filter(frame=>frame.method==='gateway.ping').length,1);transport.dispose();
});

test('explicit reconnect obtains fresh authentication and never replays a submitted prompt',async()=>{
  const {transport,paths}=web();const first=await connected(transport);
  const prompt=transport.request('prompt.submit',{session_id:'runtime',text:'Teach me'});
  const rejected=assert.rejects(prompt,/disconnected/i);await tick();first.close();await rejected;
  const reconnect=transport.reconnect();await tick();
  const second=Socket.instances.at(-1);assert.notEqual(first,second);assert.equal(paths.length,2);
  second.open();second.reply(second.sent[0],{});await reconnect;
  assert.deepEqual(second.sent.map(frame=>frame.method),['client.capabilities']);
  const restore=transport.request('session.resume',{session_id:'stored'});await tick();
  second.reply(second.sent.at(-1),{session_id:'new-runtime'});assert.deepEqual(await restore,{session_id:'new-runtime'});
  transport.dispose();await assert.rejects(transport.reconnect(),/disposed/i);
  assert.equal(paths.length,2);
});

test('late authentication from an expired connection cannot replace an explicitly reconnected socket',async()=>{
  Socket.instances=[];const resolves=[];
  const transport=createWebTutorTransport({buildWsUrl:()=>new Promise(resolve=>resolves.push(resolve))},{WebSocket:Socket,connectTimeoutMs:20});
  await assert.rejects(transport.request('session.create',{}),/timed out/i);
  const reconnect=transport.reconnect();await tick();
  resolves[1]('wss://host/api/ws?ticket=new');await tick();
  const socket=Socket.instances.at(-1);socket.open();socket.reply(socket.sent[0],{});await reconnect;
  resolves[0]('wss://host/api/ws?ticket=expired');await tick();
  assert.equal(Socket.instances.length,1);assert.equal(socket.url,'wss://host/api/ws?ticket=new');transport.dispose();
});
