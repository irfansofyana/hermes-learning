import {useState,useEffect,useRef,useCallback} from 'react';
export function useWorkspace(request) {
 const [state,setState]=useState(null),[context,setContext]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),[notice,setNotice]=useState(''),[connected,setConnected]=useState(false);
 const alive=useRef(true), snapshot=useRef(null), inFlight=useRef(false), operation=useRef(false), contextRef=useRef(null);
 const selectContext=useCallback(value=>{contextRef.current=value;setContext(value);try{if(value)sessionStorage.setItem('hermes-learning:context',JSON.stringify(value));else sessionStorage.removeItem('hermes-learning:context');}catch{}},[]);
 const refresh=useCallback(async()=>{
   if(inFlight.current)return; inFlight.current=true;
   try {const next=await request('/state');if(!alive.current)return;
    if(next.api_version!==1||next.schema_version!==1||typeof next.store_id!=='string'||!Array.isArray(next.tracks))throw new Error('This workspace needs a compatible Learning API v1 backend. Writes are unavailable.');
    if(snapshot.current&&snapshot.current.store_id!==next.store_id){selectContext(null);setNotice('Backend changed. Select a track and explicitly resume before writing.');}
    if(!snapshot.current){try{const saved=JSON.parse(sessionStorage.getItem('hermes-learning:context'));if(saved?.store_id===next.store_id)selectContext(saved);}catch{}}
    snapshot.current=next;setState(next);setConnected(true);
   }catch(e){if(alive.current){setConnected(false);setError(e.message||'The learning backend could not be reached.');}}
   finally{inFlight.current=false;}
 },[request,selectContext]);
 useEffect(()=>{alive.current=true;refresh();const poll=setInterval(()=>{if(document.visibilityState==='visible')refresh();},25000);const visible=()=>{if(document.visibilityState==='visible')refresh();};window.addEventListener('focus',refresh);window.addEventListener('online',refresh);document.addEventListener('visibilitychange',visible);return()=>{alive.current=false;clearInterval(poll);window.removeEventListener('focus',refresh);window.removeEventListener('online',refresh);document.removeEventListener('visibilitychange',visible);};},[refresh]);
 const act=useCallback(async(action,params={},options={})=>{
   if(operation.current)throw new Error('Wait for the current action to finish.');
   if(!snapshot.current||!connected)throw new Error('Reconnect to the learning backend before saving.');
   operation.current=true;setBusy(true);setError('');
   try{const result=await request('/action',{api_version:1,action,params:{...(contextRef.current&&!['start','resume'].includes(action)?{context_id:contextRef.current.context_id}:{}),...params}});
     if(!alive.current)return result;
     if(action==='start'||action==='resume')selectContext({...result,store_id:snapshot.current.store_id});
     if(action==='leave')selectContext(null);
     if(options.refresh!==false)await refresh();return result;
   }catch(e){if(alive.current){setError(e.message||'Could not save this change.');if(e.code==='context_revoked'||/Tracking context has ended|Track must be explicitly resumed|context not found/.test(e.message||''))selectContext(null);}throw e;}
   finally{operation.current=false;if(alive.current)setBusy(false);}
 },[request,refresh,selectContext,connected]);
 return {state,context,error,busy,notice,connected,act,refresh,setError,setNotice,selectContext};
}
