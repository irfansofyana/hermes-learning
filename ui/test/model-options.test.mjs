import test from 'node:test';
import assert from 'node:assert/strict';
import {normalizeModelOptions,loadModelOptions,modelCreateParams,applySessionModel} from '../src/model-options.mjs';
const payload={provider:'openai',model:'gpt-default',providers:[{slug:'openai',name:'OpenAI',authenticated:true,models:['gpt-default','gpt-other','gpt-other','bad --global']},{slug:'offline',authenticated:false,models:['hidden']},{slug:'custom:local',name:'Local',authenticated:true,models:['org/model:tag']} ]};
test('only configured safe model identities are selectable and credentials never escape normalization',()=>{
 const result=normalizeModelOptions({...payload,api_key:'secret'});
 assert.deepEqual(result.defaultModel,{provider:'openai',model:'gpt-default'});
 assert.equal(result.options.length,3);assert.ok(!JSON.stringify(result).includes('secret'));assert.ok(!JSON.stringify(result).includes('--global'));
});
test('inventory request is scoped to profile and never to an active session',async()=>{
 let call;const result=await loadModelOptions({request:async(...args)=>(call=args,payload)},'work');
 assert.deepEqual(call,['model.options',{profile:'work',explicit_only:true,include_unconfigured:false}]);assert.equal(result.options.length,3);
});
test('creation inherits default or supplies validated per-session fields',()=>{
 assert.deepEqual(modelCreateParams(null),{});assert.deepEqual(modelCreateParams({provider:'openai',model:'gpt-other'}),{provider:'openai',model:'gpt-other'});
 assert.throws(()=>modelCreateParams({provider:'openai --global',model:'gpt-other'}),/model/i);
});
function transport(response={key:'model',value:'gpt-default',scope:'session',confirm_required:false}){const calls=[];return{calls,request:async(method,params)=>{calls.push({method,params});if(method==='model.options')return payload;if(method==='session.activate')return{running:false};return response;}};}
test('default explicitly resets a previous selection using session-only flags',async()=>{
 const t=transport();await applySessionModel(t,'work','live',null);const call=t.calls.at(-1);
 assert.equal(call.method,'config.set');assert.deepEqual(call.params,{profile:'work',session_id:'live',key:'model',value:'gpt-default --provider openai --session',persist:false});
});
test('model warnings requiring confirmation and deferred changes fail closed',async()=>{
 for(const response of [{confirm_required:true,confirm_message:'Review pricing'},{deferred:true},{status:'error',error:'Failed'},{}])await assert.rejects(applySessionModel(transport(response),'work','live',{provider:'openai',model:'gpt-default'}));
});
test('scope invalidation while resolving default prevents mutation',async()=>{
 let current=true;const t=transport();const request=t.request;t.request=async(...args)=>{const result=await request(...args);if(args[0]==='model.options')current=false;return result;};
 await assert.rejects(applySessionModel(t,'work','live',null,{isCurrent:()=>current}),/changed|cancel/i);assert.equal(t.calls.filter(c=>c.method==='config.set').length,0);
});
test('running sessions cannot mutate models',async()=>{
 const t=transport();t.request=async()=>({running:true});await assert.rejects(applySessionModel(t,'work','live',{provider:'openai',model:'gpt-default'}),/working|running|turn/i);
});
test('picker has an accessible model label and default choice',async()=>{
 const {loadRenderedModule}=await import('./render-module.mjs');const {createElement}=await import('react');const {renderToStaticMarkup}=await import('react-dom/server');
 const {ModelPicker}=await loadRenderedModule('../src/ModelPicker.jsx');
 const html=renderToStaticMarkup(createElement(ModelPicker,{transport:null,value:null,onChange(){}}));
 assert.match(html,/Model/);assert.match(html,/Hermes default/);assert.match(html,/<label[^>]*for=/);
});
test('branching preserves server-side conversation with the resolved default and idempotency key',async()=>{
 const {branchSessionModel}=await import('../src/model-options.mjs');const t=transport();const request=t.request;
 t.request=async(method,params)=>method==='session.branch_stored'?(t.calls.push({method,params}),{session_id:'next',stored_session_id:'saved-next'}):request(method,params);
 const result=await branchSessionModel(t,'work','live','saved',null,{idempotencyKey:'change-1'});
 assert.equal(result.session_id,'next');assert.deepEqual(t.calls.at(-1).params,{profile:'work',parent_session_id:'saved',provider:'openai',model:'gpt-default',close_on_disconnect:false,idempotency_key:'change-1'});
 assert.equal(t.calls.filter(c=>c.method==='config.set').length,0);
});
