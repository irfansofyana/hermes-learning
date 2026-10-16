import test from 'node:test';
import assert from 'node:assert/strict';
import {openTutorChat} from '../src/handoff.mjs';
const command='/learning-track resume track-1',request='Review my pending answer.';
function fixture(initial=''){let draft=initial,profile='learning';const calls=[];const data=new Map();const storage={setItem:(k,v)=>data.set(k,v),getItem:k=>data.get(k),removeItem:k=>data.delete(k)};const host={state:{profile:{get:()=>profile},connectionId:{get:()=> 'local'}},newChat:()=>calls.push('newChat'),composer:{getDraft:async id=>{assert.equal(id,'new');return draft;},insertText:async(id,text,options)=>{calls.push({id,text,options});draft=text;return true;},focus:id=>calls.push(`focus:${id}`)}};return {host,calls,storage,draft:()=>draft,changeProfile:()=>{profile='other';}};}
test('native tutor handoff prepares only the resume command and retains the second message',async()=>{
 const f=fixture();await openTutorChat(f.host,command,f.storage,request);
 assert.equal(f.calls[0],'newChat');assert.equal(f.calls[1].id,'new');assert.deepEqual(f.calls[1].options,{mode:'block'});
 assert.equal(f.draft(),command);assert.equal(f.storage.getItem('hermes-learning:tutor-request'),`${command}\n\n${request}`);
});
test('native resume preserves existing unsent notes without mixing them into a command',async()=>{
 const f=fixture('My existing unsent notes.');
 await assert.rejects(openTutorChat(f.host,command,f.storage,request),/already contains a draft/);
 assert.equal(f.draft(),'My existing unsent notes.');assert.equal(f.calls.filter(call=>typeof call==='object').length,0);
});
test('a delayed insertion acknowledgement does not duplicate the resume command',async()=>{
 const f=fixture(),insert=f.host.composer.insertText;f.host.composer.insertText=async(...args)=>{await insert(...args);return false;};
 await openTutorChat(f.host,command,f.storage,request);
 assert.equal(f.calls.filter(call=>typeof call==='object').length,1);
});
test('profile changes stop insertion and preserve both recovery messages',async()=>{
 const f=fixture();f.host.newChat=()=>f.changeProfile();
 await assert.rejects(openTutorChat(f.host,command,f.storage,request),/profile changed/);
 assert.equal(f.calls.filter(call=>typeof call==='object').length,0);
 assert.equal(f.storage.getItem('hermes-learning:tutor-request'),`${command}\n\n${request}`);
});
test('native handoff rejects combined command and request before opening chat',async()=>{
 const f=fixture();await assert.rejects(openTutorChat(f.host,`${command}\n${request}`,f.storage),/one separate line/);
 assert.equal(f.calls.length,0);
});
