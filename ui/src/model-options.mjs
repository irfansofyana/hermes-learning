// Hermes owns provider credentials. Keep only identities and display labels in Learning.
const safeId=value=>typeof value==='string'&&/^[A-Za-z0-9][A-Za-z0-9._:/@+~-]*$/.test(value)&&value.length<=300;
export function modelCreateParams(selection){
 if(selection==null)return {};
 if(!safeId(selection.provider)||!safeId(selection.model))throw Error('This model selection is not supported. Choose a configured model.');
 return {provider:selection.provider,model:selection.model};
}
export const modelSelectionKey=selection=>selection==null?'default':JSON.stringify(modelCreateParams(selection));
export function normalizeModelOptions(payload){
 if(!payload||!Array.isArray(payload.providers))throw Error('Hermes did not return its configured models.');
 const options=[],seen=new Set();
 for(const row of payload.providers){
  if(row?.authenticated!==true||!safeId(row.slug)||!Array.isArray(row.models))continue;
  for(const model of row.models){
   if(!safeId(model))continue;
   const value={provider:row.slug,model},key=modelSelectionKey(value);
   if(seen.has(key))continue;seen.add(key);
   options.push({...value,label:`${typeof row.name==='string'?row.name:row.slug} · ${model}`});
  }
 }
 const defaultModel=safeId(payload.provider)&&safeId(payload.model)?{provider:payload.provider,model:payload.model}:null;
 return {defaultModel,options};
}
export async function loadModelOptions(transport,profile){
 if(!transport?.request)throw Error('Connect to Hermes to load models.');
 return normalizeModelOptions(await transport.request('model.options',{...(profile?{profile}:{}),explicit_only:true,include_unconfigured:false}));
}
export async function applySessionModel(transport,profile,sessionId,selection,{isCurrent=()=>true}={}){
 const check=()=>{if(!isCurrent())throw Error('The learning session changed. Model selection was cancelled.');};
 check();if(!sessionId)throw Error('A conversation is required to select its model.');
 const params=values=>({...(profile?{profile}:{}),...values});
 const snapshot=await transport.request('session.activate',params({session_id:sessionId,omit_messages:true}));
 check();if(snapshot.running!==false)throw Error('Wait for the current turn before changing its model.');
 const target=selection==null?(await loadModelOptions(transport,profile)).defaultModel:modelCreateParams(selection);
 check();if(!target)throw Error('Hermes could not resolve this profile’s default model. Retry loading models.');
 // persist:false is advisory on older hosts. --session is the actual host persistence guard.
 const result=await transport.request('config.set',params({session_id:sessionId,key:'model',value:`${target.model} --provider ${target.provider} --session`,persist:false}));
 check();
 if(result?.confirm_required)throw Error(result.confirm_message||result.warning||'Hermes requires confirmation for this model. Confirm it in Hermes before trying again.');
 if(result?.deferred)throw Error('This Hermes host only queues model changes for existing conversations and cannot confirm the selected model before sending. Start a new tutor conversation with this model.');
 if(result?.key!=='model'||typeof result.value!=='string'||!result.value||result.scope!=='session'||result.error||result.status==='error')throw Error('Hermes did not confirm the model change. Your request was not sent.');
 return {...target,model:result.value};
}
// session.branch_stored uses the create implementation internally, but its wire
// schema does NOT allow model/provider overrides. Read the authenticated history
// and seed session.create instead; that public contract supports both together.
export async function branchSessionModel(transport,profile,sessionId,storedSessionId,selection,{isCurrent=()=>true,idempotencyKey}={}){
 const check=()=>{if(!isCurrent())throw Error('The learning session changed. Model selection was cancelled.');};
 const params=values=>({...(profile?{profile}:{}),...values});
 check();if(!sessionId||!storedSessionId||!idempotencyKey)throw Error('A saved conversation is required to change its model.');
 const snapshot=await transport.request('session.activate',params({session_id:sessionId,omit_messages:true}));
 check();if(snapshot.running!==false)throw Error('Wait for the current turn before changing its model.');
 const target=selection==null?(await loadModelOptions(transport,profile)).defaultModel:modelCreateParams(selection);
 check();if(!target)throw Error('Hermes could not resolve this profile’s default model. Retry loading models.');
 const history=await transport.request('session.history',params({session_id:sessionId}));
 check();
 if(!Array.isArray(history?.messages))throw Error('Hermes did not return the tutor history. Your model change was not applied.');
 const messages=history.messages.flatMap(message=>{
  if(!message||!['user','assistant'].includes(message.role)||message.display_kind==='hidden')return [];
  const content=typeof message.text==='string'?message.text:typeof message.content==='string'?message.content:null;
  if(content===null)throw Error('This conversation contains history that cannot be copied safely. Your model change was not applied.');
  return content.trim()?[{role:message.role,content}]:[];
 });
 const created=await transport.request('session.create',params({parent_session_id:storedSessionId,messages,...target,close_on_disconnect:false,idempotency_key:idempotencyKey}));
 check();
 if(!created?.session_id||!created.stored_session_id||created.confirm_required||created.error)throw Error('Hermes did not create the conversation with the selected model. Your request was not sent.');
 return created;
}
